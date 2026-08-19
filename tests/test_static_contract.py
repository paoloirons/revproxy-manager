from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_compose_ports_and_isolation():
    y = (ROOT / "docker-compose.yml").read_text()
    assert "8087" in y and "8080" in y and "./data:/data:ro" in y


def test_upstream_not_vendored():
    assert not (ROOT / "runtime" / "revproxy").exists()
    req = (ROOT / "runtime" / "requirements.txt").read_text()
    assert "django-revproxy==0.13.0" in req


def test_runtime_dynamic_view():
    s = (ROOT / "runtime" / "runtime_app" / "views.py").read_text()
    assert "from revproxy.views import ProxyView" in s
    assert "self.upstream=selected" in s


def test_sqlite_is_readonly_runtime_friendly():
    s = (ROOT / "manager" / "db.py").read_text()
    assert "PRAGMA journal_mode=DELETE" in s
    assert "PRAGMA journal_mode=WAL" not in s
