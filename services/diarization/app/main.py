from __future__ import annotations

import logging
import os
import secrets
import tempfile
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import torch
from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from pyannote.audio import Pipeline
from starlette.concurrency import run_in_threadpool

LOGGER = logging.getLogger("basai.diarization")

MODEL_PATH = Path(
    os.getenv("BASAI_DIARIZATION_MODEL_PATH", "/models/community-1")
).resolve()

API_KEY = os.getenv("BASAI_DIARIZATION_API_KEY", "")

MAX_UPLOAD_BYTES = int(
    os.getenv("BASAI_DIARIZATION_MAX_UPLOAD_BYTES", "2147483648")
)

ALLOWED_SPEAKERS = range(1, 9)


class Runtime:
    pipeline: Pipeline | None = None
    inference_lock = threading.Lock()


runtime = Runtime()


def _validate_runtime_config() -> None:
    if len(API_KEY) < 32:
        raise RuntimeError(
            "BASAI_DIARIZATION_API_KEY must contain at least 32 characters."
        )

    if MAX_UPLOAD_BYTES <= 44:
        raise RuntimeError(
            "BASAI_DIARIZATION_MAX_UPLOAD_BYTES is invalid."
        )

    if not MODEL_PATH.is_dir():
        raise RuntimeError(
            f"Diarization model directory does not exist: {MODEL_PATH}"
        )

    if not (MODEL_PATH / "config.yaml").is_file():
        raise RuntimeError(
            f"Diarization model config.yaml is missing: {MODEL_PATH}"
        )

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available to diarization service.")


@asynccontextmanager
async def lifespan(_: FastAPI):
    _validate_runtime_config()

    pipeline = Pipeline.from_pretrained(str(MODEL_PATH))
    pipeline.to(torch.device("cuda"))

    runtime.pipeline = pipeline

    LOGGER.info(
        "Diarization model loaded on CUDA: %s",
        torch.cuda.get_device_name(0),
    )

    try:
        yield
    finally:
        runtime.pipeline = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


app = FastAPI(
    title="BAS-AI Speaker Diarization",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)


def _authorized(value: str | None) -> bool:
    return (
        value is not None
        and len(value) >= 32
        and secrets.compare_digest(value, API_KEY)
    )


def _validate_speaker_constraints(
    num_speakers: int | None,
    min_speakers: int | None,
    max_speakers: int | None,
) -> None:
    values = {
        "num_speakers": num_speakers,
        "min_speakers": min_speakers,
        "max_speakers": max_speakers,
    }

    for name, value in values.items():
        if value is not None and value not in ALLOWED_SPEAKERS:
            raise HTTPException(
                status_code=422,
                detail=f"{name} must be between 1 and 8.",
            )

    if num_speakers is not None and (
        min_speakers is not None or max_speakers is not None
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "Use num_speakers or min_speakers/max_speakers, not both."
            ),
        )

    if (
        min_speakers is not None
        and max_speakers is not None
        and min_speakers > max_speakers
    ):
        raise HTTPException(
            status_code=422,
            detail="min_speakers cannot exceed max_speakers.",
        )


async def _store_upload(file: UploadFile) -> Path:
    suffix = ".wav"

    descriptor, temp_name = tempfile.mkstemp(
        prefix="basai-diar-",
        suffix=suffix,
        dir="/tmp",
    )
    os.close(descriptor)

    path = Path(temp_name)
    total = 0

    try:
        with path.open("wb") as destination:
            while True:
                chunk = await file.read(1024 * 1024)

                if not chunk:
                    break

                total += len(chunk)

                if total > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail="Audio file is too large.",
                    )

                destination.write(chunk)

        if total <= 44:
            raise HTTPException(
                status_code=422,
                detail="WAV payload is empty or invalid.",
            )

        with path.open("rb") as source:
            header = source.read(12)

        if not (
            len(header) == 12
            and header[0:4] == b"RIFF"
            and header[8:12] == b"WAVE"
        ):
            raise HTTPException(
                status_code=415,
                detail="Only canonical RIFF/WAVE input is accepted.",
            )

        return path

    except Exception:
        path.unlink(missing_ok=True)
        raise


def _annotation_segments(annotation: Any) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []

    for turn, _, speaker in annotation.itertracks(yield_label=True):
        segments.append(
            {
                "speaker_id": str(speaker),
                "start_ms": int(round(float(turn.start) * 1000)),
                "end_ms": int(round(float(turn.end) * 1000)),
            }
        )

    segments.sort(
        key=lambda item: (
            item["start_ms"],
            item["end_ms"],
            item["speaker_id"],
        )
    )

    return segments


def _run_diarization(
    path: Path,
    num_speakers: int | None,
    min_speakers: int | None,
    max_speakers: int | None,
) -> dict[str, Any]:
    pipeline = runtime.pipeline

    if pipeline is None:
        raise RuntimeError("Diarization model is not loaded.")

    options: dict[str, int] = {}

    if num_speakers is not None:
        options["num_speakers"] = num_speakers
    else:
        if min_speakers is not None:
            options["min_speakers"] = min_speakers

        if max_speakers is not None:
            options["max_speakers"] = max_speakers

    with runtime.inference_lock:
        started = time.perf_counter()

        with torch.inference_mode():
            output = pipeline(str(path), **options)

        processing_seconds = round(
            time.perf_counter() - started,
            3,
        )

    regular = output.speaker_diarization
    exclusive = getattr(
        output,
        "exclusive_speaker_diarization",
        None,
    )

    if exclusive is None:
        exclusive = regular

    segments = _annotation_segments(exclusive)
    speaker_activity = _annotation_segments(regular)

    speakers = sorted(
        {
            item["speaker_id"]
            for item in speaker_activity
        }
    )

    return {
        "status": "ok",
        "engine": "pyannote-community-1",
        "device": "cuda",
        "mode": "exclusive",
        "speaker_count": len(speakers),
        "speakers": speakers,
        "processing_seconds": processing_seconds,
        "segments": segments,
        "speaker_activity": speaker_activity,
    }


@app.get("/health/live")
def health_live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
def health_ready() -> dict[str, Any]:
    if runtime.pipeline is None:
        raise HTTPException(
            status_code=503,
            detail="Diarization model is not loaded.",
        )

    if not torch.cuda.is_available():
        raise HTTPException(
            status_code=503,
            detail="CUDA is not available.",
        )

    return {
        "status": "cuda_available",
        "model_loaded": True,
        "model": "community-1",
        "device": "cuda",
        "cuda_device": torch.cuda.get_device_name(0),
    }


@app.post("/v1/diarize")
async def diarize(
    file: UploadFile = File(...),
    num_speakers: int | None = Form(default=None),
    min_speakers: int | None = Form(default=None),
    max_speakers: int | None = Form(default=None),
    x_basai_key: str | None = Header(
        default=None,
        alias="X-BASAI-Key",
    ),
) -> dict[str, Any]:
    if not _authorized(x_basai_key):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized.",
        )

    _validate_speaker_constraints(
        num_speakers,
        min_speakers,
        max_speakers,
    )

    path = await _store_upload(file)

    try:
        return await run_in_threadpool(
            _run_diarization,
            path,
            num_speakers,
            min_speakers,
            max_speakers,
        )
    except HTTPException:
        raise
    except Exception:
        LOGGER.exception("Speaker diarization failed.")
        raise HTTPException(
            status_code=500,
            detail="Speaker diarization failed.",
        ) from None
    finally:
        path.unlink(missing_ok=True)
        await file.close()
