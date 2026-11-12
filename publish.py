"""대기열에서 다음 편을 골라 인스타그램에 캐러셀로 게시한다.

환경변수
  IG_TOKEN     인스타그램 장기 액세스 토큰 (Instagram API with Instagram Login)
  IMAGE_BASE   이미지 공개 주소 접두사 (예: https://cdn.jsdelivr.net/gh/user/repo@<sha>)
  DRY_RUN=1    실제 게시 없이 확인만

사용법
  python publish.py next        -> 다음 게시할 편 번호 출력 (없으면 빈 줄)
  python publish.py post <no>   -> 해당 편 게시 후 state.json 갱신
"""
import json, os, sys, time, pathlib, urllib.request, urllib.parse
import caption_check

ROOT = pathlib.Path(__file__).parent
STATE = ROOT / "state.json"
IG_USER_ID = os.environ.get("IG_USER_ID", "17841465585453824")  # golden_duck_lab


def api_base():
    # IGAA... 토큰은 Instagram 로그인, EAA... 토큰은 Facebook(통합) 로그인
    tok = os.environ.get("IG_TOKEN", "")
    return "https://graph.instagram.com/v23.0" if tok.startswith("IG") else "https://graph.facebook.com/v23.0"


def load_state():
    return json.loads(STATE.read_text()) if STATE.exists() else {"published": []}


def next_episode():
    done = set(load_state()["published"])
    for f in sorted((ROOT / "episodes").glob("*.json")):
        no = json.loads(f.read_text(encoding="utf-8"))["no"]
        if no not in done:
            return no
    return None


def call(method, path, **params):
    params["access_token"] = os.environ["IG_TOKEN"]
    data = urllib.parse.urlencode(params).encode()
    url = f"{api_base()}/{path}"
    if method == "GET":
        req = urllib.request.Request(url + "?" + data.decode())
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"API 오류 {e.code} {path}: {e.read().decode()}")


def raw_base(base):
    """jsDelivr 주소 → GitHub raw 주소 (인스타가 jsDelivr 이미지를 못 가져올 때 대체)"""
    pre = "https://cdn.jsdelivr.net/gh/"
    if not base.startswith(pre) or "@" not in base:
        return None
    repo, sha = base[len(pre):].split("@", 1)
    return f"https://raw.githubusercontent.com/{repo}/{sha}"


def create_media(uid, base, rel, **params):
    """미디어 컨테이너 생성. 인스타가 URL에서 파일을 못 받아 오면(9004) 잠시 뒤 재시도 → raw 주소로 대체."""
    key = "video_url" if rel.endswith(".mp4") else "image_url"
    tries = [base, base, raw_base(base)]
    last = None
    for i, b in enumerate(t for t in tries if t):
        if i:
            print(f"::warning::미디어 주소를 못 가져와 다시 시도 ({b.split('/')[2]}) {rel}")
            time.sleep(15)
        extra = dict(params)
        if "cover_url" in extra:
            extra["cover_url"] = f"{b}/{extra['cover_url']}"
        try:
            return call("POST", f"{uid}/media", **{key: f"{b}/{rel}"}, **extra)["id"]
        except SystemExit as e:
            last = e
            if "9004" not in str(e) and "2207052" not in str(e):
                raise
    raise last


def wait_ready(cid, tries=30):
    for _ in range(tries):
        r = call("GET", cid, fields="status_code,status")
        st = r["status_code"]
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            raise SystemExit(f"컨테이너 {cid} 상태 {st} {r.get('status', '')}")
        time.sleep(5)
    raise SystemExit(f"컨테이너 {cid} 준비 시간 초과")


