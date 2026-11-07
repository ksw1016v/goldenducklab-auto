"""계정·게시물 성과를 읽어서 insights.json 으로 저장 (읽기 전용, 게시·수정 없음)."""
import json, os, time, pathlib, urllib.request, urllib.parse
from publish import api_base, IG_USER_ID

ROOT = pathlib.Path(__file__).parent


def get(path, **p):
    p["access_token"] = os.environ["IG_TOKEN"]
    url = f"{api_base()}/{path}?" + urllib.parse.urlencode(p)
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode()[:300]}


acct = get(IG_USER_ID, fields="username,followers_count,follows_count,media_count")
media = get(f"{IG_USER_ID}/media", fields="id,caption,media_type,media_product_type,timestamp,like_count,comments_count,permalink", limit=100)
items = []
for m in media.get("data", []):
    metrics = "reach,saved,shares,total_interactions,views" if m.get("media_product_type") != "REELS" else "reach,saved,shares,total_interactions,views,ig_reels_avg_watch_time"
    ins = get(f"{m['id']}/insights", metric=metrics)
    if "error" in ins:
        ins = get(f"{m['id']}/insights", metric="reach,saved,shares,total_interactions")
    vals = {d["name"]: (d.get("values") or [{}])[0].get("value") for d in ins.get("data", [])}
    items.append({**{k: m.get(k) for k in ("id", "media_type", "media_product_type", "timestamp", "like_count", "comments_count", "permalink")},
                  "title": (m.get("caption") or "").split("\n")[0][:60], **vals, **({"insights_error": ins["error"]} if "error" in ins else {})})
    time.sleep(0.3)
day = get(f"{IG_USER_ID}/insights", metric="reach,profile_views,follower_count", period="day")
total = get(f"{IG_USER_ID}/insights", metric="profile_links_taps,accounts_engaged,total_interactions,views", period="day", metric_type="total_value")
out = {"fetched_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()), "account": acct, "account_daily": day, "account_totals_today": total, "media": items}
(ROOT / "insights.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(acct, ensure_ascii=False), len(items), "media")
