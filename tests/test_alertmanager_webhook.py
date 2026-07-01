from fastapi.testclient import TestClient
from models.incident import Incident
from app.main import api


client = TestClient( api)

def test_webook(sample_message):
    response = client.post("/webhooks/alertmanager/", json=sample_message)
    assert response.status_code == 202, response.json()
    incident = response.json()
       
    assert incident["fingerprint"] == "a1b2c3d4e5f60718"
    assert incident["severity"]  == "critical"
    assert incident["service"]  == "checkout"
    assert incident["title"]  == "Error rate above 5% on checkout"
    