def post(path, state_key="published", state_val=None):
    ep = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    no = ep["no"]
    slug = ep.get("slug") or f"{no:02d}"
    n = len(ep["slides"])
    base = os.environ["IMAGE_BASE"].rstrip("/")
    urls = [f"{base}/out/{slug}/golden_duck_lab_{slug}_{i:02d}.jpg" for i in range(1, n + 1)]
    caption = ep["caption"]
    caption_check.warn_only(path)  # 규칙 위반은 경고만 남기고 게시는 계속
    if os.environ.get("DRY_RUN"):
        print("DRY RUN", no, *urls, caption[:80], sep="\n")
        return
    uid = IG_USER_ID
    print("계정:", call("GET", uid, fields="username").get("username"))
    children = []
    for i in range(1, n + 1):
        c = create_media(uid, base, f"out/{slug}/golden_duck_lab_{slug}_{i:02d}.jpg", is_carousel_item="true")
        children.append(c)
    for c in children:
        wait_ready(c)
    car = call("POST", f"{uid}/media", media_type="CAROUSEL", children=",".join(children), caption=caption)["id"]
    wait_ready(car)
    res = call("POST", f"{uid}/media_publish", creation_id=car)
    print("게시 완료 media id:", res["id"])
    st = load_state()
    st.setdefault(state_key, []).append(state_val if state_val is not None else no)
    st.setdefault("log", []).append({"no": no, "slug": slug, "media_id": res["id"], "at": time.strftime("%Y-%m-%d %H:%M:%S")})
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=1))


def post_reel(path, state_val, repost=False):
    """out/<slug>/reel.mp4 를 릴스로 게시 (피드에도 함께 노출)."""
    ep = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    slug = ep.get("slug") or f"{ep['no']:02d}"
    base = os.environ["IMAGE_BASE"].rstrip("/")
    video = f"{base}/out/{slug}/reel.mp4"
    cover = f"{base}/out/{slug}/cover.jpg"
    has_cover = (ROOT / "out" / slug / "cover.jpg").exists()
    if not repost:
        caption_check.warn_only(path)
    if os.environ.get("DRY_RUN"):
        print("DRY RUN reel", video)
        return
    uid = IG_USER_ID
    extra = {"cover_url": f"out/{slug}/cover.jpg"} if has_cover else {"thumb_offset": "3500"}
    # CDN이 방금 올린 영상을 아직 못 줄 때가 있어(컨테이너 ERROR) 1분 간격으로 3번까지 다시 시도
    for attempt in range(3):
        cid = create_media(uid, base, f"out/{slug}/reel.mp4", media_type="REELS", caption=ep["caption"], share_to_feed="true", **extra)
        try:
            wait_ready(cid, tries=72)
            break
        except SystemExit as ex:
            print(f"::warning::릴스 준비 실패({attempt + 1}/3): {ex}")
            if attempt == 2:
                raise
            time.sleep(60)
    res = call("POST", f"{uid}/media_publish", creation_id=cid)
    print("릴스 게시 완료 media id:", res["id"])
    st = load_state()
    if not repost:
        key = ("income_reels" if slug.startswith("inc-") else "brief_published" if slug.startswith("brief-")
               else "toon_reels" if slug.startswith("toon-") else "quiz_published" if slug.startswith("quiz-") else "etf_reels")
        st.setdefault(key, []).append(state_val)
        if slug.startswith("quiz-"):
            st.setdefault("quiz_media", {})[res["id"]] = str(pathlib.Path(path))   # 댓글 DM 봇이 이 게시물의 정답을 찾는 표
        if slug.startswith("toon-") and state_val not in st.get("toon_published", []):
            st.setdefault("toon_published", []).append(state_val)   # 골든튠은 릴스가 본편
    st.setdefault("log", []).append({"no": ep["no"], "slug": slug, "type": "reel", "repost": repost, "media_id": res["id"], "at": time.strftime("%Y-%m-%d %H:%M:%S")})
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "next"
    if cmd == "reel":
        # reel <원고경로> <기록값>
        post_reel(sys.argv[2], sys.argv[3], repost=len(sys.argv) > 4 and sys.argv[4] == "repost")
        sys.exit(0)
    if cmd == "next":
        n = next_episode()
        print("" if n is None else n)
    elif cmd == "post":
        # post <편번호>  또는  post <원고경로> <state키> <기록값>
        a = sys.argv[2]
        if a.isdigit():
            post(ROOT / "episodes" / f"{int(a):02d}.json")
        else:
            post(a, sys.argv[3], sys.argv[4])
