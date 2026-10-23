import msvcrt
import os
from pathlib import Path


class SingleInstance:
    """Keep an exclusive Windows file lock while the app is running."""

    def __init__(self):
        self._file = None

    def acquire(self) -> bool:
        if self._file is not None:
            return True

        directory = (
            Path(os.environ["LOCALAPPDATA"])
            / "JarvisAssistant"
        )
        directory.mkdir(parents=True, exist_ok=True)

        lock_file = open(directory / "jarvis.lock", "a+b")

        try:
            lock_file.seek(0, os.SEEK_END)

            if lock_file.tell() == 0:
                lock_file.write(b"\0")
                lock_file.flush()

            lock_file.seek(0)

            msvcrt.locking(
                lock_file.fileno(),
                msvcrt.LK_NBLCK,
                1,
            )

        except OSError:
            lock_file.close()
            return False

        self._file = lock_file
        return True

    def release(self):
        if self._file is None:
            return

        try:
            self._file.seek(0)

            msvcrt.locking(
                self._file.fileno(),
                msvcrt.LK_UNLCK,
                1,
            )

        finally:
            self._file.close()
            self._file = None