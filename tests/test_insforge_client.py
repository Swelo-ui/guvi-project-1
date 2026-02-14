from utils import insforge_client


class FakeResponse:
    def __init__(self, status_code, data=None, text=""):
        self.status_code = status_code
        self._data = data or []
        self.text = text

    def json(self):
        return self._data


def test_get_headers_includes_auth_key(monkeypatch):
    monkeypatch.setattr(insforge_client, "INSFORGE_KEY", "test_key")
    headers = insforge_client.get_headers()
    assert headers["Authorization"] == "Bearer test_key"


def test_get_persona_returns_none_when_not_configured(monkeypatch):
    monkeypatch.setattr(insforge_client, "REST_URL", "")
    assert insforge_client.get_persona("s1") is None


def test_save_persona_success(monkeypatch):
    monkeypatch.setattr(insforge_client, "REST_URL", "https://example.insforge.app/api/database/records")

    def fake_post(url, headers, json, timeout):
        return FakeResponse(201)

    monkeypatch.setattr(insforge_client.httpx, "post", fake_post)
    saved = insforge_client.save_persona("s1", {"name": "Asha", "bank": {"name": "SBI"}, "upi": {"primary": "a@upi"}})
    assert saved is True


def test_save_intelligence_updates_existing(monkeypatch):
    monkeypatch.setattr(insforge_client, "REST_URL", "https://example.insforge.app/api/database/records")

    def fake_get(url, headers, timeout):
        return FakeResponse(200, [{"id": 10}])

    def fake_patch(url, headers, json, timeout):
        return FakeResponse(204)

    monkeypatch.setattr(insforge_client.httpx, "get", fake_get)
    monkeypatch.setattr(insforge_client.httpx, "patch", fake_patch)
    ok = insforge_client.save_intelligence("s1", {"upi_ids": ["a@upi"]}, agent_notes="test")
    assert ok is True


def test_save_intelligence_inserts_new(monkeypatch):
    monkeypatch.setattr(insforge_client, "REST_URL", "https://example.insforge.app/api/database/records")

    def fake_get(url, headers, timeout):
        return FakeResponse(200, [])

    def fake_post(url, headers, json, timeout):
        return FakeResponse(201)

    monkeypatch.setattr(insforge_client.httpx, "get", fake_get)
    monkeypatch.setattr(insforge_client.httpx, "post", fake_post)
    ok = insforge_client.save_intelligence("s2", {"bank_accounts": ["1234567890"]}, agent_notes="test")
    assert ok is True


def test_mark_callback_sent(monkeypatch):
    monkeypatch.setattr(insforge_client, "REST_URL", "https://example.insforge.app/api/database/records")

    def fake_patch(url, headers, json, timeout):
        return FakeResponse(200)

    monkeypatch.setattr(insforge_client.httpx, "patch", fake_patch)
    assert insforge_client.mark_callback_sent("s1") is True


def test_save_message_success(monkeypatch):
    monkeypatch.setattr(insforge_client, "REST_URL", "https://example.insforge.app/api/database/records")

    def fake_post(url, headers, json, timeout):
        return FakeResponse(201)

    monkeypatch.setattr(insforge_client.httpx, "post", fake_post)
    assert insforge_client.save_message("s1", "scammer", "hello") is True
