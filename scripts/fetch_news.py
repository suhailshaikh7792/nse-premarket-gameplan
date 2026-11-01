import json, time, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30))
now = datetime.now(IST)
end = now.replace(hour=8, minute=30, second=0, microsecond=0)
if now < end:
    end = now
start = (end - timedelta(days=1)).replace(hour=15, minute=30, second=0, microsecond=0)
queries = [
    '("India" OR "Indian") (stocks OR shares OR NSE OR BSE OR markets)',
    '("India" OR "Indian") (company OR corporate) (order OR contract OR acquisition OR merger OR results OR earnings OR regulation)',
    '("crude oil" OR Brent OR RBI OR "Indian rupee" OR tariffs OR "interest rates")',
    '(geopolitical OR "global markets" OR "US markets" OR "China markets") (India OR Asian OR oil OR trade)'
]
def seen_time(value):
    try:
        return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).astimezone(IST)
    except (TypeError, ValueError):
        return None
articles = {}
warnings = []
for i, query in enumerate(queries):
    params = {"query": query, "mode": "ArtList", "format": "json", "maxrecords": "75", "sort": "DateDesc", "timespan": "48h"}
    url = "https://api.gdeltproject.org/api/v2/doc/doc?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "NSE-Premarket-GamePlan/1.0"})
        with urllib.request.urlopen(req, timeout=35) as response:
            rows = json.loads(response.read().decode("utf-8")).get("articles", [])
        for row in rows:
            title, link = (row.get("title") or "").strip(), (row.get("url") or "").strip()
            stamp = seen_time(row.get("seendate"))
            if title and link and stamp and start <= stamp <= end:
                articles[link] = {"title": title, "url": link, "source": row.get("domain") or urllib.parse.urlparse(link).netloc, "firstSeenAt": stamp.isoformat()}
    except Exception as exc:
        warnings.append("Query " + str(i + 1) + " failed: " + str(exc))
    if i != len(queries) - 1:
        time.sleep(5.5)
result = {"generatedAt": now.isoformat(), "windowStart": start.isoformat(), "windowEnd": end.isoformat(), "timezone": "Asia/Kolkata", "provider": "GDELT DOC 2.0", "providerUrl": "https://www.gdeltproject.org/", "articleCount": len(articles), "articles": sorted(articles.values(), key=lambda x: x["firstSeenAt"], reverse=True)[:200], "warnings": warnings, "notice": "Headlines and links only. Open the publisher source to verify details; coverage is not exhaustive."}
Path("public/data").mkdir(parents=True, exist_ok=True)
Path("public/data/news.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Saved", len(articles), "articles.")
