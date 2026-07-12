from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def success_response(data: Any, meta: Any = None, status_code: int = 200) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=jsonable_encoder({"data": data, "meta": meta}))


def error_response(status_code: int, title: str, detail: str, error_type: str = "about:blank") -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"type": error_type, "title": title, "status": status_code, "detail": detail}, "meta": None},
    )
