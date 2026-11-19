import os

# Hanya untuk import ASGI pada unit test; bukan token deployment.
os.environ.setdefault('BASAI_OCR_TOKEN', 'local-test-token-is-not-for-production-0123456789')
