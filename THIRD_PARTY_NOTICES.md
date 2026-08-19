# Third-party notices

RevProxy Manager is licensed under the MIT License. It depends on third-party software that remains governed by its own licenses.

## django-revproxy

- Project: `jazzband/django-revproxy`
- Role: HTTP reverse-proxy engine used by the runtime container
- Distribution model here: installed as an external Python dependency; not vendored or patched
- License: Mozilla Public License 2.0 (MPL-2.0)

Upstream project: https://github.com/jazzband/django-revproxy

## Other dependencies

The manager/runtime images also install Python and framework dependencies listed in `manager/requirements.txt` and `runtime/requirements.txt`. Their respective packages and licenses remain the property of their authors. This notice is not intended as a replacement for the license metadata shipped by those dependencies.
