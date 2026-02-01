from urllib.parse import quote_plus
import httpx
import re
import orjson
import asyncio

# ─────────────────────────────
# CONFIG
# ─────────────────────────────
UPSTASH_REDIS_REST_URL = "https://accepted-woodcock-22573.upstash.io"
UPSTASH_REDIS_REST_TOKEN = "PASTE_YOUR_TOKEN_HERE"

REDIS_HEADERS = {
    "Authorization": f"Bearer {UPSTASH_REDIS_REST_TOKEN}"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9"
}

YOUTUBE_SEARCH_URL = "https://www.youtube.com/results?search_query={}"
YT_REGEX = re.compile(r"ytInitialData\s*=\s*(\{.+?\});", re.DOTALL)

_client = httpx.AsyncClient(http2=True, timeout=10)

# ─────────────────────────────
# CACHE
# ─────────────────────────────
MEMORY_CACHE = {}
LOCKS = {}
CACHE_LIMIT = 1000


def normalize(q: str):
    return re.sub(r"\s+", " ", q.lower().strip())


def format_views(text: str):
    return text.replace(" views", "").replace(" view", "")


# ─────────────────────────────
# REDIS HELPERS
# ─────────────────────────────
async def redis_get(key):
    r = await _client.get(
        f"{UPSTASH_REDIS_REST_URL}/get/{key}",
        headers=REDIS_HEADERS
    )
    if r.status_code == 200:
        return r.json().get("result")
    return None


async def redis_set(key, value):
    await _client.post(
        f"{UPSTASH_REDIS_REST_URL}/set/{key}",
        headers=REDIS_HEADERS,
        json={"value": value.decode()}
    )


# ─────────────────────────────
# MAIN SEARCH
# ─────────────────────────────
async def Search(query: str, limit: int = 1):
    if not query:
        return {"main_results": [], "suggested": []}

    qkey = normalize(query)

    # RAM CACHE
    if qkey in MEMORY_CACHE:
        return MEMORY_CACHE[qkey]

    # REDIS CACHE
    cached = await redis_get(qkey)
    if cached:
        data = orjson.loads(cached.encode())
        MEMORY_CACHE[qkey] = data
        return data

    lock = LOCKS.setdefault(qkey, asyncio.Lock())
    async with lock:

        url = YOUTUBE_SEARCH_URL.format(quote_plus(query))
        r = await _client.get(url, headers=HEADERS)

        match = YT_REGEX.search(r.text)
        if not match:
            return {"main_results": [], "suggested": []}

        raw = orjson.loads(match.group(1))
        contents = raw["contents"]["twoColumnSearchResultsRenderer"][
            "primaryContents"]["sectionListRenderer"]["contents"
        ]

        results = []

        for section in contents:
            items = section.get("itemSectionRenderer", {}).get("contents", [])
            for item in items:
                v = item.get("videoRenderer")
                if not v:
                    continue

                video_id = v["videoId"]

                results.append({
                    "title": v["title"]["runs"][0]["text"],
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "duration": v.get("lengthText", {}).get("simpleText", "LIVE"),
                    "channel": v.get("ownerText", {}).get("runs", [{}])[0].get("text", "Unknown"),
                    "views": format_views(
                        v.get("viewCountText", {}).get("simpleText", "0 views")
                    ),
                    "thumbnail": f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
                })

                if len(results) >= limit + 5:
                    break

        output = {
            "main_results": results[:limit],
            "suggested": results[limit:limit + 5]
        }

        if len(MEMORY_CACHE) >= CACHE_LIMIT:
            MEMORY_CACHE.clear()

        MEMORY_CACHE[qkey] = output
        await redis_set(qkey, orjson.dumps(output))

        return output
        
