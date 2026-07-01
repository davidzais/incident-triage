from models.providers.alert_manager import Payload
from models.incident import Severity, Incident
import pytest

def test_to_incident(sample_message):
    payload: Payload = Payload.model_validate(sample_message)
    incident = payload.to_incidents()
    incident = incident[0]

    assert incident.fingerprint == "a1b2c3d4e5f60718"
    assert incident.severity  == Severity.CRITICAL
    assert incident.service  == "checkout"
    assert incident.title  == "Error rate above 5% on checkout"

@pytest.mark.parametrize("value, expected", [
    ("critical", Severity.CRITICAL),
    ("", Severity.UNKNOWN),
    (None, Severity.UNKNOWN),
    ("  warning  ", Severity.WARNING),
    ("INFO", Severity.INFO),
    ("unknown", Severity.UNKNOWN),
    ("invalid", Severity.UNKNOWN),
])
def test_severity_from_raw(value, expected):
    assert Severity.from_raw(value) == expected


def test_multi_incidents(sample_multi_message):
    payload: Payload = Payload.model_validate(sample_multi_message)
    
    incidents: list[Incident] = payload.to_incidents()
    assert len(incidents) == 2
    incidents: list[Incident] = payload.to_incidents()
    assert len(incidents) == 2
 
    incident: Incident = incidents[0]   
    assert incident.fingerprint == "a1b2c3d4e5f60718"
    assert incident.severity  == Severity.CRITICAL
    assert incident.service  == "checkout"
    assert incident.title  == "Error rate above 5% on checkout"

    incident2: Incident = incidents[1]
    assert incident2.fingerprint == "f6e5d4c3b2a10718"
    assert incident2.severity  == Severity.WARNING
    assert incident2.service  == "inventory"
    assert incident2.title  == "Error rate above 8% on orders"

    assert Payload(alerts=[]).to_incidents() == []