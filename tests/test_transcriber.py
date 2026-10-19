import importlib.util
import wave

import numpy as np
import pytest

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("scipy") is None,
    reason="transcribe-cuda extra not installed",
)

from botmeet.adapters.transcriber_faster_whisper import load_mono_16k


def _write_stereo_wav(path, samplerate=48000, seconds=1.0, freq=880.0):
    t = np.arange(int(samplerate * seconds)) / samplerate
    left = 0.5 * np.sin(2 * np.pi * freq * t)
    right = 0.25 * np.sin(2 * np.pi * freq * t)
    stereo = np.stack([left, right], axis=1)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes((stereo * 32767).astype(np.int16).tobytes())


def test_load_mono_16k_downmixes_and_resamples(tmp_path):
    wav = tmp_path / "in.wav"
    _write_stereo_wav(wav)
    audio = load_mono_16k(wav)
    assert audio.dtype == np.float32
    assert len(audio) == 16000  # 1 s at 16 kHz
    spectrum = np.abs(np.fft.rfft(audio))
    freqs = np.fft.rfftfreq(len(audio), 1 / 16000)
    assert abs(float(freqs[int(np.argmax(spectrum))]) - 880.0) < 5.0
