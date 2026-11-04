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


def wait_ready(cid, tries=30):
    for _ in range(tries):
        st = call("GET", cid, fields="status_code")["status_code"]
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            raise SystemExit(f"컨테이너 {cid} 상태 {st}")
        time.sleep(5)
    raise SystemExit(f"컨테이너 {cid} 준비 시간 초과")


def post(no):
    ep = json.loads((ROOT / "episodes" / f"{no:02d}.json").read_text(encoding="utf-8"))
    n = len(ep["slides"])
    base = os.environ["IMAGE_BASE"].rstrip("/")
    urls = [f"{base}/out/{no:02d}/golden_duck_lab_{no:02d}_{i:02d}.jpg" for i in range(1, n + 1)]
    caption = ep["caption"]
    if os.environ.get("DRY_RUN"):
        print("DRY RUN", no, *urls, caption[:80], sep="\n")
        return
    uid = IG_USER_ID
    print("계정:", call("GET", uid, fields="username").get("username"))
    children = []
    for u in urls:
        c = call("POST", f"{uid}/media", image_url=u, is_carousel_item="true")["id"]
        children.append(c)
    for c in children:
        wait_ready(c)
    car = call("POST", f"{uid}/media", media_type="CAROUSEL", children=",".join(children), caption=caption)["id"]
    wait_ready(car)
    res = call("POST", f"{uid}/media_publish", creation_id=car)
    print("게시 완료 media id:", res["id"])
    st = load_state()
    st["published"].append(no)
    st.setdefault("log", []).append({"no": no, "media_id": res["id"], "at": time.strftime("%Y-%m-%d %H:%M:%S")})
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "next"
    if cmd == "next":
        n = next_episode()
        print("" if n is None else n)
    elif cmd == "post":
        post(int(sys.argv[2]))
