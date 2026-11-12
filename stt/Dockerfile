FROM nvidia/cuda:12.9.1-cudnn-runtime-ubuntu24.04
ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    HF_HOME=/models/hf NVIDIA_VISIBLE_DEVICES=all NVIDIA_DRIVER_CAPABILITIES=compute,utility
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv python3-pip ffmpeg ca-certificates && \
    rm -rf /var/lib/apt/lists/* && useradd --uid 10001 --create-home --shell /usr/sbin/nologin basai && \
    mkdir -p /models && chown -R basai:basai /models
WORKDIR /app
COPY requirements.txt ./
RUN python3 -m venv /venv && /venv/bin/pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
USER 10001:10001
ENV PATH=/venv/bin:$PATH
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log"]
