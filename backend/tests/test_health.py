# Health check for SCAM.TJ backend

def test_health_ok(api_client, base_url):
    r = api_client.get(f"{base_url}/api/health", timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get('status') == 'ok'
    assert data.get('ai_configured') is True


def test_root(api_client, base_url):
    r = api_client.get(f"{base_url}/api/", timeout=15)
    assert r.status_code == 200
    assert 'message' in r.json()
