"""Transcriber port: converts recorded audio into timestamped segments."""
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class TranscriptSegment:
    start: float
    end: float
    text: str
    speaker: str = ""


class Transcriber(Protocol):
    def transcribe(self, audio_path: Path) -> list[TranscriptSegment]:
        """Transcribe an audio file, returning one segment per utterance."""
        ...
