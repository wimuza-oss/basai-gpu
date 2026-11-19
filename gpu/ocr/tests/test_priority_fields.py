import numpy as np

from app.engine import OcrLine
from app.service import KtpOcrService


class TwoPassEngine:
    device = 'fake-test'

    def __init__(self):
        self.calls = 0

    def recognize(self, _image):
        self.calls += 1
        if self.calls == 1:
            return [
                OcrLine('NIK: 1234567890123456', .96),
                OcrLine('Nama: SAKSI CONTOH', .97),
                OcrLine('Tempat/Tgl Lahir: BANDUNG, 12-05-1980', .94),
            ]
        return [
            OcrLine('Alamat: JL. CONTOH NO. 12', .95),
            OcrLine('Agama: ISLAM', .98),
            OcrLine('Pekerjaan: KARYAWAN SWASTA', .92),
        ]


def test_ocr_merges_seven_priorities_across_two_passes():
    image = np.full((700, 1200, 3), 220, dtype=np.uint8)
    output = KtpOcrService(TwoPassEngine(), max_passes=2).recognize(image)
    assert output['status'] == 'OCR_REVIEW'
    assert output['required_complete'] is True
    assert output['missing_fields'] == []
    assert set(output['required_fields']) == {
        'nik', 'nama', 'tempat_lahir', 'tanggal_lahir', 'alamat', 'agama', 'pekerjaan',
    }
    assert output['fields']['nama'] == 'SAKSI CONTOH'
    assert output['fields']['pekerjaan'] == 'KARYAWAN SWASTA'
    assert output['review_required'] is True
