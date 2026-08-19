import importlib.util
import os
import pathlib
import sqlite3
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("django") is None or importlib.util.find_spec("revproxy") is None,
    reason="Django/django-revproxy not installed in this environment",
)

ROOT = pathlib.Path(__file__).parents[1]
RUNTIME = ROOT / "runtime"


class EchoHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = f"upstream:{self.path}".encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass


def _create_db(data_dir, upstream):
    db_path = pathlib.Path(data_dir) / "revproxy.db"
    con = sqlite3.connect(db_path)
    con.executescript(
        """
        CREATE TABLE proxy_routes (
          id INTEGER PRIMARY KEY, name TEXT, path_prefix TEXT UNIQUE,
          upstream TEXT, enabled INTEGER, add_x_forwarded INTEGER
        );
        CREATE TABLE route_acl (id INTEGER PRIMARY KEY, route_id INTEGER, cidr TEXT);
        CREATE TABLE trusted_proxies (id INTEGER PRIMARY KEY, cidr TEXT, description TEXT);
        """
    )
    con.execute(
        "INSERT INTO proxy_routes(id,name,path_prefix,upstream,enabled,add_x_forwarded) VALUES(1,'Echo','/echo/',?,1,1)",
        (upstream,),
    )
    con.commit()
    con.close()


def test_real_django_revproxy_request(tmp_path, monkeypatch):
    server = HTTPServer(("127.0.0.1", 0), EchoHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        upstream = f"http://127.0.0.1:{server.server_port}/"
        _create_db(tmp_path, upstream)
        monkeypatch.setenv("DATA_DIR", str(tmp_path))
        sys.path.insert(0, str(RUNTIME))
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

        import django
        django.setup()
        from django.test import Client

        response = Client().get("/echo/hello/world?x=1")
        assert response.status_code == 200
        assert response.content == b"upstream:hello/world?x=1"
    finally:
        server.shutdown()
        server.server_close()
        if str(RUNTIME) in sys.path:
            sys.path.remove(str(RUNTIME))
