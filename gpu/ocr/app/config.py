from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    token: str
    max_upload_bytes: int = 5 * 1024 * 1024
    max_image_pixels: int = 16_000_000
    enable_gpu: bool = True
    max_ocr_passes: int = 2
    min_field_confidence: float = 0.45

    @classmethod
    def from_env(cls) -> 'Settings':
        token = os.environ.get('BASAI_OCR_TOKEN', '')
        if len(token) < 32:
            raise RuntimeError('BASAI_OCR_TOKEN harus acak dan minimal 32 karakter.')
        return cls(
            token=token,
            enable_gpu=os.environ.get('OCR_REQUIRE_GPU', '1') == '1',
            max_ocr_passes=int(os.environ.get('OCR_MAX_PASSES', '2')),
        )
