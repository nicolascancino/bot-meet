from botmeet.render import extract_mermaid_blocks

MD = """# Notes

```mermaid
sequenceDiagram
A->>B: hi
```

```mermaid
graph TD
A-->B
```
"""


def test_extract_mermaid_blocks():
    blocks = extract_mermaid_blocks(MD)
    assert len(blocks) == 2
    assert blocks[0].startswith("sequenceDiagram")
    assert blocks[1].startswith("graph TD")


def test_extract_ignores_empty_and_other_fences():
    md = "```python\nprint(1)\n```\n```mermaid\n\n```\n"
    assert extract_mermaid_blocks(md) == []
