"""20년 바둑판 원고 준비 → grid/ready/YYYY-MM.json
사용법: python grid/make_grid.py [YYYY-MM]   (없으면 한국 시간 기준 이번 달)
         python grid/make_grid.py check     → 오늘이 그달 첫째 월요일이면 first=1
"""
import datetime, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from grid.grid_reel import caption  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent
kst = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
arg = sys.argv[1] if len(sys.argv) > 1 else kst.strftime("%Y-%m")
if arg == "check":
    print(f"first={1 if kst.weekday() == 0 and kst.day <= 7 else 0}")
    sys.exit(0)
y, m = map(int, arg.split("-"))
ep = {"kind": "grid", "month": m, "year": y, "slug": f"grid-{y}-{m:02d}", "series": "20년 바둑판", "no": m}
ep["caption"] = caption(ep)
(ROOT / "ready").mkdir(exist_ok=True)
(ROOT / "ready" / f"{arg}.json").write_text(json.dumps(ep, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"path=grid/ready/{arg}.json")
print(f"slug={ep['slug']}")
print(f"val={arg}")
