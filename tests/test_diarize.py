import numpy as np

from botmeet.diarize import MIXED, OTHERS, YOU, attribute_speakers
from botmeet.ports.transcriber import TranscriptSegment


def _stereo(left: float, right: float, seconds=1.0, sr=16000):
    n = int(sr * seconds)
    return np.stack(
        [np.full(n, left, dtype=np.float32), np.full(n, right, dtype=np.float32)], axis=1
    )


def test_attributes_you_when_right_dominates():
    segs = [TranscriptSegment(0.0, 1.0, "hola")]
    assert attribute_speakers(segs, _stereo(0.01, 0.5))[0].speaker == YOU


def test_attributes_others_when_left_dominates():
    segs = [TranscriptSegment(0.0, 1.0, "hello")]
    assert attribute_speakers(segs, _stereo(0.5, 0.01))[0].speaker == OTHERS


def test_attributes_mixed_when_balanced():
    segs = [TranscriptSegment(0.0, 1.0, "both")]
    assert attribute_speakers(segs, _stereo(0.4, 0.4))[0].speaker == MIXED


def test_clamps_out_of_range_segments():
    segs = [TranscriptSegment(10.0, 20.0, "late")]
    out = attribute_speakers(segs, _stereo(0.5, 0.01))
    assert out[0].speaker == ""  # untouched, keeps text
    assert out[0].text == "late"
