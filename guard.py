"""같은 시리즈를 12시간 안에 이미 올렸으면 건너뛴다 (GitHub 예약 실행이 늦거나 겹칠 때 중복 게시 방지).
사용법: python guard.py basic|etf  -> 'skip=1' 또는 'skip=0' 출력
"""
import json, sys, pathlib, datetime

kind = sys.argv[1]
st = pathlib.Path(__file__).parent / "state.json"
log = json.loads(st.read_text()).get("log", []) if st.exists() else []
now = datetime.datetime.utcnow()
skip = 0
for e in log:
    is_etf = str(e.get("slug", "")).startswith("etf-")
    if (kind == "etf") != is_etf:
        continue
    at = datetime.datetime.strptime(e["at"], "%Y-%m-%d %H:%M:%S")
    if now - at < datetime.timedelta(hours=12):
        skip = 1
print(f"skip={skip}")
