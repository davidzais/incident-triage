from fastapi.testclient import TestClient
from models.providers.alert_manager import Payload
from models.incident import AlertState, Incident, Severity
from app.main import api


client = TestClient( api)

def test_webook(sample_message):
    response = client.post("/webhooks/alertmanager/", json=sample_message)
    assert response.status_code == 202, response.json()
    incidents: list[Incident] = response.json()
    assert len(incidents) == 1

    incident = incidents[0]   
    assert incident["fingerprint"] == "a1b2c3d4e5f60718"
    assert incident["severity"]  == Severity.CRITICAL
    assert incident["service"]  == "checkout"
    assert incident["title"]  == "Error rate above 5% on checkout"
    assert incident["status"]  == AlertState.FIRING
    
