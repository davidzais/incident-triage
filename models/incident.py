from pydantic import BaseModel


class Incident(BaseModel):
    severity: str
    service: str
    fingerprint: str
    title: str