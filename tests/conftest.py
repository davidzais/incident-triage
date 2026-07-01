import pytest

from pathlib import Path
import json



test_data_file = "fixtures/alertmanager_firing.json"

@pytest.fixture
def sample_message():
    file_path = Path(__file__).parent / test_data_file
    
    with open( file_path) as f:
        json_data = json.load( f)
           
    return dict(json_data)