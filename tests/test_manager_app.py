import importlib
import pathlib
import sys

from fastapi.testclient import TestClient

ROOT = pathlib.Path(__file__).parents[1]
MANAGER = ROOT / "manager"
if str(MANAGER) not in sys.path:
    sys.path.insert(0, str(MANAGER))


def _load_app(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MANAGER_SECRET", "t" * 48)

    import db
    import security
    import app as app_module

    importlib.reload(db)
    importlib.reload(security)
    app_module = importlib.reload(app_module)
    db.init_db()
    return app_module.app


def test_setup_dashboard_and_route_flow(tmp_path, monkeypatch):
    app = _load_app(tmp_path, monkeypatch)
    with TestClient(app, client=("192.0.2.10", 50000)) as client:
        assert client.get("/healthz").json() == {"ok": True}
        assert client.get("/", follow_redirects=False).headers["location"] == "/setup"

        response = client.post(
            "/setup",
            data={
                "username": "admin",
                "password": "verystrongpass",
                "confirm": "verystrongpass",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/dashboard"

        dashboard = client.get("/dashboard")
        assert dashboard.status_code == 200
        assert "192.0.2.10" in dashboard.text

        import security
        session = security.read_session(client.cookies.get("rpm_session"))
        assert session and session["u"] == "admin"

        response = client.post(
            "/routes/save",
            data={
                "csrf": session["c"],
                "name": "Echo",
                "path_prefix": "/echo/",
                "upstream": "http://127.0.0.1:9000/",
                "enabled": "1",
                "acls": "192.0.2.0/24",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

        dashboard = client.get("/dashboard")
        assert "/echo/" in dashboard.text
        assert "http://127.0.0.1:9000/" in dashboard.text
        assert "192.0.2.0/24" in dashboard.text
