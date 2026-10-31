from pathlib import Path


# Główny folder projektu — obecnie config.py znajduje się w jego katalogu.
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

# Na tym etapie zachowujemy dotychczasową lokalizację danych.
DATA_DIR = BASE_DIR / "data"

LOG_DIR = DATA_DIR / "logs"
LOG_FILE = LOG_DIR / "jarvis.log"
LOG_MAX_BYTES = 2_000_000
LOG_BACKUP_COUNT = 3

SPOTIFY_TOKEN_FILE = DATA_DIR / "spotify_token.json"
INSTANCE_LOCK_FILE = DATA_DIR / "jarvis.lock"


# Folder skryptów dostępnych dla Jarvisa.
# Pozostawiamy obecne ustawienie; listę projektów zmienimy osobno.
PROJECTS_DIR = Path(r"E:\Code")

APPS_DIR = BASE_DIR / "shortcuts"
VSCODE_EXE = Path(r"E:\Microsoft VS Code\Code.exe")


# Ollama
OLLAMA_MODEL = "qwen2.5:3b"
OLLAMA_TAGS_URL = "http://127.0.0.1:11434/api/tags"
MAX_TOOL_ROUNDS = 5


# Rozpoznawanie mowy
WHISPER_MODEL_DIR = BASE_DIR / "models" / "Whisper"
WHISPER_MODEL_NAME = "small.en"
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"

MICROPHONE = None
SAMPLE_RATE = 16000

BLOCK_SECONDS = 0.05
SILENCE_SECONDS = 1.0
START_TIMEOUT = 8.0
MAX_RECORD_SECONDS = 20.0
VOLUME_THRESHOLD = 0.015


# Wybudzanie
WAKE_MODEL_DIR = BASE_DIR / "models" / "WakeWord"
WAKE_BLOCK_SIZE = 1280
WAKE_THRESHOLD = 0.5


# Odpowiedzi głosowe
KOKORO_MODEL_DIR = BASE_DIR / "models" / "Kokoro"
TTS_VOICE = "af_heart"
TTS_LANGUAGE = "en-us"
TTS_SPEED = 1.0
OUTPUT_DEVICE = None


# Spotify
PREFERRED_SPOTIFY_DEVICE = "DESKTOP-K641TTQ"
SPOTIFY_SHORTCUT = "Spotify.lnk"
CONVERSATION_VOLUME = 10
SPOTIFY_REQUEST_TIMEOUT = 10
SPOTIFY_REDIRECT_URI_DEFAULT = "http://127.0.0.1:8888/callback"