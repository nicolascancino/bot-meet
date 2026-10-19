"""Transcriber adapter: local faster-whisper (CUDA on NVIDIA, CPU fallback)."""
from dataclasses import dataclass, field
from pathlib import Path
import wave

import numpy as np

from botmeet.ports.transcriber import TranscriptSegment

TARGET_SR = 16000


def _ensure_cuda_dlls() -> None:
    import os
    import site as _site

    if os.name != "nt":
        return
    candidates = set(_site.getsitepackages() or [])
    try:
        candidates.add(_site.getusersitepackages())
    except AttributeError:
        pass
    bindirs: list[str] = []
    for sp in candidates:
        nvidia = Path(sp) / "nvidia"
        if nvidia.is_dir():
            bindirs += [str(p) for p in nvidia.glob("*/bin") if p.is_dir()]
    for bindir in bindirs:
        try:
            os.add_dll_directory(bindir)
        except OSError:
            pass
    if bindirs:  # native loaders that only honor PATH, not the DLL directory list
        os.environ["PATH"] = os.pathsep.join(bindirs) + os.pathsep + os.environ.get("PATH", "")


def load_mono_16k(path: Path) -> np.ndarray:
    """Decode a PCM WAV to 16 kHz mono float32 without PyAV."""
    from scipy.signal import resample_poly

    with wave.open(str(path), "rb") as wf:
        channels = wf.getnchannels()
        rate = wf.getframerate()
        raw = wf.readframes(wf.getnframes())
    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1)
    if rate != TARGET_SR:
        audio = resample_poly(audio, TARGET_SR, rate).astype(np.float32)
    return audio


@dataclass
class FasterWhisperTranscriber:
    """Local transcription. model_size: tiny/base/small/medium/large-v3."""

    model_size: str = "base"
    device: str = "cuda"
    compute_type: str = "float16"
    _model: object = field(default=None, repr=False, compare=False)

    def _load(self):
        if self._model is None:
            _ensure_cuda_dlls()
            from faster_whisper import WhisperModel

            try:
                self._model = WhisperModel(
                    self.model_size, device=self.device, compute_type=self.compute_type
                )
            except Exception:
                if self.device != "cpu":
                    self._model = WhisperModel(self.model_size, device="cpu")
                else:
                    raise
        return self._model

    def transcribe(self, audio_path: Path) -> list[TranscriptSegment]:
        model = self._load()
        audio = load_mono_16k(audio_path)
        segments, _info = model.transcribe(audio, beam_size=5)
        return [
            TranscriptSegment(start=s.start, end=s.end, text=s.text.strip())
            for s in segments
        ]


def write_transcript(path: Path, segments: list[TranscriptSegment]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for s in segments:
            fh.write(f"[{s.start:7.2f} -> {s.end:7.2f}] {s.text}\n")
