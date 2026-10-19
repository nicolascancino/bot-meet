"""Analyzer port: turns a transcript into summaries and Mermaid diagrams."""
from dataclasses import dataclass
from typing import Protocol

from botmeet.ports.transcriber import TranscriptSegment


@dataclass(frozen=True)
class MeetingNotes:
    summary: str
    decisions: list[str]
    action_items: list[str]
    sequence_diagram_mermaid: str
    architecture_diagram_mermaid: str


class Analyzer(Protocol):
    def analyze(self, segments: list[TranscriptSegment]) -> MeetingNotes:
        """Generate structured notes and diagrams from a transcript."""
        ...
