from typing import Any

import pytest

from pathlib import Path
import json



test_data_file = "fixtures/alertmanager_firing.json"
test_multi_file = "fixtures/alertmanager_multi.json"

@pytest.fixture
def sample_message() -> dict[Any, Any]:
    file_path = Path(__file__).parent / test_data_file
    
    with open( file_path) as f:
        json_data = json.load( f)
           
    return dict(json_data)

@pytest.fixture
def sample_multi_message() -> dict[Any, Any]:
    file_path = Path(__file__).parent / test_multi_file
    
    with open( file_path) as f:
        json_data = json.load( f)
           
    return dict(json_data)