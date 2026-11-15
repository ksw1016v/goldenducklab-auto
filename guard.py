"""게시 여부 판단: 같은 시리즈를 오늘 이미 올렸거나, 아직 게시 시간이 안 됐으면 건너뛴다.
GitHub 예약 실행은 늦거나 겹칠 수 있어 목표 시간 앞뒤로 여러 번 실행하고, 가장 먼저 조건을 만족한 실행만 올린다.
사용법: python guard.py brief|basic|income|etf|toon  -> 'skip=1' 또는 'skip=0' 출력

2026-11-15 일정 (성과 분석 반영): 모든 시리즈 릴스가 본편, ETF는 다시 매일
  매일 07:00 경제 브리핑(일 = 이번 주 정리, 월 = 한 달 정리) · 매일 21:00 ETF
  월·수·금 10:00 골든튠 · 화·목·토 12:10 기초 · 화·목 21:00 현금흐름(ETF 뒤에 이어서)

2026-11-15 오후 개편 (잘되는 계정 비교 분석: 정보 요약은 바닥, 사람 이야기·감정이 터짐 → 양을 줄이고 이야기형으로)
  매일 21:00 ETF 적립 릴스(유지) · 화·금 12:10 골든에그의 월급일기(새 이야기 시리즈)
  목 21:20 현금흐름 · 일 19:00 선물형(퀴즈는 중단) · 경제 브리핑은 큰 날·일요일만(econ/bigday.py)
  기초편·예전 골든튠은 월급일기로 대체해 중단
"""
import json, os, sys, pathlib, datetime

TARGET = {"quiz": (19, 0), "brief": (7, 0), "basic": (12, 10), "income": (21, 20), "etf": (21, 0), "toon": (10, 0), "story": (12, 10)}
# 게시 요일 (월=0 … 일=6). 여기에 없는 요일엔 예약 실행이 올리지 않아요(수동 실행은 요일 무시)
DAYS = {"quiz": {6}, "brief": {0, 1, 2, 3, 4, 5, 6}, "basic": set(), "income": {3}, "etf": {0, 1, 2, 3, 4, 5, 6}, "toon": set(), "story": {1, 4}}
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
         else "toon" if slug.startswith("toon-") else "quiz" if slug.startswith("quiz-") else "story" if slug.startswith("story-") else "basic")
    if e.get("repost"):
        continue  # 재게시 기록은 하루 1편 계산에서 빼요(2026-11-15부터 모든 시리즈 릴스가 본편이라 릴스도 셈)
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
