# CLAUDE.md
Response with Japanese.
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a LiveKit voice AI agent playground that implements a voice assistant using OpenAI's models for speech-to-text, language processing, and text-to-speech.

## Key Dependencies

- **livekit-agents==1.1.3** - Core LiveKit agents framework
- **livekit-plugins-openai==1.1.3** - OpenAI integration for STT/TTS/LLM
- **livekit-plugins-silero==1.1.3** - Voice Activity Detection (VAD)
- **livekit-plugins-turn-detector==1.1.3** - Conversation turn detection
- **livekit-plugins-noise-cancellation==0.2.4** - Audio noise cancellation

## Environment Setup

The project uses a `.env` file with the following required variables:
- `OPENAI_API_KEY` - Your OpenAI API key
- `LIVEKIT_API_KEY` - LiveKit API key (default: "devkey" for local dev)
- `LIVEKIT_API_SECRET` - LiveKit API secret (default: "secret" for local dev)
- `LIVEKIT_URL` - LiveKit server URL (default: "http://localhost:7880/")

## Common Commands

### Running the Agent
```bash
python agent.py dev
```

### Managing Dependencies
Since there's no requirements.txt file, create one if needed:
```bash
pip freeze > requirements.txt
```

### Known Issues

1. **WSL Audio Support**: The agent requires audio input/output which doesn't work by default in WSL. Users need to either:
   - Run on native Windows/Mac/Linux
   - Set up WSL audio passthrough (complex)
   - Deploy to cloud where audio is handled differently

2. **PortAudio Dependencies**: On Ubuntu/Debian systems, install:
   ```bash
   sudo apt-get update && sudo apt-get install -y portaudio19-dev python3-pyaudio
   ```

## Architecture

The codebase follows a simple single-file architecture:
- `agent.py` - Main entry point containing:
  - `Assistant` class - Extends LiveKit's Agent base class
  - `entrypoint` function - Sets up the agent session with AI services
  - CLI runner - Uses LiveKit's built-in CLI for development

The agent uses LiveKit's session-based architecture where:
1. An `AgentSession` is configured with various AI services (STT, LLM, TTS, VAD)
2. The session connects to a LiveKit room
3. The agent responds to user voice input with AI-generated responses