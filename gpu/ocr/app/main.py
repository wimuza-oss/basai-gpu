from __future__ import annotations

from contextlib import asynccontextmanager
import asyncio
import hmac
import logging

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from app.config import Settings
from app.engine import OcrEngine, PaddleEngine
from app.preprocess import InvalidImage, decode_image
from app.service import KtpOcrService

logger = logging.getLogger('basai.ocr')


class ApiError(BaseModel):
    detail: str


def create_app(settings: Settings | None = None, engine: OcrEngine | None = None) -> FastAPI:
    config = settings or Settings.from_env()
    ocr_engine = engine or PaddleEngine(require_gpu=config.enable_gpu)
    service = KtpOcrService(ocr_engine, max_passes=config.max_ocr_passes)
    gate = asyncio.Semaphore(1)
    state = {'ready': False}

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        await run_in_threadpool(ocr_engine.startup)
        state['ready'] = True
        logger.info('OCR engine ready (device=%s)', ocr_engine.device)
        try:
            yield
        finally:
            state['ready'] = False

    api = FastAPI(
        title='BAS-AI GPU KTP OCR', version='1.0.0',
        docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan,
    )

    def require_token(authorization: str | None = Header(default=None)) -> None:
        token = authorization.partition(' ')[2] if authorization and authorization.startswith('Bearer ') else ''
        if not token or not hmac.compare_digest(token, config.token):
            raise HTTPException(401, 'Token tidak valid.')

    @api.get('/health/live')
    def live() -> dict:
        return {'status': 'alive'}

    @api.get('/health/ready', dependencies=[Depends(require_token)])
    def ready() -> dict:
        if not state['ready']:
            raise HTTPException(503, 'Model belum siap.')
        return {'status': 'ready', 'engine': 'paddleocr-ppocrv5', 'device': ocr_engine.device}

    @api.post('/v1/ktp/ocr', dependencies=[Depends(require_token)], responses={400: {'model': ApiError}})
    async def ktp_ocr(image: UploadFile = File(...)) -> dict:
        if image.content_type not in ('image/jpeg', 'image/png'):
            raise HTTPException(415, 'Hanya JPEG/PNG yang diizinkan.')
        raw = await image.read(config.max_upload_bytes + 1)
        if len(raw) > config.max_upload_bytes:
            raise HTTPException(413, 'Maksimum file 5 MB.')
        try:
            normalized = decode_image(raw, config.max_image_pixels)
        except InvalidImage as exc:
            raise HTTPException(422, str(exc)) from None
        if gate.locked():
            raise HTTPException(429, 'OCR sedang memproses dokumen lain. Coba beberapa saat lagi.')
        async with gate:
            try:
                return await run_in_threadpool(service.recognize, normalized)
            except Exception as exc:
                # Log hanya jenis kegagalan, tanpa payload, NIK, atau RAW OCR.
                logger.error('OCR pipeline failed type=%s', type(exc).__name__)
                raise HTTPException(503, 'OCR tidak dapat memproses gambar saat ini.') from None

    return api


app = create_app()
