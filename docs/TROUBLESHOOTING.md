# Troubleshooting

## I cannot open port 8087

Check containers:

```bash
docker compose ps
```

Check the manager health endpoint locally on the host:

```bash
curl -v http://127.0.0.1:8087/healthz
```

Inspect logs:

```bash
docker compose logs --tail=200 manager
```

If health works locally but the browser receives `403`, the management ACL probably does not include your effective source address.

## I locked myself out with an ACL

From the Docker host:

```bash
docker exec revproxy-manager python /app/recovery.py allow YOUR_IP/32
```

For IPv6 use `/128` for a single address.

As a last resort:

```bash
docker exec revproxy-manager python /app/recovery.py clear-acl
```

Then immediately log in and create a correct management ACL.

## The UI shows the proxy's IP instead of my client IP

If you intentionally put RevProxy Manager behind another reverse proxy:

1. read the **REMOTE_ADDR** value in Settings;
2. add that proxy IP/network under **Trusted Proxies**;
3. verify the edge proxy is sending `X-Forwarded-For`;
4. confirm **Effective Client IP** now shows the expected client.

Do not solve this by trusting `0.0.0.0/0` or `::/0`.

## A proxy route returns 404

A runtime 404 with `No enabled proxy route matches this path` means no enabled configured prefix matches the request.

Examples:

```text
route /grafana/ matches /grafana/ and /grafana/d/abc
route /grafana/ does not match /grafana-other/
```

The most specific enabled prefix wins.

## A proxy route returns 403

The route has an IP/CIDR allowlist and the effective client address is not included. Check the Trusted Proxy configuration if an edge proxy sits in front of port `8080`.

## Runtime has no routes after manager changes

The runtime reads the same `./data/revproxy.db` bind mount read-only. Verify both services use the expected mount:

```bash
docker compose config
```

Then inspect:

```bash
docker compose logs --tail=200 manager proxy
```

## Upstream is unreachable

The upstream URL is resolved and contacted **from the runtime container**, not from your browser. Test network reachability from the container's network context.

For example, if the upstream is another Compose service, use its Compose service name and internal port rather than `localhost`.

`localhost` inside `revproxy-runtime` refers to the runtime container itself.
