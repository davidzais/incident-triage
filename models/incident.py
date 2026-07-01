from typing_extensions import Literal

from pydantic import BaseModel
from enum import StrEnum 

class Severity(StrEnum):
    CRITICAL = "critical"
    WARNING  = "warning"
    INFO     = "info"
    UNKNOWN  = "unknown"

    @classmethod
    def from_raw(cls, raw_val) -> "Severity":
        if not raw_val:
            return cls.UNKNOWN

        return cls(raw_val.strip().lower())
    
    @classmethod
    def _missing_(cls, value) -> "Severity":
        return cls.UNKNOWN
    

class Incident(BaseModel):
    severity: Severity
    service: str
    fingerprint: str
    title: str