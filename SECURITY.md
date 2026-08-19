# Security policy

RevProxy Manager is currently an early self-hosted project.

## Supported versions

Security fixes are applied to the latest code on the default branch until formal versioned releases are established.

## Reporting

For issues that do not expose sensitive details, open a GitHub issue with reproducible steps. For vulnerabilities that would create immediate risk if published, use a private GitHub security advisory/reporting channel when available rather than posting exploit details publicly.

## Deployment security

Before deployment, read [docs/SECURITY_MODEL.md](docs/SECURITY_MODEL.md). In particular:

- do not expose an uninitialized manager to the Internet;
- keep port 8087 on a trusted LAN/VPN or behind a hardened HTTPS edge;
- configure Trusted Proxies narrowly;
- use source-IP management ACLs;
- set `SECURE_COOKIES=1` when management traffic is HTTPS;
- protect and back up `data/revproxy.db` and `data/manager.secret`.
