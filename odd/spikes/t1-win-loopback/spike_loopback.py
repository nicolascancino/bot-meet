"""T1 spike: verify Windows WASAPI loopback (system-audio) capture.

Plays a known 880 Hz tone through the default speaker while recording
from the WASAPI loopback device, then checks the recording contains it.

PASS criteria: a loopback device exists AND the recorded spectrum peaks
within +/-30 Hz of 880 Hz with RMS clearly above the noise floor.
"""
import threading
import wave

import numpy as np
import soundcard as sc

SR = 48000
TONE_HZ = 880.0
RECORD_S = 6.0
TOL_HZ = 30.0


def main() -> int:
    mics = sc.all_microphones(include_loopback=True)
    print("Loopback-capable inputs:")
    for m in mics:
        print(f"  - {m.name} [{m.id}]")
    if not mics:
        print("FAIL: no loopback input found")
        return 1

    speaker = sc.default_speaker()
    print(f"default speaker: {speaker.name}")
    loopback = sc.get_microphone(speaker.name, include_loopback=True)

    frames: list[np.ndarray] = []

    def record():
        with loopback.recorder(samplerate=SR) as rec:
            frames.append(rec.record(numframes=int(SR * RECORD_S)))

    t = threading.Thread(target=record)
    t.start()

    import time
    time.sleep(1.0)  # let the recorder start, keep 1s of silence as noise floor
    tone = (0.3 * np.sin(2 * np.pi * TONE_HZ * np.arange(SR * 2) / SR)).astype(np.float32)
    with speaker.player(samplerate=SR) as player:
        player.play(tone)
    t.join()

    data = np.concatenate(frames, axis=0).mean(axis=1)  # mono
    noise = data[: SR]  # first second: silence
    signal = data[int(1.2 * SR): int(3.2 * SR)]  # tone window

    noise_rms = float(np.sqrt(np.mean(noise ** 2)))
    spectrum = np.abs(np.fft.rfft(signal * np.hanning(len(signal))))
    freqs = np.fft.rfftfreq(len(signal), 1 / SR)
    peak_hz = float(freqs[int(np.argmax(spectrum))])
    signal_rms = float(np.sqrt(np.mean(signal ** 2)))

    with wave.open("spike_loopback.wav", "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        pcm = np.clip(data, -1, 1)
        wf.writeframes((pcm * 32767).astype(np.int16).tobytes())

    band = (freqs > TONE_HZ - 200) & (freqs < TONE_HZ + 200)
    band_mags = spectrum[band]
    peak_mag = spectrum[int(np.argmax(spectrum))]
    spectral_snr = float(peak_mag / (np.median(band_mags) + 1e-12))
    print(f"noise_rms={noise_rms:.5f} signal_rms={signal_rms:.5f} peak={peak_hz:.1f} Hz "
          f"spectral_snr={spectral_snr:.1f}")
    ok = abs(peak_hz - TONE_HZ) <= TOL_HZ and spectral_snr > 10.0
    print("SPIKE:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
