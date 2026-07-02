from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from datetime import datetime
from models.incident import AlertState, Incident, Severity


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
    status: AlertState
    labels: Label
    annotations: Annotations
    starts_at: datetime 
    ends_at: datetime
    generator_url: str = Field(validation_alias="generatorURL")
    fingerprint: str

class Payload(ConfigBase):
    alerts: list[Alert]

    
    def to_incidents(self) -> list[Incident]:
        incidents: list[Incident] = []
        alerts = self.alerts
        for alert in alerts:
            incident: Incident = Incident(
                fingerprint = alert.fingerprint,
                severity = Severity.from_raw(alert.labels.severity),
                service = alert.labels.service,
                title = alert.annotations.summary,
                status = alert.status
            )
            incidents.append(incident)

        return incidents