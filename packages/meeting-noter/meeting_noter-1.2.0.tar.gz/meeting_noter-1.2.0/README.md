# Meeting Noter

Offline meeting transcription tool for macOS. Captures both your voice and meeting participants' audio, saves to MP3, and transcribes locally using Whisper.

## Features

- **No setup required** - Just install and run
- **Captures both sides** - Your mic + system audio (meeting participants)
- **Offline transcription** - Uses Whisper locally, no API calls
- **Auto-detection** - Detects active meetings (Zoom, Teams, Meet, Slack)
- **Multiple interfaces** - Menu bar app, desktop GUI, or CLI
- **Auto-segmentation** - One file per meeting (detects silence)

## Installation

```bash
pipx install meeting-noter
```

**For corporate/offline environments** (bundles Whisper model, no download needed):
```bash
pipx install "meeting-noter[offline]"
```

### Upgrading

```bash
# Standard
pipx upgrade meeting-noter

# With offline model
pipx reinstall "meeting-noter[offline]"
```

No system dependencies required - ffmpeg is bundled automatically.

## Quick Start

**Menu Bar App** (recommended):
```bash
meeting-noter menubar
```

**Desktop GUI**:
```bash
meeting-noter gui
```

**CLI Recording**:
```bash
meeting-noter start "Weekly Standup"
```

The app will request microphone and Screen Recording permissions on first use.

## Usage

### Recording
- The menu bar app auto-detects meetings and prompts to record
- Or manually start recording via the GUI/CLI
- Press Ctrl+C (CLI) or click Stop to end recording

### Transcription
Recordings are auto-transcribed by default. Or manually:

```bash
# Transcribe the most recent recording
meeting-noter transcribe

# Transcribe a specific file
meeting-noter transcribe recording.mp3

# List all recordings
meeting-noter list
```

## Commands

| Command | Description |
|---------|-------------|
| `meeting-noter` | Launch desktop GUI |
| `meeting-noter menubar` | Launch menu bar app |
| `meeting-noter gui` | Launch desktop GUI |
| `meeting-noter start [name]` | Interactive CLI recording |
| `meeting-noter list` | List recent recordings |
| `meeting-noter transcribe` | Transcribe a recording |
| `meeting-noter devices` | List audio devices |
| `meeting-noter status` | Check daemon status |

## Options

### `start`
- First argument: Meeting name (optional, auto-generates timestamp if omitted)

### `transcribe`
- `-m, --model`: Whisper model size (tiny.en, base.en, small.en, medium.en, large-v3)
- `-o, --output-dir`: Directory with recordings

### `list`
- `-n, --limit`: Number of recordings to show
- `-o, --output-dir`: Directory with recordings

## How It Works

```
┌─────────────────────────────────────┐
│         Your Meeting App            │
│      (Zoom/Teams/Meet/Slack)        │
└──────────────────┬──────────────────┘
                   │
     ┌─────────────┴─────────────┐
     ▼                           ▼
┌─────────┐               ┌─────────────┐
│   Mic   │               │ System Audio│
│(default)│               │(ScreenCaptureKit)
└────┬────┘               └──────┬──────┘
     │                           │
     └───────────┬───────────────┘
                 ▼
         ┌─────────────┐
         │Meeting Noter│
         │  (capture)  │
         └──────┬──────┘
                │
                ▼
    ~/meetings/2024-01-15_Weekly_Standup.mp3
                │
                ▼ (auto or on-demand)
         ┌─────────────┐
         │   Whisper   │ (local)
         └──────┬──────┘
                │
                ▼
    ~/meetings/2024-01-15_Weekly_Standup.txt
```

## Permissions

On first use, macOS will ask for:

1. **Microphone** - For capturing your voice
2. **Screen Recording** - For capturing system audio (meeting participants)

Grant these in System Settings > Privacy & Security.

## Configuration

Config file: `~/.config/meeting-noter/config.json`

```json
{
    "recordings_dir": "~/meetings",
    "transcripts_dir": "~/meetings",
    "whisper_model": "tiny.en",
    "auto_transcribe": true,
    "silence_timeout": 5,
    "capture_system_audio": true
}
```

## Whisper Models

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| `tiny.en` | ~75MB | Fastest | Good |
| `base.en` | ~150MB | Fast | Better |
| `small.en` | ~500MB | Medium | High |
| `medium.en` | ~1.5GB | Slow | Very High |
| `large-v3` | ~3GB | Slowest | Best |

## Requirements

- macOS 12.3+ (for ScreenCaptureKit)
- Python 3.9+

## License

MIT
