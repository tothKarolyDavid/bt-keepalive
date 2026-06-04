from btkeepalive.app import Application


def test_second_instance_exits_without_starting(monkeypatch):
    monkeypatch.setattr("btkeepalive.app.acquire", lambda: False)
    assert Application().run() == 0
