# AI Chat endpoint tests: POST /api/ai/chat
import pytest

ENDPOINT = '/api/ai/chat'


def _post(client, base_url, payload):
    return client.post(f"{base_url}{ENDPOINT}", json=payload, timeout=90)


def test_empty_messages_returns_400(api_client, base_url):
    r = _post(api_client, base_url, {'messages': [], 'lang': 'en'})
    assert r.status_code == 400
    assert 'detail' in r.json()


def test_chat_en_returns_non_empty_reply(api_client, base_url):
    payload = {
        'messages': [
            {'role': 'user', 'content': 'I got an SMS saying I won a prize and must click a link. Is this a scam?'}
        ],
        'lang': 'en',
    }
    r = _post(api_client, base_url, payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert 'reply' in data
    assert isinstance(data['reply'], str)
    assert len(data['reply'].strip()) > 10


def test_chat_ru_returns_russian_reply(api_client, base_url):
    payload = {
        'messages': [
            {'role': 'user', 'content': 'Мне пришло сообщение о выигрыше приза с ссылкой. Это мошенничество?'}
        ],
        'lang': 'ru',
    }
    r = _post(api_client, base_url, payload)
    assert r.status_code == 200, r.text
    reply = r.json().get('reply', '')
    assert len(reply.strip()) > 10
    # Expect Cyrillic characters for Russian
    assert any('\u0400' <= ch <= '\u04FF' for ch in reply), f'Reply not in Cyrillic: {reply[:200]}'


def test_chat_tg_returns_cyrillic_reply(api_client, base_url):
    payload = {
        'messages': [
            {'role': 'user', 'content': 'Ба ман паём омад, ки ҷоизаро бурдам. Ин фиреб аст?'}
        ],
        'lang': 'tg',
    }
    r = _post(api_client, base_url, payload)
    assert r.status_code == 200, r.text
    reply = r.json().get('reply', '')
    assert len(reply.strip()) > 10
    assert any('\u0400' <= ch <= '\u04FF' for ch in reply), f'Reply not in Cyrillic: {reply[:200]}'


def test_multi_turn_context(api_client, base_url):
    payload = {
        'session_id': 'TEST_multi_turn_session',
        'messages': [
            {'role': 'user', 'content': 'My name is Ali. Remember it.'},
            {'role': 'assistant', 'content': 'Okay Ali, noted.'},
            {'role': 'user', 'content': 'What is my name?'},
        ],
        'lang': 'en',
    }
    r = _post(api_client, base_url, payload)
    assert r.status_code == 200, r.text
    reply = r.json().get('reply', '').lower()
    assert 'ali' in reply, f'Expected name in reply, got: {reply[:300]}'


def test_missing_messages_field_returns_422(api_client, base_url):
    r = _post(api_client, base_url, {'lang': 'en'})
    # FastAPI returns 422 for pydantic validation errors
    assert r.status_code in (400, 422)
