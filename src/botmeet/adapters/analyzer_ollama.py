"""Analyzer adapter: local Ollama (OpenAI-compatible chat endpoint)."""
import json
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from botmeet.ports.analyzer import MeetingNotes
from botmeet.ports.transcriber import TranscriptSegment

TRANSCRIPT_LINE = re.compile(
    r"\[\s*([\d.]+)\s*->\s*([\d.]+)\]\s*(?:(YOU|OTHERS|MIXED):\s*)?(.*)"
)


def read_transcript(path: Path) -> list[TranscriptSegment]:
    segments = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = TRANSCRIPT_LINE.match(line)
        if match:
            start, end, speaker, text = match.groups()
            segments.append(TranscriptSegment(float(start), float(end), text, speaker or ""))
    return segments


def build_prompt(segments: list[TranscriptSegment]) -> str:
    body = "\n".join(
        f"[{s.start:.0f}s{f' {s.speaker}' if s.speaker else ''}] {s.text}" for s in segments
    )
    return f"""You are a meeting analyst. Read this transcript and respond with JSON only
(no markdown fences, no commentary) using exactly these keys:
"summary" (string, 3-5 sentences), "decisions" (string array),
"action_items" (string array), "sequence_diagram_mermaid" (a valid Mermaid
sequenceDiagram showing who said/did what, participant names from context),
"architecture_diagram_mermaid" (a valid Mermaid graph TD of the system or
concepts discussed; empty string if the meeting has no technical content).
In both diagrams put each statement on its own line (never the whole diagram
on a single line). The *_mermaid values must be Mermaid code, never prose.
If a diagram has no content, use an empty string. Example:
"sequence_diagram_mermaid": "sequenceDiagram\n    Nico->>Team: Propone canales L/R\n    Team-->>Nico: De acuerdo"
Write all values in the same language as the transcript.

Transcript:
{body}"""


def parse_notes(payload: dict) -> MeetingNotes:
    return MeetingNotes(
        summary=str(payload.get("summary", "")),
        decisions=[str(d) for d in payload.get("decisions", [])],
        action_items=[str(a) for a in payload.get("action_items", [])],
        sequence_diagram_mermaid=str(payload.get("sequence_diagram_mermaid", "")),
        architecture_diagram_mermaid=str(payload.get("architecture_diagram_mermaid", "")),
    )


@dataclass
class OllamaAnalyzer:
    model: str = "qwen2.5:7b-instruct"
    host: str = "http://localhost:11434"
    timeout_s: float = 300.0

    def analyze(self, segments: list[TranscriptSegment]) -> MeetingNotes:
        body = json.dumps(
            {
                "model": self.model,
                "messages": [{"role": "user", "content": build_prompt(segments)}],
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.2},
            }
        ).encode()
        request = urllib.request.Request(
            f"{self.host}/api/chat", data=body, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
            result = json.load(response)
        return parse_notes(json.loads(result["message"]["content"]))


def write_notes(path: Path, notes: MeetingNotes) -> None:
    decisions = "\n".join(f"- {d}" for d in notes.decisions) or "_none_"
    actions = "\n".join(f"- [ ] {a}" for a in notes.action_items) or "_none_"
    path.write_text(
        "# Meeting notes\n\n"
        f"## Summary\n\n{notes.summary}\n\n"
        f"## Decisions\n\n{decisions}\n\n"
        f"## Action items\n\n{actions}\n\n"
        f"## Sequence diagram\n\n```mermaid\n{notes.sequence_diagram_mermaid}\n```\n\n"
        f"## Architecture diagram\n\n```mermaid\n{notes.architecture_diagram_mermaid}\n```\n",
        encoding="utf-8",
    )
