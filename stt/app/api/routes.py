from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from pathlib import Path
from tempfile import TemporaryDirectory
from hashlib import sha256

from app.core.security import authenticate
from app.services.audio import inspect_wav, AudioValidationError

router = APIRouter()
CHUNK_SIZE = 1024 * 1024


@router.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/health/ready", dependencies=[Depends(authenticate)])
async def ready(request: Request) -> dict[str, str]:
    try:
        gpu_ok = await run_in_threadpool(request.app.state.stt.check_gpu)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="CUDA belum siap") from exc
    if not gpu_ok:
        raise HTTPException(status_code=503, detail="Compute type GPU tidak tersedia")
    return {"status": "cuda_available", "model_loaded": str(getattr(request.app.state.stt, '_model', None) is not None).lower()}


@router.post("/v1/stt/transcribe", dependencies=[Depends(authenticate)])
async def transcribe(request: Request, file: UploadFile = File(...)) -> dict:
    if not file.filename or Path(file.filename).suffix.lower() != ".wav":
        raise HTTPException(status_code=415, detail="Hanya berkas .wav")
    # Ini endpoint sinkron khusus pilot audio <=10 menit. Tahap berikutnya antrean durable.
    lock = request.app.state.gpu_lock
    if not lock.acquire(blocking=False):
        await file.close()
        raise HTTPException(status_code=429, detail="GPU sibuk, coba kembali")
    try:
        with TemporaryDirectory(prefix="basai-upload-") as temp_dir:
            path = Path(temp_dir) / "recording.wav"
            length = 0
            digest = sha256()
            with path.open("wb") as output:
                while True:
                    chunk = await file.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    length += len(chunk)
                    if length > request.app.state.settings.max_upload_mb * 1024 * 1024:
                        raise HTTPException(status_code=413, detail="Berkas terlalu besar")
                    output.write(chunk)
                    digest.update(chunk)
            if length == 0:
                raise HTTPException(status_code=422, detail="Berkas kosong")
            try:
                info = inspect_wav(
                    path, request.app.state.settings.max_audio_seconds,
                    request.app.state.settings.max_channels
                )
            except AudioValidationError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
            try:
                result = await run_in_threadpool(request.app.state.stt.transcribe, path, info)
            except Exception as exc:
                # Detail internal dan isi audio/transkrip tidak dilog/dikembalikan.
                raise HTTPException(status_code=503, detail="Engine STT gagal; pemeriksaan GPU diperlukan") from exc
            result["sha256"] = digest.hexdigest()
            return result
    finally:
        lock.release()
        await file.close()
