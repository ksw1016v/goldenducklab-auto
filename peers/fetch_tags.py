"""해시태그 인기 게시물 (읽기 전용). peers/tags.txt → peers/tags.json"""
import json, os, re, time, pathlib, urllib.request, urllib.parse, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from publish import api_base, IG_USER_ID
ROOT = pathlib.Path(__file__).parent
TOK = os.environ["IG_TOKEN"]
def get(path, **p):
    p["access_token"] = TOK
    try:
        with urllib.request.urlopen(f"{api_base()}/{path}?" + urllib.parse.urlencode(p), timeout=60) as r:
            d = json.loads(r.read()); d.pop("paging", None); return d
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode()[:200]}
out = {}
for t in [l.strip().lstrip("#") for l in (ROOT / "tags.txt").read_text().splitlines() if l.strip() and not l.startswith("#")]:
    h = get("ig_hashtag_search", user_id=IG_USER_ID, q=t)
    if "error" in h or not h.get("data"):
        out[t] = h; print("err", t, str(h)[:120]); continue
    hid = h["data"][0]["id"]
    m = get(f"{hid}/top_media", user_id=IG_USER_ID, fields="caption,media_type,media_product_type,like_count,comments_count,permalink,timestamp", limit=50)
    out[t] = {"id": hid, "top": [{**{k: x.get(k) for k in ("media_type", "media_product_type", "like_count", "comments_count", "permalink", "timestamp")}, "caption": (x.get("caption") or "")[:300]} for x in m.get("data", [])], **({"error": m["error"]} if "error" in m else {})}
    print("ok", t, len(out[t]["top"]))
    time.sleep(0.5)
text = json.dumps({"fetched_at": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), "tags": out}, ensure_ascii=False, indent=1)
text = re.sub(r"access_token=[^&\"\s]+", "access_token=REDACTED", text)
assert TOK not in text
(ROOT / "tags.json").write_text(text, encoding="utf-8")
