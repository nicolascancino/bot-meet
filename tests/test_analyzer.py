from botmeet.adapters.analyzer_ollama import build_prompt, parse_notes, read_transcript
from botmeet.ports.transcriber import TranscriptSegment

SAMPLE = [
    TranscriptSegment(0.0, 3.0, "Bueno, arranquemos con el diseño del grabador"),
    TranscriptSegment(3.0, 7.0, "Propongo guardar sistema en canal izquierdo y mic en derecho"),
    TranscriptSegment(7.0, 11.0, "De acuerdo, y transcribimos con Whisper local"),
]


def test_build_prompt_embeds_transcript():
    prompt = build_prompt(SAMPLE)
    assert "canal izquierdo" in prompt
    assert "sequence_diagram_mermaid" in prompt


def test_parse_notes_defaults_missing_keys():
    notes = parse_notes({"summary": "s"})
    assert notes.summary == "s"
    assert notes.decisions == []
    assert notes.action_items == []
    assert notes.sequence_diagram_mermaid == ""


def test_parse_notes_full_payload():
    notes = parse_notes(
        {
            "summary": "s",
            "decisions": ["d1"],
            "action_items": ["a1"],
            "sequence_diagram_mermaid": "sequenceDiagram\nA->>B: hi",
            "architecture_diagram_mermaid": "graph TD\nA-->B",
        }
    )
    assert notes.decisions == ["d1"]
    assert "sequenceDiagram" in notes.sequence_diagram_mermaid


def test_read_transcript_roundtrip(tmp_path):
    path = tmp_path / "transcript.txt"
    path.write_text("[   0.00 ->    3.20] hola mundo\n[   3.20 ->    5.00] chau\n", encoding="utf-8")
    segments = read_transcript(path)
    assert [(s.start, s.end, s.text) for s in segments] == [
        (0.0, 3.2, "hola mundo"),
        (3.2, 5.0, "chau"),
    ]


def test_read_transcript_with_speaker_tags(tmp_path):
    from botmeet.adapters.transcriber_faster_whisper import write_transcript

    path = tmp_path / "transcript.txt"
    write_transcript(
        path,
        [
            TranscriptSegment(0.0, 1.0, "yo hablo", "YOU"),
            TranscriptSegment(1.0, 2.0, "sin marca"),
        ],
    )
    segments = read_transcript(path)
    assert [(s.speaker, s.text) for s in segments] == [
        ("YOU", "yo hablo"),
        ("", "sin marca"),
    ]
