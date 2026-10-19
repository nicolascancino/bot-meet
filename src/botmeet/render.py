"""Render Mermaid blocks from notes.md into SVG/PNG via mermaid-cli (mmdc)."""
import os
import re
import subprocess
from pathlib import Path

MERMAID_BLOCK = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)


def extract_mermaid_blocks(markdown: str) -> list[str]:
    return [b.strip() for b in MERMAID_BLOCK.findall(markdown) if b.strip()]


def render_notes(notes_path: Path, image_format: str = "svg") -> list[Path]:
    blocks = extract_mermaid_blocks(notes_path.read_text(encoding="utf-8"))
    outputs: list[Path] = []
    failures: list[str] = []
    for i, block in enumerate(blocks, start=1):
        mmd = notes_path.parent / f"diagram-{i}.mmd"
        out = notes_path.parent / f"diagram-{i}.{image_format}"
        mmd.write_text(block + "\n", encoding="utf-8")
        # npm shims are .cmd files on Windows: CreateProcess needs a shell.
        binary = "mmdc.cmd" if os.name == "nt" else "mmdc"
        try:
            subprocess.run(
                [binary, "-i", str(mmd), "-o", str(out), "-b", "white"],
                check=True,
                capture_output=True,
                text=True,
                shell=os.name == "nt",
            )
        except subprocess.CalledProcessError as e:
            failures.append(f"{mmd.name}: {e.stderr.strip().splitlines()[-1]}")
            continue
        outputs.append(out)
    if failures:
        raise RuntimeError("mmdc failed:\n" + "\n".join(failures))
    return outputs
