#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python - <<'PY'
from PIL import Image, ImageDraw
im=Image.new('RGB',(1200,700),'#DCECEF')
d=ImageDraw.Draw(im)
d.text((100,70),'PROVINSI CONTOH',fill='black',stroke_width=1)
d.text((100,200),'NIK : 1234567890123456',fill='black',stroke_width=1)
d.text((100,270),'Nama : SAKSI SINTETIS',fill='black',stroke_width=1)
im.save('/tmp/basai-ocr-smoke.png')
PY
set -a
source .env
set +a
curl -fsS --max-time 90 -H "Authorization: Bearer $BASAI_OCR_TOKEN" \
  -F 'image=@/tmp/basai-ocr-smoke.png;type=image/png' \
  http://127.0.0.1:18069/v1/ktp/ocr \
  | python -c 'import json,sys; d=json.load(sys.stdin); print("STATUS",d.get("status"),"ENGINE",d.get("engine"),"DEVICE",d.get("device"),"FIELD_COUNT",len(d.get("fields",{})))'
rm -f /tmp/basai-ocr-smoke.png
