import subprocess
import json
import os
import hashlib
import httpx
import time

__all__ = ["get_stream"]

# ==============================
# CONFIG
# ==============================

_CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")
os.makedirs(_CACHE_DIR, exist_ok=True)

_MEM_CACHE = {}
_client = httpx.Client(timeout=5, follow_redirects=True)

# ==============================
# HELPERS
# ==============================

def _key(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def _cache_path(url: str) -> str:
    return os.path.join(_CACHE_DIR, _key(url) + ".json")


def _is_alive(stream_url: str) -> bool:
    """
    Check whether stream URL is still valid
    """
    try:
        r = _client.head(stream_url)
        return r.status_code == 200
    except Exception:
        return False


def _read_disk(url: str):
    path = _cache_path(url)
    if not os.path.exists(path):
        return None

    try:
        with open(path, "r") as f:
            data = json.load(f)

        stream = data.get("stream")
        if stream and _is_alive(stream):
            return stream
    except Exception:
        pass

    return None


def _write_disk(url: str, stream: str):
    try:
        with open(_cache_path(url), "w") as f:
            json.dump({"stream": stream}, f)
    except Exception:
        pass


def _extract_stream(url: str) -> str | None:
    cmd = [
        "yt-dlp",
        "-J",
        "-f", "ba/b",
        "--quiet",
        "--no-warnings",
        "--extractor-args", "youtube:player-client=android",
        url
    ]

    p = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if p.returncode != 0:
        return None

    data = json.loads(p.stdout)

    for f in data.get("formats", []):
        if (
            f.get("acodec") not in (None, "none")
            and f.get("vcodec") in (None, "none")
            and f.get("url")
        ):
            return f["url"]

    return None


# ==============================
# PUBLIC API
# ==============================

def get_stream(url: str) -> str | None:
    # 1️⃣ RAM cache
    cached = _MEM_CACHE.get(url)
    if cached and _is_alive(cached):
        return cached

    # 2️⃣ Disk cache
    cached = _read_disk(url)
    if cached:
        _MEM_CACHE[url] = cached
        return cached

    # 3️⃣ Fresh extract
    stream = _extract_stream(url)
    if stream:
        _MEM_CACHE[url] = stream
        _write_disk(url, stream)
        return stream

    return None
    
