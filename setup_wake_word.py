from openwakeword.utils import download_models
from jarvis.config import WAKE_MODEL_DIR as MODEL_DIR



def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Downloading wake-word models to: {MODEL_DIR}")

    download_models(
        model_names=["hey_jarvis"],
        target_directory=str(MODEL_DIR),
    )

    required_files = [
        "hey_jarvis_v0.1.onnx",
        "melspectrogram.onnx",
        "embedding_model.onnx",
    ]

    for filename in required_files:
        path = MODEL_DIR / filename

        if not path.is_file():
            raise FileNotFoundError(f"Missing model file: {path}")

    print("Wake-word models are ready.")


if __name__ == "__main__":
    main()