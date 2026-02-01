from __future__ import annotations

from pathlib import Path

from .exceptions import BaiduPanAuthError


def parse_cookie_text(cookie_text: str) -> dict[str, str]:
    """
    Parse cookie text into a dict.

    Supported formats:
    - "key=value; key2=value2" (Cookie header-like)
    - Netscape cookies.txt export (7 tab-separated fields)
    """
    cookie_text = cookie_text.strip()
    if not cookie_text:
        return {}

    lines = [ln.strip() for ln in cookie_text.splitlines() if ln.strip()]
    # Netscape format usually has tab-separated fields and comment lines starting with '#'
    if any("\t" in ln for ln in lines):
        cookies: dict[str, str] = {}
        for ln in lines:
            if ln.startswith("#"):
                continue
            parts = ln.split("\t")
            if len(parts) < 7:
                continue
            name = parts[5].strip()
            value = parts[6].strip()
            if name:
                cookies[name] = value
        return cookies

    # Cookie header-like format
    cookies: dict[str, str] = {}
    for part in cookie_text.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        name, value = part.split("=", 1)
        name = name.strip()
        value = value.strip()
        if name:
            cookies[name] = value
    return cookies


def load_cookies(cookie_file: str | Path) -> dict[str, str]:
    path = Path(cookie_file)
    if not path.exists():
        raise BaiduPanAuthError(f"cookie file not found: {path}")
    text = path.read_text(encoding="utf-8")
    cookies = parse_cookie_text(text)
    if not cookies:
        raise BaiduPanAuthError(f"failed to parse cookies from: {path}")
    return cookies
