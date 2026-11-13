"""다른 계정 공개 성과 비교 (비즈니스 디스커버리, 읽기 전용). peers/list.txt → peers/peers.json"""
import json, os, re, time, pathlib, urllib.request, urllib.parse, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from publish import api_base, IG_USER_ID
ROOT = pathlib.Path(__file__).parent
TOK = os.environ["IG_TOKEN"]
F = "username,name,biography,followers_count,media_count,media.limit(30){caption,media_product_type,media_type,timestamp,like_count,comments_count,permalink}"
out = {}
for u in [l.strip().lstrip("@") for l in (ROOT / "list.txt").read_text().splitlines() if l.strip() and not l.startswith("#")]:
    q = urllib.parse.urlencode({"fields": f"business_discovery.username({u}){{{F}}}", "access_token": TOK})
    try:
        with urllib.request.urlopen(f"{api_base()}/{IG_USER_ID}?{q}", timeout=60) as r:
            d = json.loads(r.read()).get("business_discovery", {})
        ms = d.pop("media", {}).get("data", [])
        d["media"] = [{**{k: m.get(k) for k in ("media_product_type", "media_type", "timestamp", "like_count", "comments_count", "permalink")},
                       "title": (m.get("caption") or "").split("\n")[0][:70]} for m in ms]
        out[u] = d
        print("ok", u, d.get("followers_count"))
    except urllib.error.HTTPError as e:
        out[u] = {"error": e.read().decode()[:200]}
        print("err", u)
    time.sleep(0.5)
text = json.dumps({"fetched_at": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), "accounts": out}, ensure_ascii=False, indent=1)
text = re.sub(r"access_token=[^&\"\s]+", "access_token=REDACTED", text)
assert TOK not in text
(ROOT / "peers.json").write_text(text, encoding="utf-8")
