"""퀴즈 게시물 댓글이 API에서 어떻게 보이는지, 봇이 어떻게 판단하는지 출력 (읽기 전용)."""
import json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from dm_bot import safe, match, ROOT, IG_USER_ID  # noqa
from publish import load_state
st = load_state(); done = set(st.get("quiz_dm_done", []))
for mid, p in st.get("quiz_media", {}).items():
    ep = json.loads((ROOT / p).read_text(encoding="utf-8"))
    info, e0 = safe("GET", mid, fields="comments_count,timestamp,permalink")
    print("==", p, info, e0)
    res, err = safe("GET", f"{mid}/comments", fields="id,text,username,timestamp,from", limit=50)
    print("  댓글 API 오류:", err) if err else None
    for c in (res or {}).get("data", []):
        print("  ", c.get("timestamp"), c.get("username"), c.get("from"), repr(c.get("text")), "→", match(ep, c.get("text")), "처리됨" if c["id"] in done else "")
