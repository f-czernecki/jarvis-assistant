from collections import deque
from pathlib import Path
from app_state import shutdown_event,pause_event
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

MODEL_DIR = Path(r"E:\Models\Whisper")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MICROPHONE = None  # Wpisz tutaj numer swojego mikrofonu!

SAMPLE_RATE = 16000
BLOCK_SECONDS = 0.05

SILENCE_SECONDS = 1.0
START_TIMEOUT = 8.0
MAX_RECORD_SECONDS = 20.0

# Próg głośności: trzeba go dopasować do mikrofonu.
VOLUME_THRESHOLD = 0.015

_model = None


def get_model():
    global _model

    if _model is None:
        print("Loading speech model...")

        _model = WhisperModel(
            "small.en",
            device="cpu",
            compute_type="int8",
            download_root=str(MODEL_DIR),
        )

        print("Speech model ready.")

    return _model

def listen_and_transcribe() -> str:
    if shutdown_event.is_set() or pause_event.is_set():
        return ""

    model = get_model()

    block_size = int(SAMPLE_RATE * BLOCK_SECONDS)

    # Zachowujemy początek wypowiedzi sprzed wykrycia głosu.
    pre_roll = deque(maxlen=6)
    frames = []

    started = False
    silent_time = 0.0
    waiting_time = 0.0
    recorded_time = 0.0

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        blocksize=block_size,
        channels=1,
        dtype="float32",
        device=MICROPHONE,
    ) as stream:
        print("Speak now. Recording stops after a short silence.")

        while True:
            # Zamknięcie podczas oczekiwania na mowę lub nagrywania.
            if shutdown_event.is_set() or pause_event.is_set():
                return ""

            block, overflowed = stream.read(block_size)

            if overflowed:
                print("Audio overflow. Please try again.")
                return ""

            chunk = block[:, 0].copy()
            volume = float(np.sqrt(np.mean(chunk ** 2)))
            loud_enough = volume >= VOLUME_THRESHOLD

            if not started:
                pre_roll.append(chunk)
                waiting_time += BLOCK_SECONDS

                if loud_enough:
                    started = True
                    frames.extend(pre_roll)

                elif waiting_time >= START_TIMEOUT:
                    print("No speech detected.")
                    return ""

                continue

            frames.append(chunk)
            recorded_time += BLOCK_SECONDS

            if loud_enough:
                silent_time = 0.0
            else:
                silent_time += BLOCK_SECONDS

            if silent_time >= SILENCE_SECONDS:
                break

            if recorded_time >= MAX_RECORD_SECONDS:
                print("Recording time limit reached.")
                break

    # Tutaj mikrofon jest już zamknięty przez blok „with”.
    if shutdown_event.is_set() or pause_event.is_set():
        return ""

    audio = np.concatenate(frames)

    print("Transcribing...")

    segments, _ = model.transcribe(
        audio,
        language="en",
        initial_prompt=(
            "A conversation with an assistant named Jarvis. "
            "Hey Jarvis. Thanks Jarvis. Thank you Jarvis. "
        ),
        vad_filter=True,
        condition_on_previous_text=False,
    )

    parts = []

    # Segmenty są generowane podczas iterowania.
    for segment in segments:
        if shutdown_event.is_set():
            return ""

        parts.append(segment.text.strip())

    if shutdown_event.is_set():
        return ""

    text = " ".join(parts).strip()

    print("You:", text if text else "[no speech]")
    return text


if __name__ == "__main__":
    get_model()

    while True:
        choice = input("\nEnter to speak, or type 'exit': ").strip()

        if choice.lower() == "exit":
            break

        listen_and_transcribe()