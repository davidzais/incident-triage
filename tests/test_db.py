from fastapi.testclient import TestClient
from app.main import api
from models.incident import IncidentRead


client = TestClient( app=api)
  
def test_incidents_ranked_by_priority(test_db, test_data_json):   
    #POST a known payload with mixed severities/services
    response = client.post("/webhooks/alertmanager/", json=test_data_json)
    assert response.status_code == 202, response.json()


    # get all the incidents from the posts and make sure they come back with the correct priorities
    # in descending order (P1 before P2 before P3)
    response = client.get("/incidents")
    assert response.status_code == 200, response.json()
    
    incidents: list[IncidentRead] = response.json()
    expected_priorities = ["P1", "P1", "P2", "P2", "P3", "P4"]
    priorities = [incident["priority"] for incident in incidents]
    assert priorities == expected_priorities, f"Expected priorities {expected_priorities}, but got {priorities}"

  
