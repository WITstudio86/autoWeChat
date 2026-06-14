import json
import ssl
import urllib.request


def _parse_version(tag):
    """Parse 'v1.2.3' or '1.2.3' to tuple of ints."""
    tag = tag.lstrip("v")
    try:
        return tuple(int(x) for x in tag.split("."))
    except (ValueError, AttributeError):
        return (0,)


def check_for_update(current_version, server_url):
    """Return (has_update, latest_version, html_url).

    Calls the Node.js server's /api/version/latest endpoint,
    which proxies GitHub Releases with authentication.
    """
    current_tuple = _parse_version(current_version)

    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        api_url = server_url.rstrip("/") + "/api/version/latest"
        req = urllib.request.Request(api_url)
        req.add_header("Accept", "application/json")

        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = json.loads(resp.read().decode())

        version = data.get("version", "")
        html_url = data.get("html_url", server_url)

        latest_tuple = _parse_version(version)
        if latest_tuple > current_tuple:
            return True, version, html_url

        return False, "", ""
    except Exception:
        return False, "", ""
