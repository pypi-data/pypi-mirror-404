"""Transcription engine using faster-whisper."""

from __future__ import annotations

import click
from pathlib import Path
from datetime import datetime
from typing import Optional


def _get_bundled_model_path() -> Optional[Path]:
    """Check if bundled model is available via meeting-noter-models package."""
    try:
        from meeting_noter_models import get_model_path, MODEL_NAME
        model_path = get_model_path()
        if model_path.exists() and (model_path / "model.bin").exists():
            return model_path
    except ImportError:
        pass
    return None


def get_model(model_size: str = "tiny.en"):
    """Load the Whisper model.

    Priority:
    1. Bundled model from meeting-noter-models package (offline)
    2. Download from Hugging Face Hub (cached after first download)
    """
    from faster_whisper import WhisperModel

    # Check for bundled model first (for offline use)
    bundled_path = _get_bundled_model_path()
    if bundled_path and model_size == "tiny.en":
        click.echo(f"Loading bundled model '{model_size}'...")
        model = WhisperModel(
            str(bundled_path),
            device="cpu",
            compute_type="int8",
        )
        return model

    # Fall back to Hugging Face download
    click.echo(f"Loading model '{model_size}'...")

    # Use INT8 for CPU efficiency
    model = WhisperModel(
        model_size,
        device="cpu",
        compute_type="int8",
    )

    return model


def format_timestamp(seconds: float) -> str:
    """Format seconds as [HH:MM:SS] or [MM:SS]."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"[{hours:02d}:{minutes:02d}:{secs:02d}]"
    return f"[{minutes:02d}:{secs:02d}]"


def transcribe_audio(audio_path: Path, model_size: str = "tiny.en") -> str:
    """Transcribe an audio file.

    Args:
        audio_path: Path to MP3 or WAV file
        model_size: Whisper model to use

    Returns:
        Formatted transcript string
    """
    model = get_model(model_size)

    click.echo(f"Transcribing {audio_path.name}...")

    segments, info = model.transcribe(
        str(audio_path),
        beam_size=5,
        vad_filter=True,  # Voice Activity Detection
        vad_parameters=dict(
            min_silence_duration_ms=500,
        ),
    )

    # Build transcript
    lines = []
    lines.append("Meeting Transcription")
    lines.append(f"File: {audio_path.name}")
    lines.append(f"Transcribed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Language: {info.language} (probability: {info.language_probability:.2f})")
    lines.append(f"Duration: {info.duration:.1f} seconds")
    lines.append("-" * 40)
    lines.append("")

    for segment in segments:
        timestamp = format_timestamp(segment.start)
        text = segment.text.strip()
        if text:
            lines.append(f"{timestamp} {text}")

    return "\n".join(lines)


def transcribe_file(
    file: Optional[str],
    output_dir: Path,
    model_size: str = "tiny.en",
    transcripts_dir: Optional[Path] = None,
):
    """Transcribe a recording file.

    If no file specified, transcribes the most recent recording.
    Saves transcript to transcripts_dir (defaults to same as audio file).
    """
    # Find the file to transcribe
    if file:
        audio_path = Path(file)
        if not audio_path.exists():
            # Try in output dir
            audio_path = output_dir / file
        if not audio_path.exists():
            click.echo(click.style(f"File not found: {file}", fg="red"))
            return
    else:
        # Find most recent recording
        mp3_files = sorted(output_dir.glob("*.mp3"), key=lambda p: p.stat().st_mtime)
        if not mp3_files:
            click.echo(click.style(
                f"No recordings found in {output_dir}",
                fg="yellow"
            ))
            return
        audio_path = mp3_files[-1]
        click.echo(f"Using most recent recording: {audio_path.name}")

    # Determine transcript path
    if transcripts_dir:
        transcripts_dir.mkdir(parents=True, exist_ok=True)
        transcript_path = transcripts_dir / audio_path.with_suffix(".txt").name
    else:
        transcript_path = audio_path.with_suffix(".txt")
    if transcript_path.exists():
        click.echo(click.style(
            f"Transcript already exists: {transcript_path.name}",
            fg="yellow"
        ))
        if not click.confirm("Overwrite?"):
            return

    # Transcribe
    try:
        transcript = transcribe_audio(audio_path, model_size)

        # Save transcript
        transcript_path.write_text(transcript)
        click.echo(click.style(
            f"\nTranscript saved: {transcript_path}",
            fg="green"
        ))

        # Show preview
        click.echo("\n--- Preview ---")
        lines = transcript.split("\n")
        preview_lines = lines[:15]
        for line in preview_lines:
            click.echo(line)
        if len(lines) > 15:
            click.echo(f"... ({len(lines) - 15} more lines)")

    except Exception as e:
        click.echo(click.style(f"Transcription failed: {e}", fg="red"))
        raise


def transcribe_live(output_dir: Path, model_size: str = "tiny.en"):
    """Real-time transcription of ongoing recording.

    Note: This is more CPU intensive and may have latency.
    """
    click.echo(click.style(
        "Live transcription is experimental and CPU-intensive.",
        fg="yellow"
    ))

    # Find active recording (most recent, still being written)
    mp3_files = sorted(output_dir.glob("*.mp3"), key=lambda p: p.stat().st_mtime)
    if not mp3_files:
        click.echo("No recordings found. Is the daemon running?")
        return

    latest = mp3_files[-1]
    click.echo(f"Monitoring: {latest.name}")
    click.echo("Press Ctrl+C to stop.\n")

    model = get_model(model_size)
    last_position = 0

    try:
        import time
        while True:
            # Check file size
            current_size = latest.stat().st_size
            if current_size > last_position:
                # New data available - transcribe the whole file
                # (faster-whisper doesn't support streaming well)
                try:
                    segments, info = model.transcribe(
                        str(latest),
                        beam_size=3,  # Faster for live
                        vad_filter=True,
                    )

                    # Print new segments
                    for segment in segments:
                        if segment.end > last_position / 1000:  # Rough estimate
                            timestamp = format_timestamp(segment.start)
                            text = segment.text.strip()
                            if text:
                                click.echo(f"{timestamp} {text}")

                    last_position = current_size
                except Exception as e:
                    # File might be locked, retry
                    pass

            time.sleep(5)  # Check every 5 seconds

    except KeyboardInterrupt:
        click.echo("\nStopped live transcription.")
