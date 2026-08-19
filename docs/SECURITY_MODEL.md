# Security model

RevProxy Manager is an administrative network component. Its safest deployment is on a trusted LAN or VPN, with the management interface kept away from direct public exposure.

## Trust boundaries

There are three separate decisions:

1. **Who can open the management UI?** — `management_acl`
2. **Which reverse proxies may assert client IP information?** — `trusted_proxies`
3. **Who can use a particular proxy route?** — `route_acl`

Do not combine these concepts. A network being trusted to forward client-IP metadata does not automatically mean clients from that network are allowed to administer the manager or access every route.

## Effective client IP

The immediate socket peer (`REMOTE_ADDR`) is authoritative unless it belongs to a configured Trusted Proxy network.

If the immediate peer is trusted and an `X-Forwarded-For` header is present, the application evaluates the chain from right to left and chooses the nearest valid IP that is not itself a trusted proxy hop.

This means an arbitrary Internet client cannot gain an allowed address by sending:

```http
X-Forwarded-For: 192.168.1.10
```

unless the request actually arrives through a peer that you explicitly configured as trusted.

## Management sessions

- Passwords are stored using PBKDF2-HMAC-SHA256 with a random salt.
- Session data is signed using `itsdangerous`.
- Session cookies are `HttpOnly` and `SameSite=Strict`.
- Authenticated state-changing forms use a per-session CSRF token.
- Session lifetime is 12 hours.
- If no explicit `MANAGER_SECRET` of sufficient length is supplied, a random persistent secret is generated in `/data/manager.secret` with mode `0600`.

When the UI is served via HTTPS, set:

```text
SECURE_COOKIES=1
```

## First-run setup risk

Before the first administrator exists, `/setup` must be reachable so the initial account can be created. Do the first start on a controlled LAN/VPN and finish setup before exposing the host more broadly. Do not publish an uninitialized manager directly to the Internet.

## Management ACL behavior

- No management ACL rows means the UI is not restricted by source IP.
- First-run setup can add the detected client as a single-host allow rule.
- The UI prevents deleting the final ACL rule to reduce accidental lockout.
- Recovery commands can deliberately bypass that safeguard from the host/container console.

## Route ACL behavior

- No ACL rows for a route means that route accepts all source IPs that can reach port `8080`.
- One or more ACL rows changes the route to allowlist behavior.
- IPv4 and IPv6 CIDRs are accepted.

## Upstream URLs

Only `http://` and `https://` upstream URLs are accepted. User-info credentials such as:

```text
http://user:password@example.internal/
```

are rejected so credentials are not stored in the SQLite configuration.

This is not an SSRF sandbox: an authenticated administrator is intentionally allowed to point a route at internal HTTP services reachable by the runtime container.

## What this project does not provide

The current release does not provide:

- TLS certificate issuance or storage;
- Web Application Firewall rules;
- malware scanning;
- brute-force login rate limiting;
- SSO / MFA;
- secret storage for upstream credentials;
- isolation between multiple administrators;
- a security boundary against a malicious host administrator.

Use network controls appropriate to the sensitivity of your services.

## Lockout recovery

Allow one management CIDR:

```bash
docker exec revproxy-manager python /app/recovery.py allow 192.168.1.50/32
```

Clear all management ACLs:

```bash
docker exec revproxy-manager python /app/recovery.py clear-acl
```

Reset a password:

```bash
docker exec revproxy-manager \
  python /app/recovery.py reset-password admin 'NewStrongPassword'
```
