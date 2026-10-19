"""Session storage layout: meetings/<project>/<date>/ with audio + transcript + notes."""
from datetime import date
from pathlib import Path


def session_dir(root: Path, project: str, day: date) -> Path:
    """Return (creating if needed) the directory for one meeting session."""
    path = root / "meetings" / project / day.isoformat()
    path.mkdir(parents=True, exist_ok=True)
    return path
