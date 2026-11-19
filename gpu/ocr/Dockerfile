FROM nvidia/cuda:12.9.1-cudnn-runtime-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PADDLEX_HOME=/models \
    HOME=/models \
    XDG_CACHE_HOME=/models/.cache \
    PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True \
    PATH=/opt/venv/bin:$PATH

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv python3-pip libglib2.0-0 libgl1 libgomp1 ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /opt/venv

# Wheel CUDA 12.9 untuk arsitektur GPU Blackwell (SM120).
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir paddlepaddle-gpu==3.3.0 \
        -i https://www.paddlepaddle.org.cn/packages/stable/cu129/

WORKDIR /srv/ocr
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip check
COPY app/ ./app/
RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin ocr
USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log", "--no-proxy-headers"]
