from io import BytesIO

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from app.config import Settings
from app.engine import OcrLine
from app.main import create_app


class FakeEngine:
    device = 'fake-test'
    def startup(self):
        pass
    def recognize(self, _image):
        return [OcrLine('NIK: 3171234567890123', .99), OcrLine('Nama: MIRA SETIAWAN', .92)]


def png_bytes() -> bytes:
    buffer = BytesIO()
    Image.new('RGB', (1000, 600), 'white').save(buffer, format='PNG')
    return buffer.getvalue()


def test_auth_and_live_and_ocr():
    app = create_app(Settings(token='x'*40, enable_gpu=False), FakeEngine())
    with TestClient(app) as client:
        assert client.get('/health/live').status_code == 200
        assert client.get('/health/ready').status_code == 401
        assert client.post('/v1/ktp/ocr', files={'image': ('test.png', png_bytes(), 'image/png')}).status_code == 401
        response = client.post('/v1/ktp/ocr', files={'image': ('test.png', png_bytes(), 'image/png')}, headers={'Authorization': 'Bearer '+'x'*40})
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'OCR_REVIEW'
        assert data['fields']['nama'] == 'MIRA SETIAWAN'
        assert data['review_required'] is True
        assert data['device'] == 'fake-test'
        assert data['required_complete'] is False
        assert data['missing_fields'] == [
            'tempat_lahir', 'tanggal_lahir', 'alamat', 'agama', 'pekerjaan',
        ]


def test_invalid_payload_rejected_before_ocr():
    app = create_app(Settings(token='x'*40, enable_gpu=False), FakeEngine())
    with TestClient(app) as client:
        response = client.post('/v1/ktp/ocr', files={'image': ('bad.jpg', b'not a jpeg', 'image/jpeg')}, headers={'Authorization': 'Bearer '+'x'*40})
        assert response.status_code == 422
        response = client.post('/v1/ktp/ocr', files={'image': ('bad.txt', b'test', 'text/plain')}, headers={'Authorization': 'Bearer '+'x'*40})
        assert response.status_code == 415
