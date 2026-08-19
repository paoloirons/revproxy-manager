# Deployment

## Requirements

- Docker Engine with Docker Compose v2
- a host that can reach the intended upstream services
- an unused host port for the manager (default `8087`)
- an unused host port for the proxy runtime (default `8080`)

## Standard deployment

```bash
git clone https://github.com/paoloirons/revproxy-manager.git
cd revproxy-manager
cp .env.example .env
docker compose up -d --build
```

Verify container health:

```bash
docker compose ps
curl -fsS http://127.0.0.1:8087/healthz
curl -fsS http://127.0.0.1:8080/healthz
```

Then open `http://HOST:8087` and complete first-run setup.

## Environment variables

| Variable | Default | Purpose |
|---|---:|---|
| `MANAGER_PORT` | `8087` | Host port published for the management UI |
| `PROXY_PORT` | `8080` | Host port published for proxied traffic |
| `MANAGER_SECRET` | blank | Optional explicit signing secret; blank generates a persistent secret in `/data` |
| `SECURE_COOKIES` | `0` | Set to `1` when the management UI is served via HTTPS |

## Deployment behind an HTTPS edge proxy

A common production layout is:

```text
Internet / VPN
     │
     ▼
TLS edge proxy
     │
     ├──► RevProxy Manager :8087
     └──► RevProxy Runtime :8080
```

For the management UI:

1. terminate TLS at the edge;
2. set `SECURE_COOKIES=1`;
3. add only the edge proxy IP/CIDR under **Trusted Proxies**;
4. add the desired real client networks under **Management ACL**;
5. make sure the edge proxy sends a correct `X-Forwarded-For` chain.

Do not mark broad untrusted networks as Trusted Proxies.

## Data backup

Back up at least:

```text
data/revproxy.db
data/manager.secret
```

A consistent backup is easiest while the manager is stopped:

```bash
docker compose stop manager
cp -a data data.backup
Docker compose start manager
```

Alternatively use SQLite's online backup tooling from a controlled maintenance process.

## Updating the application

```bash
git pull --ff-only
docker compose build
docker compose up -d
```

Check:

```bash
docker compose ps
docker compose logs --tail=100 manager proxy
```

## Updating only `django-revproxy`

Change the version in `runtime/requirements.txt`, run the test suite, then rebuild only the runtime:

```bash
python -m pytest -q tests
docker compose build proxy
docker compose up -d proxy
```

The manager container does not depend on `django-revproxy` and does not need to be rebuilt for a runtime-only dependency change.
