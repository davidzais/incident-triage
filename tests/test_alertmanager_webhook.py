from fastapi.testclient import TestClient
from models.incident import Incident
import pytest
from app.main import api
from pathlib import Path
import json

client = TestClient( api)
test_data_file = "fixtures/alertmanager_firing.json"

@pytest.fixture
def sample_message():
    file_path = Path(__file__).parent / test_data_file
    
    with open( file_path) as f:
        json_data = json.load( f)
    
    return dict(json_data)

def test_webook(sample_message):
    response = client.post("/webhooks/alertmanager/", json=sample_message)
    assert response.status_code == 202, response.json()
    incident = response.json()
       
    assert incident["fingerprint"] == "a1b2c3d4e5f60718"
    assert incident["severity"]  == "critical"
    assert incident["service"]  == "checkout"
    assert incident["title"]  == "Error rate above 5% on checkout"
    