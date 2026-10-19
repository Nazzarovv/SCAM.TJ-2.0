import os
import pytest
import requests

BASE_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL') or 'https://fraud-detector-138.preview.emergentagent.com'
BASE_URL = BASE_URL.rstrip('/')

@pytest.fixture(scope='session')
def base_url():
    return BASE_URL

@pytest.fixture
def api_client():
    s = requests.Session()
    s.headers.update({'Content-Type': 'application/json'})
    return s
