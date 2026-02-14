"""
Get Results Script Tests
Validates InsForge fetch logic without external calls or file writes.
"""

import importlib.util
import sys
import types
import io
import builtins


class FakeResponse:
    def __init__(self, status_code, data=None, text=""):
        self.status_code = status_code
        self._data = data or []
        self.text = text

    def json(self):
        return self._data


def test_get_results_script_success(monkeypatch):
    """Reality check: script fetches intelligence and conversations using REST."""
    calls = []

    def fake_get(url, headers, timeout):
        calls.append(url)
        if "intelligence" in url:
            return FakeResponse(200, [{"id": 1}])
        return FakeResponse(200, [{"id": 2}])

    fake_requests = types.SimpleNamespace(get=fake_get)
    fake_files = {}

    real_open = builtins.open
    source_path = "h:\\guvi project\\get_results.py"

    def fake_open(name, mode="r", encoding=None):
        if name == source_path and "r" in mode:
            return real_open(name, mode, encoding=encoding)
        buffer = io.StringIO()
        fake_files[name] = buffer
        return buffer

    monkeypatch.setitem(sys.modules, "requests", fake_requests)
    monkeypatch.setattr(builtins, "open", fake_open)

    spec = importlib.util.spec_from_file_location("get_results_test", source_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert any("intelligence" in url for url in calls)
    assert any("conversations" in url for url in calls)
    assert "guvi_intelligence.json" in fake_files
    assert "guvi_conversations.json" in fake_files
