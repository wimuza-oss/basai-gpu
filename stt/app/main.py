from fastapi import FastAPI
from threading import Lock

from app.api.routes import router
from app.core.config import Settings
from app.services.stt import FasterWhisperService, STTServiceProtocol


def create_app(settings: Settings | None = None,
               stt: STTServiceProtocol | None = None) -> FastAPI:
    settings = settings if settings is not None else Settings.from_env()
    app = FastAPI(title="BAS-AI STT Pilot", version="6.6.0",
                  docs_url=None, redoc_url=None, openapi_url=None)
    app.state.settings = settings
    app.state.stt = stt if stt is not None else FasterWhisperService(settings)
    app.state.gpu_lock = Lock()
    app.include_router(router)
    return app


app = create_app()
