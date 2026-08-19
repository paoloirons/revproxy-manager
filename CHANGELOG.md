# Changelog

All notable changes to RevProxy Manager will be documented here.

## [0.1.0] - 2026-08-19

### Added

- FastAPI management UI on port 8087.
- First-run administrator setup and signed sessions.
- Management source-IP/CIDR ACLs.
- Trusted Proxy configuration and safe `X-Forwarded-For` handling.
- Effective client-IP diagnostics.
- Dynamic proxy-route CRUD with per-route CIDR ACLs.
- Django runtime on port 8080 using unmodified `django-revproxy` from PyPI.
- Shared SQLite configuration with read-only runtime access.
- Docker Compose deployment and health checks.
- Recovery CLI for management ACL lockout and password reset.
- CI for manager tests, Docker builds, pinned runtime integration and scheduled latest-upstream compatibility checks.
- Architecture, deployment, security, compatibility and troubleshooting documentation.
