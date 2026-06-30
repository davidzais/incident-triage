from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from datetime import datetime
from models.incident import Incident


class ConfigBase(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
   
class Annotations(ConfigBase):
    summary: str
    description: str

class Label(ConfigBase):
    alertname: str
    service: str
    severity: str
    namespace: str
    instance: str

class Alert(ConfigBase):
    status: str
    labels: Label
    annotations: Annotations
    starts_at: datetime 
    ends_at: datetime
    generator_url: str = Field(validation_alias="generatorURL")
    fingerprint: str

class Payload(ConfigBase):
    alerts: list[Alert]

    def to_incident(self) -> Incident:
        alert = self.alerts[0]
        incident: Incident = Incident(
            fingerprint = alert.fingerprint,
            severity = alert.labels.severity,
            service = alert.labels.service,
            title = alert.annotations.summary
        )

        return incident