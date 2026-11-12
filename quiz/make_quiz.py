"""황금알 퀴즈: 종목을 숨긴 릴스 원고 + 댓글·DM 문구를 만든다.
정답(종목)은 릴스·캡션 어디에도 쓰지 않고, 팔로우 확인 후 DM으로만 알려 준다.
사용법: python quiz/make_quiz.py next        (대기열 다음 퀴즈, '경로 티커' 출력)
       python quiz/make_quiz.py <티커> <번호>
"""
import json, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
KEYWORD = "정답"
DISC = "과거 수익률은 미래 수익을 보장하지 않아요 · 특정 종목 추천이 아닌 정보 제공 · 세금·수수료 미반영"


def won(v):
    v = int(v)
    if v >= 100_000_000:
        e, m = divmod(v, 100_000_000)
        m //= 10_000
        return f"{e}억 {m:,}만원" if m else f"{e}억원"
    return f"{v // 10_000:,}만원"


def load(t):
    d = json.loads((ROOT / "etf" / "results.json").read_text(encoding="utf-8"))
    return next(x for x in d["etfs"] if x["ticker"].upper() == t.upper())


def hints(e):
    us = e["market"] == "US"
    h = [f"{e['invests']}에 투자해요",
         f"{e['first_date'][:4]}년에 상장했어요",
         ("미국 증시에 상장된 ETF예요" if us else "한국 증시에 상장된 ETF예요")
         + (f" · 보수 연 {e['expense_ratio_pct']:.2f}%" if e.get("expense_ratio_pct") else "")]
    return h


def build(t, no):
    e = load(t)
    inv = e["invest10y_months"] * 100_000
    val = e["v10y_10"]
    asof = e["last_date"]
    ep = {
        "series": "황금알 퀴즈", "theme": "etf", "kind": "quiz", "no": no, "slug": f"quiz-{no:02d}",
        "ticker": e["ticker"], "keyword": KEYWORD, "asof": asof,
        "q": {"months": e["invest10y_months"], "invested": inv, "value": val, "ret": e["ret10y_pct"],
              "hints": hints(e), "category": e["category"]},
        "answer": {"ticker": e["ticker"], "name": e["name"], "desc": e["desc"], "invests": e["invests"]},
    }
    q = ep["q"]
    ep["caption"] = (
        f"월 10만원씩 10년, {won(inv)}이 {won(val)}이 된 ETF는? 🥚\n"
        f"정답이 궁금하면 댓글에 '{KEYWORD}'이라고 남겨 주세요.\n\n"
        "오늘의 황금알 퀴즈예요.\n\n"
        "✔ 힌트\n" + "\n".join(f"{i + 1}. {h}" for i, h in enumerate(q["hints"])) + "\n\n"
        f"✔ 결과\n넣은 돈 {won(inv)} → 지금 {won(val)} (수익률 {q['ret']:+.0f}%)\n\n"
        f"✔ 정답 받는 법\n1. @golden_duck_lab 팔로우\n2. 댓글에 '{KEYWORD}' 남기기\n→ 팔로우 확인 후 DM으로 정답을 보내드려요 📩\n\n"
        f"📌 {asof} 기준, 매달 같은 날 10만원씩 사고 배당은 다시 투자했다고 계산했어요"
        + (". 원달러 환율을 반영했어요" if e["market"] == "US" else "") + ". 세금·수수료는 빼지 않았어요.\n"
        "과거 수익률은 미래 수익을 보장하지 않으며, 특정 종목 추천이 아닌 정보 제공이에요.\n\n"
        "여러분이 생각하는 정답은 무엇인가요? 맞혀 보세요 👇\n\n"
        "🦆 골든덕랩은 매일 황금알 하나씩,\n기초부터 차근차근 돈 공부를 함께해요.\n\n"
        "💛 저장해두고 하나씩 따라 해보세요\n🐥 팔로우하면 매일 새 황금알이 도착해요\n\n"
        "#ETF #ETF투자 #적립식투자 #재테크퀴즈 #미국ETF #재테크 #골든덕랩")
    a = ep["answer"]
    ep["dm"] = {
        "comment_replies": ["DM 보내드렸어요 📩 확인해 주세요!", "정답 DM으로 보냈어요 🥚 메시지함 확인해 주세요!",
                            "보내드렸어요! 팔로우 확인 버튼만 눌러 주세요 🦆", "DM 확인해 주세요 📩 정답이 기다려요!",
                            "메시지 보냈어요 🥚 버튼 하나만 눌러 주시면 돼요!"],
        "first": ("댓글 고마워요 🥚 퀴즈 정답 바로 알려 드릴게요!\n"
                  "골든덕랩을 팔로우하신 분께만 보내드리고 있어요.\n"
                  "팔로우하셨다면 아래 버튼을 눌러 주세요 👇"),
        "button": "팔로우했어요, 정답 보기",
        "answer": (f"정답은 {a['ticker']} ({a['name']}) 예요 🎉\n"
                   f"{a['desc']}.\n"
                   f"월 10만원씩 10년, {won(q['invested'])}이 {won(q['value'])}이 됐어요 ({asof} 기준).\n"
                   "과거 수익률은 미래를 보장하지 않고, 특정 종목 추천이 아닌 정보예요.\n"
                   "다음 퀴즈도 맞혀 보실래요? 생각한 정답이 맞았는지 답장으로 알려 주세요 🦆"),
        "not_following": ("아직 팔로우가 확인되지 않았어요 🥲\n"
                          "@golden_duck_lab 팔로우 후 아래 버튼을 한 번 더 눌러 주세요!"),
    }
    dd = ROOT / "quiz" / "episodes"
    dd.mkdir(exist_ok=True)
    path = dd / f"{no:02d}.json"
    path.write_text(json.dumps(ep, ensure_ascii=False, indent=1), encoding="utf-8")
    (dd / f"{no:02d}_dm.txt").write_text(dm_sheet(ep), encoding="utf-8")
    return path


def dm_sheet(ep):
    d = ep["dm"]
    return (f"[황금알 퀴즈 #{ep['no']:02d} · 정답 {ep['ticker']}] 자동화 도구 세팅표\n\n"
            f"■ 키워드: {ep['keyword']}\n\n"
            "■ [댓글이 달리면] 자동 대댓글 (돌려쓰기)\n" + "\n".join(f"- {r}" for r in d["comment_replies"]) + "\n\n"
            f"■ [댓글 직후] 첫 DM\n{d['first']}\n(버튼: {d['button']})\n\n"
            f"■ [버튼 클릭 · 팔로우 확인됨] 정답 DM\n{d['answer']}\n\n"
            f"■ [버튼 클릭 · 팔로우 아님] 안내 DM\n{d['not_following']}\n")


def next_in_queue():
    st = json.loads((ROOT / "state.json").read_text()) if (ROOT / "state.json").exists() else {}
    done = st.get("quiz_published", [])
    queue = [l.split("#")[0].strip() for l in (ROOT / "quiz" / "queue.txt").read_text(encoding="utf-8").splitlines()]
    todo = [q for q in queue if q and q not in done]
    if not todo:
        print("")
        return
    path = build(todo[0], len(done) + 1)
    print(path.relative_to(ROOT), todo[0])


if __name__ == "__main__":
    if sys.argv[1] == "next":
        next_in_queue()
    else:
        print(build(sys.argv[1], int(sys.argv[2])))
