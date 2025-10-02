"""Common response schemas."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Service status")
    service: str = Field(default="qeem-backend", description="Service name")
