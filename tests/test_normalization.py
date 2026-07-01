from models.providers.alert_manager import Payload
from models.incident import Severity
import pytest

def test_to_incident(sample_message):
    payload: Payload = Payload.model_validate(sample_message)
    incident = payload.to_incident()    
    
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
   