from hmac import compare_digest
from fastapi import HTTPException, Request, status


def authenticate(request: Request) -> None:
    actual = request.headers.get("X-BASAI-Key", "")
    expected = request.app.state.settings.api_key
    if not actual or not compare_digest(actual, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
