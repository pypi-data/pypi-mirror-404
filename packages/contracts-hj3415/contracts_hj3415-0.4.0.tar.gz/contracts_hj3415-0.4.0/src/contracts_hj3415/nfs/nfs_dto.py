# contracts_hj3415/nfs/nfs_dto.py
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict
from .types import Endpoints, Payload


class NfsDTO(BaseModel):
    code: str
    asof: datetime
    endpoint: Endpoints
    payload: Payload

    model_config = ConfigDict(extra="ignore")


