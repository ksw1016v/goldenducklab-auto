"""황금알 퀴즈 댓글 → 자동 대댓글 + 정답 DM (GitHub Actions에서 주기 실행).

- 대상: 올린 퀴즈 릴스(state.json 의 quiz_media: {media_id: 원고 경로})
- 시험 모드(TEST=1): 최근 게시물 전체에서 키워드 댓글을 찾아 TEST_EP 원고의 정답으로 응답
- 댓글 하나당 대댓글 1개 + DM 1통(인스타 규정: 댓글당 비공개 답장 1통, 7일 이내)
- 이미 처리한 댓글은 state.json 의 quiz_dm_done 에 기록해 다시 보내지 않음
"""
import json, os, re, sys, random, time, datetime, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from publish import call, IG_USER_ID, load_state, STATE  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OWN = "golden_duck_lab"


def norm(t):
    return re.sub(r"[\s!~.?·]", "", t or "")


def safe(method, path, **p):
    try:
        return call(method, path, **p), None
    except SystemExit as ex:
        return None, str(ex)[:400]


def send_dm(cid, text):
    payload = dict(recipient=json.dumps({"comment_id": cid}), message=json.dumps({"text": text}, ensure_ascii=False))
    r, err = safe("POST", f"{IG_USER_ID}/messages", **payload)
    if err:
        r2, err2 = safe("POST", "me/messages", **payload)
        if not err2:
            return r2, None
        err = f"{err} | me/messages: {err2}"
    return r, err


def targets(st):
    t = {m: p for m, p in st.get("quiz_media", {}).items()}
    if os.environ.get("TEST") == "1":
        ep = os.environ.get("TEST_EP", "quiz/episodes/01.json")
        media, err = safe("GET", f"{IG_USER_ID}/media", fields="id,timestamp", limit=10)
        if err:
            print("::error::게시물 목록 실패", err)
        for m in (media or {}).get("data", []):
            t.setdefault(m["id"], ep)
    return t


def main():
    st = load_state()
    done = set(st.get("quiz_dm_done", []))
    log = st.setdefault("quiz_dm_log", [])
    now = datetime.datetime.now(datetime.timezone.utc)
    sent = 0
    for media_id, ep_path in targets(st).items():
        ep = json.loads((ROOT / ep_path).read_text(encoding="utf-8"))
        kw = norm(ep.get("keyword", "골든덕"))
        res, err = safe("GET", f"{media_id}/comments", fields="id,text,username,timestamp", limit=50)
        if err:
            print("::warning::댓글 읽기 실패", media_id, err)
            continue
        for c in res.get("data", []):
            if c["id"] in done or c.get("username") == OWN or kw not in norm(c.get("text")):
                continue
            ts = datetime.datetime.strptime(c["timestamp"], "%Y-%m-%dT%H:%M:%S%z")
            if now - ts > datetime.timedelta(days=6, hours=20):
                continue  # 인스타 규정: 7일 지난 댓글엔 DM 불가
            reply = random.choice(ep["dm"]["comment_replies"])
            dm, dm_err = send_dm(c["id"], ep["dm"]["answer"])
            print("DM 응답", dm, dm_err)
            rp, rp_err = safe("POST", f"{c['id']}/replies", message=reply if not dm_err else "댓글 고마워요 🥚 정답은 곧 DM으로 보내드릴게요!")
            rec = {"comment": c["id"], "media": media_id, "user": c.get("username"), "quiz": ep.get("no"),
                   "dm": "ok" if not dm_err else "fail", "reply": "ok" if not rp_err else "fail",
                   "at": time.strftime("%Y-%m-%d %H:%M:%S")}
            if dm_err:
                rec["dm_error"] = dm_err
                print("::warning::DM 실패", c["id"], dm_err)
            if rp_err:
                rec["reply_error"] = rp_err
                print("::warning::대댓글 실패", c["id"], rp_err)
            log.append(rec)
            done.add(c["id"])
            sent += 1
            print("처리", rec)
            time.sleep(2)
    st["quiz_dm_done"] = sorted(done)
    st["quiz_dm_log"] = log[-500:]
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=1))
    print(f"새로 처리한 댓글 {sent}개")


if __name__ == "__main__":
    main()
