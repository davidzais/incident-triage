from models.providers.alert_manager import Payload
from models.incident import AlertState, Severity, Incident, prioritize, Priority
import pytest

def test_to_incident(sample_message):
    payload: Payload = Payload.model_validate(sample_message)
    incident = payload.to_incidents()
    incident = incident[0]

    assert incident.fingerprint == "a1b2c3d4e5f60718"
    assert incident.severity  == Severity.CRITICAL
    assert incident.service  == "checkout"
    assert incident.title  == "Error rate above 5% on checkout"
    assert incident.priority == Priority.P1

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
    assert incident.status  == AlertState.FIRING
    assert incident.priority == Priority.P1

    incident2: Incident = incidents[1]
    assert incident2.fingerprint == "f6e5d4c3b2a10718"
    assert incident2.severity  == Severity.WARNING
    assert incident2.service  == "inventory"
    assert incident2.title  == "Error rate above 8% on orders"
    assert incident2.status  == AlertState.FIRING

    assert Payload(alerts=[]).to_incidents() == []

@pytest.mark.parametrize(argnames="severity, service, expected", argvalues=[
    (Severity.CRITICAL, "checkout", Priority.P1),
    (Severity.CRITICAL, "inventory", Priority.P1),
    (Severity.WARNING, "returns", Priority.P3),
    (Severity.INFO, "orders", Priority.P4),
    (Severity.UNKNOWN, "checkout", Priority.P3),
    (Severity.UNKNOWN, "unknown_service", Priority.P3),
    (Severity.CRITICAL, "unknown_service", Priority.P2)
])
def test_prioritize(severity, service, expected):
    # Test known severity and service
    assert prioritize(severity=severity, service=service) == expected
    
