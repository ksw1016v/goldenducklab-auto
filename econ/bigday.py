"""브리핑을 올릴 만한 날인지 판단 (2026-11-15 성과 분석: 매일 정보 요약은 도달이 바닥 → 큰 날만).
올림: 일요일(한 주 정리) · 코스피/코스닥/S&P500/나스닥 중 하나라도 ±2% 이상 · 원/달러 ±1% 이상
종료 코드 0 = 올림, 1 = 건너뜀
"""
import json, sys, pathlib, datetime
d = json.loads((pathlib.Path(__file__).parent / "data.json").read_text())["markets"]
kst = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
why = []
if kst.weekday() == 6:
    why.append("일요일 한 주 정리")
for k in ("kospi", "kosdaq", "spx", "ndx"):
    if k in d and abs(d[k].get("pct") or 0) >= 2:
        why.append(f"{d[k]['name']} {d[k]['pct']:+.1f}%")
if "usdkrw" in d and abs(d["usdkrw"].get("pct") or 0) >= 1:
    why.append(f"원/달러 {d['usdkrw']['pct']:+.1f}%")
print("큰 날:", ", ".join(why) if why else "없음")
sys.exit(0 if why else 1)
