# Architecture

RevProxy Manager is split into two processes and two trust zones: a **management control plane** and a **proxy data plane**.

## Components

### Manager (`manager/`, port 8087)

The manager is a small FastAPI application using Jinja templates and server-rendered HTML. It owns all writes to the SQLite database.

Responsibilities:

- first-run administrator creation;
- signed session cookies and CSRF tokens;
- management source-IP ACLs;
- trusted-proxy CIDRs;
- proxy-route CRUD;
- per-route source-IP ACLs;
- client-IP diagnostics;
- recovery CLI.

### Runtime (`runtime/`, port 8080)

The runtime is a minimal Django project. It imports `ProxyView` from the PyPI-installed `django-revproxy` package:

```python
from revproxy.views import ProxyView
```

The runtime does not write configuration. It mounts `/data` read-only, loads enabled routes from SQLite for each request, selects the most-specific matching prefix, applies the route ACL, and delegates the actual HTTP proxying to `django-revproxy`.

### Shared database

The manager creates `data/revproxy.db`. The runtime opens the database using SQLite URI read-only mode.

The main tables are:

```text
users
management_acl
trusted_proxies
proxy_routes
route_acl
```

SQLite uses rollback-journal mode rather than WAL so the read-only runtime container does not need to create or mutate `-wal` / `-shm` sidecar files.

## Request flow: management

```text
Browser
  │
  ▼
:8087 / FastAPI
  │
  ├─ resolve effective client IP
  │    ├─ REMOTE_ADDR
  │    ├─ Trusted Proxies
  │    └─ X-Forwarded-For (only when peer is trusted)
  │
  ├─ management ACL
  │
  ├─ signed session + CSRF
  │
  └─ HTML dashboard / configuration write
```

## Request flow: proxy runtime

```text
Client
  │
  ▼
:8080 / Django
  │
  ├─ load enabled routes
  ├─ choose longest matching path prefix
  ├─ calculate effective client IP
  ├─ enforce per-route CIDR ACL
  ├─ strip public route prefix
  └─ django-revproxy ProxyView
          │
          ▼
       upstream
```

## Dynamic configuration

Routes are not compiled into `urls.py`. Django has one catch-all URL pattern and the adapter selects a route at request time. As a result, creating, editing, enabling or disabling a route does not require a container rebuild or application restart.

## Why upstream stays untouched

Vendoring or patching `django-revproxy` would make every upstream update a merge exercise. This repository instead keeps a narrow adapter boundary around the documented `ProxyView` API. Compatibility is checked with a real integration test that sends a request through Django and `django-revproxy` to a local HTTP upstream.
