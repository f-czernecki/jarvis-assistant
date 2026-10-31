from jarvis.logging_setup import setup_logging

setup_logging()

from jarvis.desktop.single_instance import SingleInstance
from jarvis.desktop.tray_app import main as run_tray


def main():
    instance = SingleInstance()

    if not instance.acquire():
        print("[Startup] Jarvis is already running.")
        return

    try:
        run_tray()
    finally:
        instance.release()


if __name__ == "__main__":
    main()