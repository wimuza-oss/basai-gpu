from dataclasses import dataclass
from pathlib import Path
import subprocess
import wave


class AudioValidationError(ValueError):
    pass


@dataclass(frozen=True)
class AudioInfo:
    channels: int
    sample_rate: int
    sample_width_bytes: int
    duration_seconds: float


def inspect_wav(path: Path, max_seconds: int, max_channels: int) -> AudioInfo:
    try:
        with wave.open(str(path), "rb") as wav:
            if wav.getcomptype() != "NONE":
                raise AudioValidationError("WAV terkompresi tidak didukung")
            channels = wav.getnchannels()
            rate = wav.getframerate()
            width = wav.getsampwidth()
            duration = wav.getnframes() / rate if rate else 0
    except (wave.Error, EOFError, OSError, ZeroDivisionError) as exc:
        raise AudioValidationError("Berkas bukan PCM WAV yang valid") from exc

    if not 1 <= channels <= max_channels:
        raise AudioValidationError("Jumlah kanal di luar batas")
    if rate < 8000 or rate > 192000 or width not in (2, 3, 4):
        raise AudioValidationError("Sample rate atau sample width tidak didukung")
    if not 0 < duration <= max_seconds:
        raise AudioValidationError("Durasi audio di luar batas pilot")
    return AudioInfo(channels, rate, width, duration)


def extract_channel(input_wav: Path, output_wav: Path, channel_index: int,
                    duration_seconds: float) -> None:
    # Pisahkan kanal tanpa mengubah sumber; output 16kHz, mono, PCM 16-bit.
    cmd = [
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(input_wav), "-filter:a", f"pan=mono|c0=c{channel_index}",
        "-ar", "16000", "-c:a", "pcm_s16le", str(output_wav)
    ]
    try:
        subprocess.run(cmd, capture_output=True, check=True,
                       timeout=max(60, int(duration_seconds * 1.5)))
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
        raise RuntimeError("Normalisasi kanal WAV gagal") from exc
