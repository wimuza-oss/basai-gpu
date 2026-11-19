import numpy as np

from app.config import Settings
from app.engine import PaddleEngine


def main() -> None:
    engine = PaddleEngine(require_gpu=Settings.from_env().enable_gpu)
    engine.startup()
    # Synthetic white image: model download/warmup only. No real KTP.
    image = np.full((600, 1000, 3), 255, dtype=np.uint8)
    engine.recognize(image)
    print('WARMUP_OK device=' + engine.device)


if __name__ == '__main__':
    main()
