from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str = "turbo"
    device: str = "cuda"
    compute_type: str = "int8_float16"
    max_upload_mb: int = 256
    max_audio_seconds: int = 600
    max_channels: int = 8
    language: str = "id"
    channel_labels: tuple[str, ...] = (
        "Hakim", "Penggugat atau Kuasa", "Tergugat atau Kuasa", "Saksi"
    )

    @classmethod
    def from_env(cls) -> "Settings":
        key = os.getenv("BASAI_API_KEY", "")
        if len(key) < 32:
            raise RuntimeError("BASAI_API_KEY wajib diisi minimal 32 karakter")
        model = os.getenv("BASAI_MODEL", "turbo")
        if model not in ("turbo", "large-v3", "small"):
            raise RuntimeError("BASAI_MODEL tidak ada dalam allowlist")
        device = os.getenv("BASAI_DEVICE", "cuda")
        if device != "cuda":
            raise RuntimeError("Tahap GPU tidak mengizinkan fallback ke CPU")
        compute = os.getenv("BASAI_COMPUTE_TYPE", "int8_float16")
        if compute not in ("int8_float16", "float16"):
            raise RuntimeError("compute type tidak diizinkan")
        return cls(api_key=key, model=model, device=device, compute_type=compute)
