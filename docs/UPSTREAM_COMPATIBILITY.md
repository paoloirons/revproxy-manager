# Upstream compatibility

## Design goal

`django-revproxy` must remain a normal external dependency. RevProxy Manager should never require patches inside the upstream package in order to function.

The adapter boundary is intentionally small:

```python
from revproxy.views import ProxyView

class DynamicProxyView(ProxyView):
    ...
```

The runtime sets `self.upstream`, rewrites the route-local path, then delegates to `ProxyView.dispatch()`.

## Current baseline

The runtime currently pins:

```text
Python 3.11
Django >=4.2,<5.0
django-revproxy ==0.13.0
```

At the time this baseline was selected, `0.13.0` is the current PyPI release of `django-revproxy` and is distributed under MPL-2.0.

## CI strategy

### Pinned runtime test

Every push and pull request installs exactly `runtime/requirements.txt` and runs `tests/test_runtime_integration.py`.

That test starts a real local HTTP server and verifies this chain:

```text
Django test client
   -> DynamicProxyView
   -> django-revproxy ProxyView
   -> local upstream HTTP server
   -> response back to Django client
```

This catches more than import-level compatibility problems: it validates actual URL/path forwarding.

### Latest-upstream compatibility job

A scheduled/manual GitHub Actions job installs:

```text
Django >=4.2,<5
django-revproxy >=0.13
```

without the exact upstream pin, then runs the same integration smoke test. The job is informational (`continue-on-error`) so a newly released breaking upstream version is visible without turning an existing known-good baseline red.

## Upgrade procedure

When a new upstream release passes the compatibility job:

1. update `runtime/requirements.txt`;
2. run the full test suite;
3. build both Docker images;
4. inspect the upstream changelog/release notes;
5. deploy to a non-critical environment;
6. update `CHANGELOG.md` and the README baseline.

If an upstream release breaks the adapter, fix the adapter in this repository. Do not patch or vendor upstream source code unless the architecture of the project is intentionally changed in a future major version.
