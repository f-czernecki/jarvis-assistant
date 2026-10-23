# Jarvis

Jarvis is a personal voice assistant built in Python. It runs in the
background on Windows and listens for “Hey Jarvis” to start a conversation.

This is the first working version. It can answer questions and control Spotify.

## What works so far

- Conversations in English with a local language model.
- Voice responses, with “Hey Jarvis” to interrupt playback.
- Playing songs and playlists on Spotify.
- Pausing music, skipping tracks, and changing volume.
- A tray icon to pause listening, open logs, or close the assistant.
- Starting automatically after logging into Windows.

## Built with

- Ollama with Qwen2.5 for conversations and tool calls.
- faster-whisper for speech recognition.
- openWakeWord for “Hey Jarvis” detection.
- Kokoro ONNX for voice output.
- Spotify Web API for music control.
- pystray for the tray menu.

The speech models and language model run locally. Spotify control
requires an internet connection.

## Next steps

- Searching and discussing papers from a personal article library.
- Working with engineering software such as Autodesk Fusion.
- Running Python scripts and handling longer tasks.
- Eventually building a physical version for the desk.

## Current state

Version 1.0 works on the computer it was configured for. Some paths
and settings are still hardcoded, and there are bugs and rough edges
to work through. Liked Songs playback is not supported yet.
