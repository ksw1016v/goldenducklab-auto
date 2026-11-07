"""게시 여부 판단: 같은 시리즈를 오늘 이미 올렸거나, 아직 게시 시간이 안 됐으면 건너뛴다.
GitHub 예약 실행은 늦거나 겹칠 수 있어 목표 시간 앞뒤로 여러 번 실행하고, 가장 먼저 조건을 만족한 실행만 올린다.
사용법: python guard.py basic|income|etf  -> 'skip=1' 또는 'skip=0' 출력
"""
import json, os, sys, pathlib, datetime

TARGET = {"brief": (7, 0), "basic": (9, 0), "income": (12, 10), "etf": (21, 0)}
LATE = {"brief": (10, 30)}   # 아침 브리핑은 이 시각이 지나면 그날은 건너뜀(예약 실행만)   # 한국 시간 게시 목표
EARLY = datetime.timedelta(minutes=15)                             # 목표보다 이만큼까지만 먼저 올려도 됨

kind = sys.argv[1]
st = pathlib.Path(__file__).parent / "state.json"
log = json.loads(st.read_text()).get("log", []) if st.exists() else []
now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(hours=9)  # KST
# 저녁 시리즈(etf)는 낮 12시를 하루의 경계로 봐요: 늦게 밀려 새벽에 올라간 편은 전날 저녁 몫
shift = datetime.timedelta(hours=12) if kind == "etf" else datetime.timedelta(0)
today = (now - shift).date()
skip = 0
for e in log:
    slug = str(e.get("slug", ""))
    k = "brief" if slug.startswith("brief-") else ("etf" if slug.startswith("etf-") else ("income" if slug.startswith("inc-") else "basic"))
    if (e.get("type") == "reel" and k != "brief") or e.get("repost"):
        continue  # 릴스·재게시 기록은 하루 1편 계산에서 빼요(브리핑은 릴스가 본편)
    if k != kind:
        continue
    at = datetime.datetime.strptime(e["at"], "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=9)
    if (at - shift).date() == today:
        skip = 1
# 아직 게시 시간이 안 됐으면 건너뜀 (수동 실행은 예외)
if os.environ.get("GITHUB_EVENT_NAME") != "workflow_dispatch":
    h, m = TARGET[kind]
    start = datetime.datetime.combine(today, datetime.time(h, m)) - EARLY
    if now < start:
        skip = 1
    if kind in LATE and now > datetime.datetime.combine(today, datetime.time(*LATE[kind])):
        skip = 1
print(f"skip={skip}")
