import json
import ssl
import urllib.request

GITHUB_API = "https://api.github.com/repos/WITstudio86/autoWeChat/releases/latest"


def _parse_version(tag):
    """Parse 'v1.2.3' or '1.2.3' to tuple of ints."""
    tag = tag.lstrip("v")
    try:
        return tuple(int(x) for x in tag.split("."))
    except (ValueError, AttributeError):
        return (0,)


def check_for_update(current_version):
    """Return (has_update, latest_version, html_url).

    Compares current_version against the latest GitHub Release.
    Skips prereleases.
    """
    current_tuple = _parse_version(current_version)

    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(GITHUB_API)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("User-Agent", "autoWeChat-update-checker")

        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = json.loads(resp.read().decode())

        tag = data.get("tag_name", "")
        html_url = data.get("html_url", "https://wechat.zelab.top")
        prerelease = data.get("prerelease", False)

        if prerelease:
            return False, "", ""

        latest_tuple = _parse_version(tag)
        if latest_tuple > current_tuple:
            return True, tag.lstrip("v"), html_url

        return False, "", ""
    except Exception:
        return False, "", ""
