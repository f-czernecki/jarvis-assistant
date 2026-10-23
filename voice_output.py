from pathlib import Path
from time import perf_counter
from threading import Event, Thread
from app_state import shutdown_event, pause_event
from wake_word import WakeWordListener
import sounddevice as sd
from kokoro_onnx import Kokoro


MODEL_DIR = Path(r"E:\Models\Kokoro")

VOICE = "af_heart"
LANGUAGE = "en-us"
SPEECH_SPEED = 1.0

# None oznacza domyślne urządzenie odtwarzające.
OUTPUT_DEVICE = None

_model = None
_interrupt_listener = None


def get_interrupt_listener():
    """Load a separate wake-word detector once for speech interruption."""
    global _interrupt_listener

    if _interrupt_listener is None:
        _interrupt_listener = WakeWordListener()

    return _interrupt_listener

def get_tts_model() -> Kokoro:
    """Load the speech model once and reuse it."""
    global _model

    if _model is None:
        model_path = MODEL_DIR / "kokoro-v1.0.onnx"
        voices_path = MODEL_DIR / "voices-v1.0.bin"

        for path in (model_path, voices_path):
            if not path.is_file():
                raise FileNotFoundError(
                    f"Missing speech model file: {path}"
                )

        print("Loading speech output model...")
        start = perf_counter()

        _model = Kokoro(
            str(model_path),
            str(voices_path),
        )

        print(
            "Speech output model ready "
            f"in {perf_counter() - start:.2f} s."
        )

    return _model


def speak(text: str) -> None:
    """Speak the response; 'Hey Jarvis' interrupts playback."""
    text = text.strip()

    if not text or shutdown_event.is_set() or pause_event.is_set():
        return

    model = get_tts_model()
    listener = get_interrupt_listener()

    start = perf_counter()

    samples, sample_rate = model.create(
        text,
        voice=VOICE,
        speed=float(SPEECH_SPEED),
        lang=LANGUAGE,
    )
    if shutdown_event.is_set() or pause_event.is_set():
        return
    print(
        f"[TTS] Generation: {perf_counter() - start:.2f} s | "
        f"Audio length: {len(samples) / sample_rate:.2f} s"
    )

    interrupted = Event()
    cancel_listener = Event()

    def listen_for_interruption():
        try:
            detected = listener.wait(
                stop_event=cancel_listener,
                quiet=True,
            )

            if detected and not cancel_listener.is_set():
                interrupted.set()

        except Exception as error:
            print(f"[TTS] Interruption microphone error: {error}")

    listener_thread = Thread(
        target=listen_for_interruption,
        daemon=True,
    )

    print("[TTS] Say 'Hey Jarvis' to interrupt.")

    listener_thread.start()

    try:
        sd.play(
            samples,
            samplerate=sample_rate,
            device=OUTPUT_DEVICE,
        )

        playback_stream = sd.get_stream()

        while playback_stream.active:
            if shutdown_event.is_set() or pause_event.is_set():
                break
            
            if interrupted.wait(timeout=0.03):
                sd.stop()
                print("[TTS] Interrupted. Listening for your next command.")
                break

    finally:
        sd.stop()

        cancel_listener.set()
        listener_thread.join()


if __name__ == "__main__":
    get_tts_model()

    speak("Hello! I'm Jarvis. How can I help you today?")
    speak("My voice is ready. Let's build something together.")