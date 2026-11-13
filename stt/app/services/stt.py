from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory
import time
from typing import Any, Protocol

from app.core.config import Settings
from app.services.audio import AudioInfo, extract_channel


class STTServiceProtocol(Protocol):
    def transcribe(self, audio_path: Path, info: AudioInfo) -> dict[str, Any]: ...
    def check_gpu(self) -> bool: ...


class FasterWhisperService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._model: Any = None

    def check_gpu(self) -> bool:
        import ctranslate2
        supported = ctranslate2.get_supported_compute_types("cuda")
        return self.settings.compute_type in supported

    def _ensure_model(self) -> Any:
        if self._model is None:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(
                self.settings.model, device=self.settings.device,
                compute_type=self.settings.compute_type
            )
        return self._model

    def transcribe(self, audio_path: Path, info: AudioInfo) -> dict[str, Any]:
        model = self._ensure_model()
        start = time.perf_counter()
        segments: list[dict[str, Any]] = []
        # Satu berkas per sidang. Label kanal adalah posisi mic, bukan identitas terverifikasi.
        with TemporaryDirectory(prefix="basai-channels-") as temp_dir:
            for channel_idx in range(info.channels):
                channel_path = Path(temp_dir) / f"channel-{channel_idx + 1}.wav"
                extract_channel(audio_path, channel_path, channel_idx,
                                info.duration_seconds)
                result, _ = model.transcribe(
                    str(channel_path), language=self.settings.language,
                    beam_size=5, vad_filter=True, condition_on_previous_text=False
                )
                for index, segment in enumerate(result, 1):
                    label = (self.settings.channel_labels[channel_idx]
                             if info.channels > 1 and channel_idx < len(self.settings.channel_labels)
                             else None)
                    segments.append({
                        "segment_id": f"c{channel_idx + 1}-s{index}",
                        "channel_no": channel_idx + 1,
                        "speaker_role_hint": label,
                        "start_ms": round(segment.start * 1000),
                        "end_ms": round(segment.end * 1000),
                        "raw_text": segment.text.strip(),
                        "needs_review": True
                    })
        segments.sort(key=lambda x: (x["start_ms"], x["channel_no"]))
        return {
            "status": "NEEDS_REVIEW", "language": self.settings.language,
            "model": self.settings.model, "device": self.settings.device,
            "audio": asdict(info), "segments": segments,
            "processing_seconds": round(time.perf_counter() - start, 3),
        }
