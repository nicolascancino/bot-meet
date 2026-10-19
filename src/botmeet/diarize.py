"""Coarse diarization from the stereo recording (system=L, local mic=R).

No ML: per-segment channel energy decides whether the local user (YOU),
the remote side (OTHERS), or both (MIXED) were speaking. Neural diarization
(whisperx/pyannote) remains a future upgrade for multi-speaker separation.
"""
import numpy as np

from botmeet.ports.transcriber import TranscriptSegment

YOU = "YOU"
OTHERS = "OTHERS"
MIXED = "MIXED"
DOMINANCE_RATIO = 2.0


def attribute_speakers(
    segments: list[TranscriptSegment],
    stereo_16k: np.ndarray,
    dominance_ratio: float = DOMINANCE_RATIO,
) -> list[TranscriptSegment]:
    """Return new segments with speaker labels from channel energy."""
    out = []
    for seg in segments:
        start = max(0, int(seg.start * 16000))
        end = min(len(stereo_16k), int(seg.end * 16000))
        if end <= start:
            out.append(seg)
            continue
        window = stereo_16k[start:end]
        left = float(np.sqrt((window[:, 0] ** 2).mean()))
        right = float(np.sqrt((window[:, 1] ** 2).mean()))
        if right >= left * dominance_ratio:
            speaker = YOU
        elif left >= right * dominance_ratio:
            speaker = OTHERS
        else:
            speaker = MIXED
        out.append(TranscriptSegment(seg.start, seg.end, seg.text, speaker))
    return out
