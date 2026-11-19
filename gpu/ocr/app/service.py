from __future__ import annotations

from dataclasses import asdict
from time import perf_counter

import numpy as np

from app.engine import OcrEngine, OcrLine, assemble_rows
from app.parser import REQUIRED_OCR_FIELDS, parse_ktp
from app.preprocess import build_variants, inspect_quality


class KtpOcrService:
    def __init__(self, engine: OcrEngine, max_passes: int = 2):
        self.engine = engine
        self.max_passes = max_passes

    def recognize(self, image: np.ndarray) -> dict:
        begin = perf_counter()
        quality = inspect_quality(image)
        candidates: list[dict] = []
        for variant, prepared in build_variants(image, max_passes=self.max_passes):
            lines: list[OcrLine] = assemble_rows(self.engine.recognize(prepared))
            parsed = parse_ktp(lines)
            score = len(parsed.fields) + sum(parsed.confidences.values())
            candidates.append({
                'variant': variant,
                'score': score,
                'lines': lines,
                'fields': parsed.fields,
                'confidence': parsed.confidences,
            })
            if (len(parsed.fields) >= 12 and all(k in parsed.fields for k in ('nik', 'nama', 'tempat_lahir', 'tanggal_lahir'))):
                break
        best = max(candidates, key=lambda c: c['score'])
        merged_fields: dict[str, str] = {}
        merged_confidence: dict[str, float] = {}
        conflicts: set[str] = set()
        for candidate in candidates:
            for key, val in candidate['fields'].items():
                conf = candidate['confidence'][key]
                if key in merged_fields and merged_fields[key] != val:
                    conflicts.add(key)
                if key not in merged_fields or conf > merged_confidence[key]:
                    merged_fields[key] = val
                    merged_confidence[key] = conf
        missing_fields = [key for key in REQUIRED_OCR_FIELDS if not merged_fields.get(key)]
        warnings = list(quality.warnings)
        if missing_fields:
            warnings.append(
                f'{len(missing_fields)} dari {len(REQUIRED_OCR_FIELDS)} kolom prioritas belum terbaca; periksa dan isi manual.'
            )
        if conflicts:
            warnings.append('Ada perbedaan pembacaan antar-pass; verifikasi kolom yang meragukan.')
        if not merged_fields:
            warnings.append('Belum ada field valid; periksa RAW OCR text atau ambil ulang foto.')
        raw_text = '\n'.join(line.text for line in best['lines'])
        status = 'OCR_REVIEW' if merged_fields else 'OCR_NO_FIELDS'
        return {
            'status': status,
            'fields': merged_fields,
            'required_fields': list(REQUIRED_OCR_FIELDS),
            'missing_fields': missing_fields,
            'required_complete': not missing_fields,
            'raw_text': raw_text,
            'field_confidences': {key: round(score, 3) for key, score in merged_confidence.items()},
            'review_required': True,
            'conflicting_fields': sorted(conflicts),
            'quality': asdict(quality),
            'warnings': warnings,
            'engine': 'paddleocr-ppocrv5',
            'device': self.engine.device,
            'elapsed_ms': round((perf_counter()-begin)*1000),
        }
