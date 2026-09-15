from typing import Literal

from pydantic import BaseModel


class OkResponse(BaseModel):
    ok: bool = True


class ErrorResponse(BaseModel):
    detail: str


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "sentinelrag"
    env: str
    phase: Literal["1"] = "1"
