# Contributing

Contributions are welcome, especially fixes that preserve the project's core architectural boundary: **the upstream `django-revproxy` package remains unmodified**.

## Local development

Create a Python 3.11 virtual environment and install test/runtime dependencies as needed:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r manager/requirements.txt
pip install -r runtime/requirements.txt
pip install pytest httpx
pytest -q tests
```

Docker validation:

```bash
docker compose config
docker compose build
```

Run locally with Docker:

```bash
cp .env.example .env
docker compose up -d --build
```

## Pull requests

A useful change should include tests when behavior changes. For changes touching the runtime adapter, make sure `tests/test_runtime_integration.py` still performs a real request through Django and `django-revproxy`.

Do not vendor `django-revproxy`, copy its source into `runtime/`, or patch site-packages during image build. If upstream compatibility requires a change, adapt our `DynamicProxyView` boundary instead.

## Security-sensitive changes

Changes involving client-IP resolution, Trusted Proxies, management ACLs, route ACLs, sessions, cookies, CSRF, password storage or recovery commands should include focused tests and an update to `docs/SECURITY_MODEL.md` when the trust model changes.
