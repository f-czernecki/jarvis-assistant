from logging_setup import setup_logging

LOG_FILE = setup_logging()

import os
import traceback
from threading import Thread

import pystray
from PIL import Image, ImageDraw

from app_state import shutdown_event,pause_event
from single_instance import SingleInstance

def create_icon_image():
    """Create a simple icon without an external image file."""
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    draw.ellipse(
        (4, 4, 60, 60),
        fill=(30, 40, 55),
        outline=(70, 200, 240),
        width=4,
    )

    # Litera J.
    draw.line(
        [(39, 18), (39, 38), (35, 45), (26, 45), (21, 40)],
        fill=(70, 200, 240),
        width=6,
    )

    return image


def open_logs(icon, item):
    try:
        os.startfile(str(LOG_FILE.parent))
    except Exception:
        traceback.print_exc()
def listening_menu_text(item):
    if pause_event.is_set():
        return "Resume listening"

    return "Pause listening"


def toggle_listening(icon, item):
    if shutdown_event.is_set():
        return

    if pause_event.is_set():
        pause_event.clear()
        icon.title = "Jarvis"
        print("[Tray] Resume requested.")

    else:
        pause_event.set()
        icon.title = "Jarvis — listening paused"
        print("[Tray] Pause requested.")

    icon.update_menu()

def request_shutdown(icon, item):
    if shutdown_event.is_set():
        return

    print("[Tray] Shutdown requested.")

    icon.title = "Jarvis — closing..."
    shutdown_event.set()

    # Ikonę zamknie wątek asystenta po zakończeniu sprzątania.


def run_assistant(icon):
    try:
        # Import tutaj: cięższe biblioteki ładują się po pokazaniu ikony.
        from assistant import main as assistant_main

        if not shutdown_event.is_set():
            assistant_main()

    except Exception:
        traceback.print_exc()

    finally:
        shutdown_event.set()
        print("[Tray] Assistant thread finished.")
        icon.stop()


def main():
    shutdown_event.clear()
    pause_event.clear()

    icon = pystray.Icon(
        name="jarvis",
        icon=create_icon_image(),
        title="Jarvis",
        menu=pystray.Menu(
            pystray.MenuItem(
                listening_menu_text,
                toggle_listening,
            ),
            pystray.MenuItem("Open logs", open_logs),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit Jarvis", request_shutdown),
        ),
    )

    worker = Thread(
        target=run_assistant,
        args=(icon,),
        name="JarvisAssistant",
        daemon=False,
    )

    def setup(tray_icon):
        tray_icon.visible = True
        print("[Tray] Icon ready. Starting assistant...")
        worker.start()

    try:
        icon.run(setup=setup)

    except KeyboardInterrupt:
        print("[Tray] Ctrl+C received.")

    finally:
        shutdown_event.set()

        if worker.ident is not None:
            worker.join()

        icon.stop()
        print("[Tray] Application closed.")


if __name__ == "__main__":
    instance = SingleInstance()

    if not instance.acquire():
        print("[Startup] Jarvis is already running.")

    else:
        try:
            main()
        finally:
            instance.release()
