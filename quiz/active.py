"""최근 3일 안에 올린 퀴즈가 있으면 1, 없으면 0 출력 (DM 확인 반복 여부 판단)"""
import json, datetime, pathlib
st = json.loads((pathlib.Path(__file__).resolve().parent.parent / "state.json").read_text())
now = datetime.datetime.utcnow()
act = [e for e in st.get("log", []) if str(e.get("slug", "")).startswith("quiz-")
       and now - datetime.datetime.strptime(e["at"], "%Y-%m-%d %H:%M:%S") < datetime.timedelta(days=3)]
print(1 if act else 0)
