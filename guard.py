"""게시 여부 판단: 같은 시리즈를 오늘 이미 올렸거나, 아직 게시 시간이 안 됐으면 건너뛴다.
GitHub 예약 실행은 늦거나 겹칠 수 있어 목표 시간 앞뒤로 여러 번 실행하고, 가장 먼저 조건을 만족한 실행만 올린다.
사용법: python guard.py brief|basic|income|etf|toon  -> 'skip=1' 또는 'skip=0' 출력

2026-11-11 일정 개편: 하루 최대 3개
  매일 07:00 경제 브리핑(일 = 이번 주 정리, 월 = 한 달 정리)
  월·수·금 10:00 골든튠(릴스) · 21:00 ETF
  화·목 12:10 기초 · 21:00 현금흐름 / 토 12:10 기초
"""
import json, os, sys, pathlib, datetime

TARGET = {"quiz": (19, 0), "brief": (7, 0), "basic": (12, 10), "income": (21, 0), "etf": (21, 0), "toon": (10, 0)}
# 게시 요일 (월=0 … 일=6). 여기에 없는 요일엔 예약 실행이 올리지 않아요(수동 실행은 요일 무시)
DAYS = {"quiz": {5, 6}, "brief": {0, 1, 2, 3, 4, 5, 6}, "basic": {1, 3, 5}, "income": {1, 3}, "etf": {0, 2, 4}, "toon": {0, 2, 4}}
LATE = {"brief": (10, 30)}   # 아침 브리핑은 이 시각이 지나면 그날은 건너뜀(예약 실행만)   # 한국 시간 게시 목표
EARLY = datetime.timedelta(minutes=15)                             # 목표보다 이만큼까지만 먼저 올려도 됨

kind = sys.argv[1]
st = pathlib.Path(__file__).parent / "state.json"
log = json.loads(st.read_text()).get("log", []) if st.exists() else []
now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(hours=9)  # KST
# 저녁 시리즈(etf·income)는 낮 12시를 하루의 경계로 봐요: 늦게 밀려 새벽에 올라간 편은 전날 저녁 몫
shift = datetime.timedelta(hours=12) if kind in ("etf", "income") else datetime.timedelta(0)
today = (now - shift).date()
skip = 0
for e in log:
    slug = str(e.get("slug", ""))
    k = ("brief" if slug.startswith("brief-") else "etf" if slug.startswith("etf-") else "income" if slug.startswith("inc-")
         else "toon" if slug.startswith("toon-") else "quiz" if slug.startswith("quiz-") else "basic")
    if (e.get("type") == "reel" and k not in ("brief", "toon")) or e.get("repost"):
        continue  # 릴스·재게시 기록은 하루 1편 계산에서 빼요(브리핑·골든튠은 릴스가 본편)
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
    if today.weekday() not in DAYS[kind]:
        skip = 1
    if kind in LATE and now > datetime.datetime.combine(today, datetime.time(*LATE[kind])):
        skip = 1
print(f"skip={skip}")
