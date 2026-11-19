from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class OcrLine:
    text: str
    confidence: float
    box: tuple[int, int, int, int] | None = None


class OcrEngine(Protocol):
    def startup(self) -> None: ...
    def recognize(self, image: np.ndarray) -> list[OcrLine]: ...
    @property
    def device(self) -> str: ...


class PaddleEngine:
    def __init__(self, require_gpu: bool = True):
        self._pipeline = None
        self._require_gpu = require_gpu
        self._device = 'uninitialized'

    @property
    def device(self) -> str:
        return self._device

    def startup(self) -> None:
        import paddle
        from paddleocr import PaddleOCR

        if self._require_gpu and (not paddle.is_compiled_with_cuda() or not paddle.device.cuda.device_count()):
            raise RuntimeError('PaddlePaddle GPU tidak dapat mengakses CUDA. Stop, jangan fallback diam-diam.')
        self._device = 'gpu:0' if self._require_gpu else 'cpu'
        self._pipeline = PaddleOCR(
            lang='id',
            ocr_version='PP-OCRv5',
            device=self._device,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            text_rec_score_thresh=0.0,
        )

    def recognize(self, image: np.ndarray) -> list[OcrLine]:
        if self._pipeline is None:
            raise RuntimeError('Engine belum dimuat.')
        predictions = self._pipeline.predict(image)
        lines: list[OcrLine] = []
        for item in predictions:
            payload = item.json
            payload = payload.get('res', payload)
            texts = payload.get('rec_texts', [])
            scores = payload.get('rec_scores', [])
            boxes = payload.get('rec_boxes', [])
            for idx, text in enumerate(texts):
                content = str(text).strip()
                if not content:
                    continue
                raw_box = boxes[idx] if idx < len(boxes) else None
                box = None
                if raw_box is not None and len(raw_box) == 4:
                    box = tuple(int(v) for v in raw_box)
                score = float(scores[idx]) if idx < len(scores) else 0.0
                lines.append(OcrLine(content, max(0.0, min(1.0, score)), box))
        return lines


def assemble_rows(lines: list[OcrLine]) -> list[OcrLine]:
    boxed = [line for line in lines if line.box]
    non_boxed = [line for line in lines if not line.box]
    boxed.sort(key=lambda item: (item.box[1] + item.box[3]) / 2)
    grouped: list[list[OcrLine]] = []
    for line in boxed:
        mid = (line.box[1] + line.box[3]) / 2
        height = max(1, line.box[3] - line.box[1])
        if grouped:
            prev = grouped[-1]
            prev_mid = sum((p.box[1]+p.box[3])/2 for p in prev) / len(prev)
            prev_h = sum(max(1, p.box[3]-p.box[1]) for p in prev) / len(prev)
            if abs(mid-prev_mid) <= max(8, min(height, prev_h) * .52):
                prev.append(line)
                continue
        grouped.append([line])
    rows: list[OcrLine] = []
    for group in grouped:
        group.sort(key=lambda item: item.box[0])
        rows.append(OcrLine(' '.join(x.text for x in group),
                            min(x.confidence for x in group)))
    return rows + non_boxed
