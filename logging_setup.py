import atexit
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from threading import RLock


LOG_DIR = (
    Path(os.environ["LOCALAPPDATA"])
    / "JarvisAssistant"
    / "logs"
)

LOG_FILE = LOG_DIR / "jarvis.log"


class LoggedStream:
    """Copy complete output lines to a logger and optional terminal."""

    def __init__(self, logger, level, terminal):
        self.logger = logger
        self.level = level
        self.terminal = terminal
        self.buffer = ""
        self.lock = RLock()
        self.encoding = "utf-8"

    def write(self, text):
        if not text:
            return 0

        with self.lock:
            if self.terminal is not None:
                self.terminal.write(text)

            self.buffer += text

            while "\n" in self.buffer:
                line, self.buffer = self.buffer.split("\n", 1)
                line = line.rstrip("\r")

                if line.strip():
                    self.logger.log(self.level, line)

        return len(text)

    def flush(self):
        with self.lock:
            if self.terminal is not None:
                self.terminal.flush()

            if self.buffer.strip():
                self.logger.log(self.level, self.buffer.rstrip())

            self.buffer = ""

    def isatty(self):
        return False


def setup_logging():
    """Configure rotating logs once, including print and error output."""
    logger = logging.getLogger("jarvis")

    if logger.handlers:
        return LOG_FILE

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=2_000_000,
        backupCount=3,
        encoding="utf-8",
    )

    handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    ))

    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.propagate = False

    sys.stdout = LoggedStream(logger, logging.INFO, sys.stdout)
    sys.stderr = LoggedStream(logger, logging.ERROR, sys.stderr)

    atexit.register(sys.stdout.flush)
    atexit.register(sys.stderr.flush)

    logger.info("========== Jarvis starting ==========")

    return LOG_FILE