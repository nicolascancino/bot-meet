from datetime import date

from botmeet.storage import session_dir


def test_session_dir_layout(tmp_path):
    got = session_dir(tmp_path, "demo", date(2026, 10, 18))
    assert got == tmp_path / "meetings" / "demo" / "2026-10-18"
    assert got.is_dir()
