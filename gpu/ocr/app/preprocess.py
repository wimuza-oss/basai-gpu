from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import warnings

import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError


@dataclass(frozen=True)
class ImageQuality:
    width: int
    height: int
    sharpness: float
    brightness: float
    warnings: list[str]


class InvalidImage(ValueError):
    pass


def decode_image(payload: bytes, max_pixels: int = 16_000_000) -> np.ndarray:
    if not payload:
        raise InvalidImage('Gambar tidak boleh kosong.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(payload)) as opened:
                if opened.format not in ('JPEG', 'PNG'):
                    raise InvalidImage('Hanya JPEG dan PNG yang didukung.')
                w, h = opened.size
                if w < 400 or h < 200 or w * h > max_pixels:
                    raise InvalidImage('Resolusi gambar di luar batas 400x200 s.d. 16 megapiksel.')
                if getattr(opened, 'n_frames', 1) != 1:
                    raise InvalidImage('Gambar animasi tidak didukung.')
                oriented = ImageOps.exif_transpose(opened)
                rgb = np.asarray(oriented.convert('RGB'))
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        if isinstance(exc, InvalidImage):
            raise
        raise InvalidImage('Berkas bukan gambar JPEG/PNG yang valid.') from None
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def inspect_quality(image: np.ndarray) -> ImageQuality:
    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(gray.mean())
    warnings_list: list[str] = []
    if sharpness < 80:
        warnings_list.append('Foto kurang tajam; periksa hasil OCR secara manual atau ambil ulang.')
    if brightness < 65:
        warnings_list.append('Foto terlalu gelap.')
    if brightness > 215:
        warnings_list.append('Foto terlalu terang.')
    if width < 900:
        warnings_list.append('Resolusi teks KTP rendah; gunakan kamera beresolusi lebih tinggi.')
    return ImageQuality(width, height, round(sharpness, 1), round(brightness, 1), warnings_list)


def _rectify_ktp(image: np.ndarray) -> np.ndarray | None:
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 60, 155)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:8]:
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, .02 * perimeter, True)
        if len(approx) != 4:
            continue
        ratio_area = cv2.contourArea(approx) / float(w * h)
        if not (.35 < ratio_area < .98):
            continue
        pts = approx.reshape(4, 2).astype(np.float32)
        center = pts.sum(axis=1)
        delta = np.diff(pts, axis=1).reshape(-1)
        corners = np.array([pts[np.argmin(center)], pts[np.argmin(delta)],
                            pts[np.argmax(center)], pts[np.argmax(delta)]], dtype=np.float32)
        top, right, bottom, left = corners
        out_w = int(max(np.linalg.norm(right-top), np.linalg.norm(bottom-left)))
        out_h = int(max(np.linalg.norm(left-top), np.linalg.norm(bottom-right)))
        if out_h < 1 or not (1.35 < out_w / out_h < 2.1):
            continue
        out_w = min(out_w, 2400)
        out_h = min(out_h, 1600)
        matrix = cv2.getPerspectiveTransform(corners, np.float32([
            [0, 0], [out_w-1, 0], [out_w-1, out_h-1], [0, out_h-1],
        ]))
        return cv2.warpPerspective(image, matrix, (out_w, out_h))
    return None


def enhance_text(image: np.ndarray) -> np.ndarray:
    height, width = image.shape[:2]
    # Upscaling memperbaiki deteksi layout, bukan memulihkan karakter yang sudah hilang.
    scale = min(2.3, max(1.0, 1800.0 / width))
    if scale > 1:
        image = cv2.resize(image, (int(width*scale), int(height*scale)), interpolation=cv2.INTER_CUBIC)
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    corrected = cv2.merge((clahe.apply(l_channel), a_channel, b_channel))
    bgr = cv2.cvtColor(corrected, cv2.COLOR_LAB2BGR)
    denoised = cv2.bilateralFilter(bgr, 5, 40, 40)
    smooth = cv2.GaussianBlur(denoised, (0, 0), 1.0)
    return cv2.addWeighted(denoised, 1.35, smooth, -0.35, 0)


def build_variants(image: np.ndarray, max_passes: int = 2) -> list[tuple[str, np.ndarray]]:
    variants = [('original', image)]
    if max_passes <= 1:
        return variants
    straight = _rectify_ktp(image)
    variants.append(('enhanced', enhance_text(straight if straight is not None else image)))
    return variants[:max(1, min(3, max_passes))]
