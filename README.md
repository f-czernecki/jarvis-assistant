# Jarvis — Personal AI Assistant

Jarvis is a voice-controlled desktop assistant for Windows. It runs
in the background, wakes up when it hears “Hey Jarvis,” and responds
in English using a natural voice.

## Features

- Voice conversations with a local language model.
- Spoken responses that can be interrupted with “Hey Jarvis.”
- Application launching and opening Python files in VS Code.
- Spotify control: songs, playlists, play/pause, track skipping,
  and volume adjustment.
- Automatic music ducking during conversations.
- Standby mode after playback commands or “Thanks Jarvis.”
- System tray controls for pausing, resuming, and exiting.
- Windows autostart, rotating logs, and single-instance protection.

## Technology

Python · Ollama / Qwen2.5 · faster-whisper · openWakeWord ·
Kokoro ONNX · Spotify Web API · pystray

Speech recognition, language processing, and speech synthesis run
locally. Spotify control uses the Spotify Web API.

## Planned Features

- Research assistance using a personal library of academic papers.
- Integration with engineering applications, including Autodesk Fusion.
- Python script execution and project workflow automation.
- A physical desktop interface.

## Status

Version 1.0 is configured for a specific Windows environment.
Paths and device settings require manual configuration.
Liked Songs playback is not available in this version.