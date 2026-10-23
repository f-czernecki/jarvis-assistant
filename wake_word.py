from pathlib import Path

import numpy as np
import sounddevice as sd
from openwakeword.model import Model
from app_state import shutdown_event,pause_event
import voice_input

MODEL_DIR = Path(r"E:\Models\WakeWord")

SAMPLE_RATE = 16000
BLOCK_SIZE = 1280
WAKE_THRESHOLD = 0.5


class WakeWordListener:
    def __init__(self):
        wake_model = MODEL_DIR / "hey_jarvis_v0.1.onnx"
        mel_model = MODEL_DIR / "melspectrogram.onnx"
        embedding_model = MODEL_DIR / "embedding_model.onnx"

        for path in (wake_model, mel_model, embedding_model):
            if not path.is_file():
                raise FileNotFoundError(
                    f"Missing model: {path}. "
                    "Run setup_wake_word.py first."
                )

        print("Loading wake-word model...")

        self.model = Model(
            wakeword_models=[str(wake_model)],
            inference_framework="onnx",
            melspec_model_path=str(mel_model),
            embedding_model_path=str(embedding_model),
        )

        print("Wake-word model ready.")

    def wait(self, stop_event=None, quiet: bool = False) -> bool:
        """Return True on detection, or False when cancelled."""
        self.model.reset()
        debug_blocks = 0

        if quiet:
            print("[Interrupt] Microphone listener started.", flush=True)
        if not quiet:
            print("Standby. Say 'Hey Jarvis'.")

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            channels=1,
            dtype="int16",
            device=voice_input.MICROPHONE,
        ) as stream:
            while (
                not shutdown_event.is_set()
                and (stop_event is None or not stop_event.is_set())
            ):
                if pause_event.is_set():
                    return False
                block, overflowed = stream.read(BLOCK_SIZE)

                if overflowed:
                    self.model.reset()
                    continue

                audio = np.ascontiguousarray(block[:, 0])
                predictions = self.model.predict(audio)

                score = max(
                    (float(value) for value in predictions.values()),
                    default=0.0,
                )
    
                if score >= WAKE_THRESHOLD:
                    if not quiet:
                        print(f"Wake phrase detected: {score:.2f}")

                    return True

        return False


if __name__ == "__main__":
    listener = WakeWordListener()

    try:
        listener.wait()
        print("Jarvis is ready for a command.")

    except KeyboardInterrupt:
        print("\nStopped.")