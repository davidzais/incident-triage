from datetime import datetime

from pydantic import BaseModel, ConfigDict
from enum import StrEnum 

# this is a ranking of the service tiers, lower number = higher priority
SERVICE_TIER = {"checkout": 1, "payments": 1, "inventory": 2}
DEFAULT_TIER = 3

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
    
class Priority(StrEnum):
    P1 = "P1" #Highest priority
    P2 = "P2"
    P3 = "P3"
    P4 = "P4" #lowest priority


class AlertState(StrEnum):
    FIRING = "firing"
    RESOLVED = "resolved"   



class Incident(BaseModel):
    severity: Severity
    service: str
    fingerprint: str
    title: str
    status: AlertState
    priority: Priority

class IncidentRead(BaseModel):
    # this allows the model to be loaded from the database ORM object directly, 
    # without manuually mapping each field. It uses the attribute names of the ORM object to populate
    # the model fields. that way if a field gets added to the ORM object, it will automatically be 
    # included in the model without needing to update the model code.
    model_config = ConfigDict(from_attributes=True) 

    severity: Severity
    service: str
    fingerprint: str
    title: str
    status: AlertState
    times_seen: int = 1
    last_seen: datetime
    first_seen: datetime
    progress_status: str
    priority: Priority
      

PRIORITY_MATRIX = {
    # this is a mapping of (severity, service tier) to priority
    (Severity.CRITICAL, 1): Priority.P1,
    (Severity.CRITICAL, 2): Priority.P1,
    (Severity.CRITICAL, 3): Priority.P2,
    (Severity.WARNING,  1): Priority.P2,
    (Severity.WARNING,  2): Priority.P3,
    (Severity.WARNING,  3): Priority.P3,
    (Severity.INFO,     1): Priority.P4,
    (Severity.INFO,     2): Priority.P4,
    (Severity.INFO,     3): Priority.P4,
}

def prioritize(severity: Severity, service: str) -> Priority:
    tier = SERVICE_TIER.get(service, DEFAULT_TIER)
    return PRIORITY_MATRIX.get((severity, tier), Priority.P3)  # default if unlisted   
