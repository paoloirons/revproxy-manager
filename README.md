# RevProxy Manager

[![CI](https://github.com/paoloirons/revproxy-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/paoloirons/revproxy-manager/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![django--revproxy](https://img.shields.io/badge/django--revproxy-0.13.0-0C4B33)](https://github.com/jazzband/django-revproxy)

A compact web control plane for **[Jazzband's django-revproxy](https://github.com/jazzband/django-revproxy)**.

RevProxy Manager adds the part that `django-revproxy` intentionally does not provide: a small browser-based manager for creating path-based proxy routes, applying source-IP ACLs, and managing trusted reverse proxies. The upstream package itself stays **unmodified** and is installed from PyPI inside a separate runtime container.

> [!IMPORTANT]
> **Upstream relationship:** this repository is intentionally **not a source-code fork** of `jazzband/django-revproxy`. It is an independent companion/control-plane project built on top of it. That design is deliberate: upstream can be upgraded independently, there is no vendored `revproxy` source tree, and the compatibility boundary is covered by integration tests.

## What it provides

- Web manager on **port `8087`**.
- Django + `django-revproxy` runtime on **port `8080`**.
- First-run administrator setup.
- Management UI source-IP/CIDR allowlist.
- Per-route source-IP/CIDR allowlists.
- Trusted-proxy handling for `X-Forwarded-For`.
- Effective client-IP diagnostics in the UI.
- SQLite configuration shared read-only with the proxy runtime.
- Dynamic route changes without rebuilding or restarting the runtime.
- Recovery commands for ACL lockout and administrator password reset.
- Docker Compose deployment.
- GitHub Actions tests against the pinned upstream dependency plus a scheduled compatibility smoke test against newer `django-revproxy` releases.

## Quick start

```bash
git clone https://github.com/paoloirons/revproxy-manager.git
cd revproxy-manager
cp .env.example .env
docker compose up -d --build
```

Open:

```text
http://SERVER_IP:8087
```

The first-run wizard creates the administrator account. By default it can also allow only the client IP used during setup, stored as a `/32` for IPv4 or `/128` for IPv6.

The proxy runtime listens on:

```text
http://SERVER_IP:8080
```

Example route:

```text
Public path:  /grafana/
Upstream:     http://192.168.1.20:3000/
Allowed:      192.168.1.0/24
```

A request to:

```text
http://SERVER_IP:8080/grafana/d/abc?orgId=1
```

is proxied to:

```text
http://192.168.1.20:3000/d/abc?orgId=1
```

## Architecture

```text
                       management :8087
Browser ──────────────────────────────────────► FastAPI manager
                                                   │
                                                   │ writes
                                                   ▼
                                            /data/revproxy.db
                                                   ▲
                                                   │ read-only
                                                   │
Client  ──────────────────────────────────────► Django runtime
                         proxy :8080               │
                                                   │
                                                   ▼
                                            django-revproxy
                                             (unmodified)
                                                   │
                                  ┌────────────────┼──────────────┐
                                  ▼                ▼              ▼
                               Grafana            NAS           App
```

The manager and runtime are deliberately separate. The manager owns configuration; the runtime only reads it and adapts the selected route to `revproxy.views.ProxyView`.

See [Architecture](docs/ARCHITECTURE.md) for the full request flow.

## Security model

The management interface and the proxied services have separate ACLs.

**Management ACL** controls who may reach the UI on `8087`. **Route ACLs** control who may use each configured proxy path on `8080`.

`X-Forwarded-For` is accepted only when the immediate network peer belongs to a configured **Trusted Proxy** CIDR. When a trusted proxy chain exists, RevProxy Manager walks it from the nearest hop backwards and selects the nearest untrusted valid IP as the effective client address. Requests from untrusted peers cannot spoof their source address merely by supplying `X-Forwarded-For`.

Do not expose `8087` directly to the public Internet. Prefer LAN/VPN access, or place it behind an HTTPS edge proxy and configure that edge network under **Trusted Proxies**. Set `SECURE_COOKIES=1` when the management UI is served over HTTPS.

Read [Security model](docs/SECURITY_MODEL.md) before Internet-facing deployment.

## Recovery

If an ACL change locks you out of the manager:

```bash
docker exec revproxy-manager python /app/recovery.py allow 192.168.1.50/32
```

Clear the management ACL completely:

```bash
docker exec revproxy-manager python /app/recovery.py clear-acl
```

Reset an existing administrator password:

```bash
docker exec revproxy-manager \
  python /app/recovery.py reset-password admin 'NewStrongPassword'
```

`clear-acl` temporarily makes the management UI unrestricted by source IP. Use it only as a recovery operation and add a new ACL immediately afterwards.

## Updating `django-revproxy`

The upstream package is pinned in [`runtime/requirements.txt`](runtime/requirements.txt). No upstream source file exists in this repository.

Current baseline:

- Python 3.11
- Django `>=4.2,<5.0`
- `django-revproxy==0.13.0`

To evaluate a newer upstream release, update only the dependency pin and run:

```bash
python -m pytest -q tests
docker compose build proxy
docker compose up -d proxy
```

The scheduled GitHub Actions compatibility job also installs the latest `django-revproxy>=0.13` available with the current Django baseline and runs a real-request integration smoke test. See [Upstream compatibility](docs/UPSTREAM_COMPATIBILITY.md).

## Data and secrets

Persistent state lives under `./data/`:

```text
data/
├── revproxy.db
└── manager.secret
```

If `MANAGER_SECRET` is left blank, the manager generates a strong persistent secret in `data/manager.secret` with mode `0600`. You may instead provide `MANAGER_SECRET` through your own secret-management mechanism.

Back up `data/revproxy.db`. It contains route configuration, ACLs, trusted-proxy rules, administrator usernames and password hashes. It does **not** contain upstream credentials because user-info credentials in upstream URLs are rejected.

## Documentation

- [Deployment](docs/DEPLOYMENT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Security model](docs/SECURITY_MODEL.md)
- [Upstream compatibility](docs/UPSTREAM_COMPATIBILITY.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## Scope

This project intentionally starts smaller than Nginx Proxy Manager. It manages path-based HTTP/HTTPS upstreams, source-IP policy and the Django reverse-proxy runtime. It does not currently manage TLS certificates, DNS challenges, TCP/UDP streams, load-balancing pools or virtual-host/domain routing.

Those features can be added later without changing the core rule: **`django-revproxy` remains an external, unmodified dependency.**

## Upstream attribution and licensing

`django-revproxy` is maintained by Jazzband and distributed under the **Mozilla Public License 2.0**. RevProxy Manager is an independent project and is distributed under the **MIT License**.

Using this repository does not transfer ownership of, or relicense, `django-revproxy`. See [Third-party notices](THIRD_PARTY_NOTICES.md).

## Project status

This is an early implementation intended for controlled/self-hosted environments. Review the security documentation and validate it in your own network before relying on it for sensitive production traffic.
