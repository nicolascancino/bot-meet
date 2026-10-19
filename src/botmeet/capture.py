"""Capture engine: records system audio + microphone into one stereo WAV.

Left channel = system (loopback of the default speaker), right channel = mic.
Stereo (instead of a mono mix) keeps both sources separable for later
transcription and diarization.
"""
import threading
import wave
from datetime import date
from pathlib import Path

import numpy as np

from botmeet.storage import session_dir

SAMPLE_RATE = 48000


def _thread_com_init() -> bool:
    """Init COM STA on this worker thread (WASAPI needs it). True if we own it."""
    import os

    if os.name != "nt":
        return False
    import ctypes

    hr = ctypes.windll.ole32.CoInitializeEx(None, 0x2) & 0xFFFFFFFF
    return hr in (0x0, 0x1)  # S_OK, S_FALSE; anything else (e.g. MTA) isn't ours


def list_devices() -> dict[str, list[str]]:
    import soundcard as sc

    return {
        "speakers": [s.name for s in sc.all_speakers()],
        "microphones": [m.name for m in sc.all_microphones(include_loopback=False)],
    }


def mic_level(seconds: float = 3.0, mic_query: str | None = None) -> tuple[float, float]:
    """Record a mic briefly; return (max, rms) in 0..1."""
    import soundcard as sc

    mic = sc.get_microphone(resolve_mic(mic_query)) if mic_query else sc.default_microphone()
    with mic.recorder(samplerate=SAMPLE_RATE) as rec:
        data = rec.record(numframes=int(SAMPLE_RATE * seconds)).mean(axis=1)
    norm = np.abs(data)
    return float(norm.max()), float(np.sqrt((data**2).mean()))


def resolve_mic(query: str | None) -> str | None:
    """Match a mic by case-insensitive substring; None returns None (default)."""
    if not query:
        return None
    import soundcard as sc

    names = [m.name for m in sc.all_microphones(include_loopback=False)]
    hits = [n for n in names if query.lower() in n.lower()]
    if not hits:
        raise ValueError(f"no microphone matches {query!r}; available: {names}")
    return hits[0]


def mix_to_stereo(system: np.ndarray, mic: np.ndarray) -> np.ndarray:
    """Combine two mono tracks into a clipped stereo (system=L, mic=R) track."""
    n = min(len(system), len(mic))
    stereo = np.stack([system[:n], mic[:n]], axis=1)
    return np.clip(stereo, -1.0, 1.0).astype(np.float32)


def _record_device(device, seconds: float, out: list, samplerate: int) -> None:
    with device.recorder(samplerate=samplerate) as rec:
        out.append(rec.record(numframes=int(samplerate * seconds)))


class Recorder:
    """Blocking session recorder; call start() then stop(path) from another thread."""

    def __init__(self, system_id: str | None = None, mic_id: str | None = None):
        import soundcard as sc

        speaker = sc.default_speaker()
        loopback_id = system_id or speaker.name
        self._system = sc.get_microphone(loopback_id, include_loopback=True)
        self._mic = (
            sc.get_microphone(mic_id) if mic_id else sc.default_microphone()
        )
        self._stop = threading.Event()
        self._system_chunks: list[np.ndarray] = []
        self._mic_chunks: list[np.ndarray] = []
        self._threads: list[threading.Thread] = []

    def start(self) -> None:
        self._stop.clear()
        self._system_chunks = []
        self._mic_chunks = []
        self._threads = [
            threading.Thread(
                target=self._loop, args=(self._system, self._system_chunks), daemon=True
            ),
            threading.Thread(
                target=self._loop, args=(self._mic, self._mic_chunks), daemon=True
            ),
        ]
        for thread in self._threads:
            thread.start()

    def _loop(self, device, out: list) -> None:
        ours = _thread_com_init()
        try:
            with device.recorder(samplerate=SAMPLE_RATE) as rec:
                while not self._stop.is_set():
                    out.append(rec.record(numframes=SAMPLE_RATE // 2))
        finally:
            if ours:
                import ctypes

                ctypes.windll.ole32.CoUninitialize()

    def stop(self) -> np.ndarray:
        self._stop.set()
        for thread in self._threads:
            thread.join()
        system = np.concatenate(self._system_chunks, axis=0).mean(axis=1)
        mic = np.concatenate(self._mic_chunks, axis=0).mean(axis=1)
        return mix_to_stereo(system, mic)


def write_wav(path: Path, stereo: np.ndarray, samplerate: int = SAMPLE_RATE) -> None:
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes((stereo * 32767).astype(np.int16).tobytes())


def record_session(
    root: Path, project: str, day: date, seconds: float, mic_query: str | None = None
) -> Path:
    """Record a fixed-length session (smoke/CLI path); returns the WAV path."""
    session = session_dir(root, project, day)
    recorder = Recorder(mic_id=resolve_mic(mic_query))
    recorder.start()
    import time
    time.sleep(seconds)
    stereo = recorder.stop()
    out = session / "audio.wav"
    write_wav(out, stereo)
    return out
