from pydantic import BaseModel


class LivenessData(BaseModel):
    status: str


class ReadinessData(BaseModel):
    status: str
    postgres: str
    redis: str
