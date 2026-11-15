"""월급일기 다음 편 준비: 자리표시자를 실제 숫자로 바꿔 story/ready/NN.json 에 쓴다.
사용법: python story/make_story.py next   → 'path=story/ready/NN.json' 'no=NN' 출력(없으면 아무것도 안 함)
        python story/make_story.py 02
"""
import json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from story.story_reel import resolve  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent
arg = sys.argv[1]
if arg == "next":
    st = json.loads((ROOT.parent / "state.json").read_text())
    done = set(st.get("story_published", []))
    todo = [l.strip() for l in (ROOT / "queue.txt").read_text().splitlines() if l.strip() and not l.startswith("#") and l.strip() not in done]
    if not todo:
        sys.exit(0)
    arg = todo[0]
ep = json.loads((ROOT / f"{arg}.json").read_text(encoding="utf-8"))
ep["caption"] = resolve(ep["caption"])
ep["cover"] = {k: resolve(v) if isinstance(v, str) else v for k, v in ep["cover"].items()}
(ROOT / "ready").mkdir(exist_ok=True)
out = ROOT / "ready" / f"{arg}.json"
out.write_text(json.dumps(ep, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"path=story/ready/{arg}.json")
print(f"no={arg}")
