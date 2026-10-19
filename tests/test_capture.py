import sys
import types

import numpy as np
import pytest

from botmeet.capture import mix_to_stereo, resolve_mic


def test_mix_routes_system_left_and_mic_right():
    system = np.array([0.5, -0.5, 0.25], dtype=np.float32)
    mic = np.array([0.1, 0.2, 0.3], dtype=np.float32)
    stereo = mix_to_stereo(system, mic)
    assert stereo.shape == (3, 2)
    assert stereo[:, 0].tolist() == pytest.approx([0.5, -0.5, 0.25])
    assert stereo[:, 1].tolist() == pytest.approx([0.1, 0.2, 0.3])


def test_resolve_mic_matches_substring_case_insensitive(monkeypatch):
    class FakeMic:
        def __init__(self, name):
            self.name = name

    fake = types.ModuleType("soundcard")
    fake.all_microphones = lambda include_loopback=False: [
        FakeMic("Microfono (HyperX)"),
        FakeMic("Microphone Array"),
    ]
    monkeypatch.setitem(sys.modules, "soundcard", fake)
    assert resolve_mic("hyperx") == "Microfono (HyperX)"
    assert resolve_mic(None) is None
    with pytest.raises(ValueError, match="no microphone matches"):
        resolve_mic("zzz")


def test_mix_truncates_to_shortest_and_clips():
    system = np.array([2.0, 0.0], dtype=np.float32)
    mic = np.array([-2.0], dtype=np.float32)
    stereo = mix_to_stereo(system, mic)
    assert stereo.shape == (1, 2)
    assert stereo[0, 0] == 1.0
    assert stereo[0, 1] == -1.0
