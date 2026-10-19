# bot-meet

Floating meeting assistant: record system audio + mic from any meeting app
(Meet, Teams, Zoom), transcribe locally with Whisper, store per project, and
generate summaries plus Mermaid diagrams (sequence, architecture).

## Layout

- `src/botmeet/` — package (`ports/`: `Transcriber`, `Analyzer`; `adapters/`: per-OS/provider implementations; `storage.py`: `meetings/<project>/<date>/` layout)
- `tests/` — pytest suite
- `odd/` — ODD feature docs and spikes (not shipped)
- `meetings/` — recorded sessions (git-ignored)

## Dev

```bash
uv sync
uv run pytest
```

Platform extras:

```bash
uv sync --extra transcribe-cuda   # NVIDIA GPU transcription (Windows/Linux)
```

Run everything with plain `uv run botmeet ...` (UI ships by default).
Transcription needs the CUDA extra installed first.
