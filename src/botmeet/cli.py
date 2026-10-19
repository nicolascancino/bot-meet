"""botmeet CLI (smoke path until the floating widget lands)."""
import argparse
from datetime import date
from pathlib import Path

from botmeet.capture import record_session


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="botmeet")
    sub = parser.add_subparsers(dest="command", required=True)
    rec = sub.add_parser("record", help="record a fixed-length session")
    rec.add_argument("--project", required=True)
    rec.add_argument("--seconds", type=float, default=10.0)
    rec.add_argument("--root", type=Path, default=Path("meetings").resolve().parent)
    wid = sub.add_parser("widget", help="floating recorder widget")
    wid.add_argument("--root", type=Path, default=Path("meetings").resolve().parent)
    wid.add_argument("--smoke-seconds", type=float, default=0.0)
    tr = sub.add_parser("transcribe", help="transcribe an audio file locally")
    tr.add_argument("--audio", type=Path, required=True)
    tr.add_argument("--model", default="base")
    tr.add_argument("--device", default="cuda")
    an = sub.add_parser("analyze", help="generate notes from a transcript")
    an.add_argument("--transcript", type=Path, required=True)
    an.add_argument("--model", default="qwen2.5:7b-instruct")
    rn = sub.add_parser("render", help="render Mermaid diagrams from notes.md")
    rn.add_argument("--notes", type=Path, required=True)
    rn.add_argument("--format", default="svg", choices=["svg", "png"])
    dv = sub.add_parser("devices", help="list audio devices")
    mc = sub.add_parser("mic-check", help="measure mic level")
    mc.add_argument("--seconds", type=float, default=3.0)
    mc.add_argument("--mic", default=None, help="substring of the mic name")
    rec.add_argument("--mic", default=None, help="substring of the mic name")
    args = parser.parse_args(argv)

    if args.command == "record":
        out = record_session(args.root, args.project, date.today(), args.seconds, mic_query=args.mic)
        print(f"saved {out}")
        return 0
    if args.command == "widget":
        from botmeet.ui_widget import run_widget

        return run_widget(args.root, args.smoke_seconds)
    if args.command == "transcribe":
        from botmeet.adapters.transcriber_faster_whisper import (
            FasterWhisperTranscriber,
            write_transcript,
        )

        transcriber = FasterWhisperTranscriber(model_size=args.model, device=args.device)
        segments = transcriber.transcribe(args.audio)
        out = args.audio.parent / "transcript.txt"
        write_transcript(out, segments)
        for s in segments:
            print(f"[{s.start:7.2f} -> {s.end:7.2f}] {s.text}")
        print(f"saved {out} ({len(segments)} segments)")
        return 0
    if args.command == "analyze":
        from botmeet.adapters.analyzer_ollama import (
            OllamaAnalyzer,
            read_transcript,
            write_notes,
        )

        segments = read_transcript(args.transcript)
        notes = OllamaAnalyzer(model=args.model).analyze(segments)
        out = args.transcript.parent / "notes.md"
        write_notes(out, notes)
        print(f"saved {out}")
        return 0
    if args.command == "devices":
        from botmeet.capture import list_devices

        for kind, names in list_devices().items():
            print(f"{kind}:")
            for name in names:
                print(f"  - {name}")
        return 0
    if args.command == "mic-check":
        from botmeet.capture import mic_level

        print(f"recording mic {args.mic or '(default)'} for {args.seconds}s, speak now...")
        peak, rms = mic_level(args.seconds, args.mic)
        print(f"peak={peak:.4f} rms={rms:.5f} (silence is ~0.000)")
        return 0
    if args.command == "render":
        from botmeet.render import render_notes

        for out in render_notes(args.notes, args.format):
            print(f"saved {out}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
