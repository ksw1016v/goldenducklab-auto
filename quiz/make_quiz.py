"""황금알 퀴즈: 종목을 숨긴 릴스 원고 + 댓글·DM 문구를 만든다.
정답(종목)은 릴스·캡션 어디에도 쓰지 않고, 팔로우 확인 후 DM으로만 알려 준다.
사용법: python quiz/make_quiz.py next        (대기열 다음 퀴즈, '경로 티커' 출력)
       python quiz/make_quiz.py <티커> <번호>
"""
import json, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
KEYWORD = "골든덕"
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


REPLIES = ["DM으로 정답 보냈어요 📩 안 보이면 '메시지 요청함'을 확인해 주세요!",
           "정답 DM 보냈어요 🥚 메시지 요청함에 있을 수 있어요!",
           "보내드렸어요 📩 받은 편지함에 없으면 '요청'을 눌러 보세요!",
           "DM 확인해 주세요 🦆 요청함(숨겨진 요청 포함)도 한 번 봐 주세요!",
           "메시지 보냈어요 🥚 팔로우하시면 다음엔 받은 편지함으로 바로 가요!"]
HOWTO = (f"✔ 정답 받는 법\n1. @golden_duck_lab 팔로우\n2. 댓글에 '{KEYWORD}' 남기기\n→ DM으로 정답을 보내드려요 📩\n"
         "(팔로우하면 받은 편지함으로 바로 오고, 아니면 '메시지 요청함'으로 가요)\n\n")
OUTRO = ("여러분이 생각하는 정답은 무엇인가요? 맞혀 보세요 👇\n\n"
         "🦆 골든덕랩은 매일 황금알 하나씩,\n기초부터 차근차근 돈 공부를 함께해요.\n\n"
         "💛 저장해두고 하나씩 따라 해보세요\n🐥 팔로우하면 매일 새 황금알이 도착해요\n\n")


def fdate(d):
    return f"{d[:4]}.{int(d[5:7])}.{int(d[8:])}"


def save(ep):
    dd = ROOT / "quiz" / "episodes"
    dd.mkdir(exist_ok=True)
    path = dd / f"{ep['no']:02d}.json"
    path.write_text(json.dumps(ep, ensure_ascii=False, indent=1), encoding="utf-8")
    (dd / f"{ep['no']:02d}_dm.txt").write_text(dm_sheet(ep), encoding="utf-8")
    return path


def base(no, qtype, ticker, asof):
    return {"series": "황금알 퀴즈", "theme": "etf", "kind": "quiz", "qtype": qtype, "no": no, "slug": f"quiz-{no:02d}",
            "ticker": ticker, "keyword": KEYWORD, "asof": asof}


def build(spec, no):
    qtype, _, t = spec.partition(":") if ":" in spec else ("dca", "", spec)
    return {"dca": build_dca, "coffee": build_coffee, "trap": build_trap}[qtype](t, no)


def build_dca(t, no):
    e = load(t)
    inv = e["invest10y_months"] * 100_000
    val = e["v10y_10"]
    asof = e["last_date"]
    ep = base(no, "dca", e["ticker"], asof)
    ep["q"] = {"months": e["invest10y_months"], "invested": inv, "value": val, "ret": e["ret10y_pct"],
               "hints": hints(e), "category": e["category"]}
    ep["answer"] = {"ticker": e["ticker"], "name": e["name"], "desc": e["desc"], "invests": e["invests"]}
    q = ep["q"]
    ep["caption"] = (
        f"월 10만원씩 10년, {won(inv)}이 {won(val)}이 된 ETF는? 🥚\n"
        f"팔로우 후 댓글에 '{KEYWORD}' 남기면 정답 DM 📩\n\n"
        "오늘의 황금알 퀴즈예요.\n\n"
        "✔ 힌트\n" + "\n".join(f"{i + 1}. {h}" for i, h in enumerate(q["hints"])) + "\n\n"
        f"✔ 결과\n넣은 돈 {won(inv)} → 지금 {won(val)} (수익률 {q['ret']:+,.0f}%)\n\n" + HOWTO +
        f"📌 {asof} 기준, 매달 같은 날 10만원씩 사고 배당은 다시 투자했다고 계산했어요"
        + (". 원달러 환율을 반영했어요" if e["market"] == "US" else "") + ". 세금·수수료는 빼지 않았어요.\n"
        "과거 수익률은 미래 수익을 보장하지 않으며, 특정 종목 추천이 아닌 정보 제공이에요.\n\n" + OUTRO +
        "#ETF #ETF투자 #적립식투자 #재테크퀴즈 #미국ETF #재테크 #골든덕랩")
    ep["dm"] = {"comment_replies": REPLIES, "answer": answer_dm(ep, e)}
    return save(ep)


def build_coffee(t, no):
    """매일 커피 한 잔(5,000원) = 월 15만원 적립으로 10년"""
    e = load(t)
    k = 1.5                                   # 월 10만원 결과 × 1.5 = 월 15만원 (적립식은 금액에 비례)
    inv = int(e["invest10y_months"] * 150_000)
    val = int(e["v10y_10"] * k)
    asof = e["last_date"]
    ep = base(no, "coffee", e["ticker"], asof)
    ep["q"] = {"months": e["invest10y_months"], "invested": inv, "value": val, "ret": e["ret10y_pct"],
               "hints": hints(e), "category": e["category"], "daily": 5000, "monthly": 150_000}
    ep["answer"] = {"ticker": e["ticker"], "name": e["name"], "desc": e["desc"], "invests": e["invests"]}
    ep["caption"] = (
        f"매일 커피 한 잔 값을 10년 모았더니 {won(val)}? ☕\n"
        f"팔로우 후 댓글에 '{KEYWORD}' 남기면 정답 DM 📩\n\n"
        "오늘의 황금알 퀴즈예요.\n\n"
        "✔ 계산법\n하루 5,000원 × 30일 = 매달 15만원을 10년 동안 이 ETF에 넣었다면?\n\n"
        "✔ 힌트\n" + "\n".join(f"{i + 1}. {h}" for i, h in enumerate(ep["q"]["hints"])) + "\n\n"
        f"✔ 결과\n넣은 돈 {won(inv)} → 지금 {won(val)} (수익률 {e['ret10y_pct']:+,.0f}%)\n\n" + HOWTO +
        f"📌 {asof} 기준, 매달 같은 날 15만원씩 사고 배당은 다시 투자했다고 계산했어요"
        + (". 원달러 환율을 반영했어요" if e["market"] == "US" else "") + ". 세금·수수료는 빼지 않았어요.\n"
        "과거 수익률은 미래 수익을 보장하지 않으며, 특정 종목 추천이 아닌 정보 제공이에요.\n\n" + OUTRO +
        "#커피값 #ETF #적립식투자 #재테크퀴즈 #미국ETF #재테크 #골든덕랩")
    rows = []
    for y in (5, 10, 20):
        v, m = e.get(f"v{y}y_10"), e.get(f"invest{y}y_months")
        if v and m:
            rows.append(f"· {y}년: {won(m * 150_000)} → {won(v * k)} ({e[f'ret{y}y_pct']:+,.0f}%)")
    ep["dm"] = {"comment_replies": REPLIES, "answer": (
        f"☕ 황금알 퀴즈 #{no:02d} 정답 공개!\n\n"
        f"정답은 {e['ticker']} ({e['name']}) 예요 🎉\n\n"
        f"📌 어떤 ETF?\n{e['desc']}.\n{e['first_date'][:4]}년 상장"
        + (f" · 보수 연 {e['expense_ratio_pct']:.2f}%" if e.get("expense_ratio_pct") else "") + "\n\n"
        "☕ 매일 커피값(월 15만원)을 모았다면\n" + "\n".join(rows) + "\n\n"
        f"⚠️ 알아둘 점\n{RISK.get(e['category'], '한쪽에 몰린 상품일수록 오르내림이 커요')}.\n\n"
        f"※ {fdate(asof)} 기준 · 배당 재투자·환율 반영 · 세금·수수료 미반영 · 과거 수익률은 미래 수익을 보장하지 않아요 · 특정 종목 추천이 아닌 정보예요.\n\n"
        "생각하신 정답, 맞히셨나요? 답장으로 알려 주세요 🦆\n"
        "다음 퀴즈 정답도 받고 싶다면 @golden_duck_lab 팔로우해 두세요!")}
    return save(ep)


def build_trap(t, no):
    """월 100만원(세후) 배당을 가장 적은 원금으로? → 초고배당 ETF의 함정(원금 감소)"""
    d = json.loads((ROOT / "quiz" / "quiz_data.json").read_text(encoding="utf-8"))
    rows = [x for x in d["trap"] if x.get("need_krw") and x["years"] >= 1.5]
    anchor = next(x for x in rows if x["ticker"] == "SCHD")
    pick = min((x for x in rows if x["ticker"] != "SCHD"), key=lambda x: x["need_krw"]) if t in ("", "AUTO") else next(x for x in rows if x["ticker"] == t)
    asof = pick["last_date"]
    ep = base(no, "trap", pick["ticker"], asof)
    years = pick["years"]
    ep["q"] = {"need": pick["need_krw"], "anchor_need": anchor["need_krw"], "yield": pick["yield_pct"],
               "hints": [f"{pick['freq']} 배당을 줘요 (1년에 {pick['pay_count']}번)",
                         f"최근 1년 배당률이 연 {pick['yield_pct']:.0f}%예요",
                         f"상장한 지 {years:.0f}년 남짓 된 미국 ETF예요"],
               "price_chg": pick["price_chg_pct"], "price_chg_1y": pick["price_chg_1y_pct"], "total_ret": pick["total_ret_pct"]}
    ep["answer"] = {"ticker": pick["ticker"], "name": pick["name"]}
    q = ep["q"]
    ep["caption"] = (
        f"월 100만원 배당, 단 {won(q['need'])}으로 가능하다고? 💸\n"
        f"팔로우 후 댓글에 '{KEYWORD}' 남기면 정답 DM 📩\n\n"
        "오늘의 황금알 퀴즈예요. 이번엔 함정이 있어요 ⚠️\n\n"
        f"✔ 비교\n매달 세후 100만원을 받으려면\nSCHD는 약 {won(q['anchor_need'])}, 이 ETF는 약 {won(q['need'])}\n\n"
        "✔ 힌트\n" + "\n".join(f"{i + 1}. {h}" for i, h in enumerate(q["hints"])) + "\n\n"
        "✔ 함정은 무엇일까?\n정답 DM에서 이 ETF의 '원금'이 어떻게 됐는지 함께 알려드려요.\n\n" + HOWTO +
        f"📌 {asof} 기준, 최근 1년 배당이 그대로라고 가정하고 배당소득세 15.4%를 뺀 금액으로 계산했어요. 원달러 {d['fx']:,.0f}원 기준이에요.\n"
        "배당은 확정된 금액이 아니고, 과거 수익률은 미래 수익을 보장하지 않으며, 특정 종목 추천이 아닌 정보 제공이에요.\n\n" + OUTRO +
        "#배당 #고배당 #월배당 #재테크퀴즈 #미국ETF #재테크 #골든덕랩")
    ep["dm"] = {"comment_replies": REPLIES, "answer": (
        f"💸 황금알 퀴즈 #{no:02d} 정답 공개!\n\n"
        f"정답은 {pick['ticker']} ({pick['name']}) 예요.\n\n"
        f"📌 왜 원금이 적게 들까?\n최근 1년 배당률이 연 {q['yield']:.0f}%라서, 계산상 약 {won(q['need'])}이면 매달 세후 100만원이 나와요. (SCHD는 약 {won(q['anchor_need'])})\n\n"
        "⚠️ 함정은 바로 '원금'\n"
        f"· 상장 후 주가: {q['price_chg']:+.0f}%\n"
        + (f"· 최근 1년 주가: {q['price_chg_1y']:+.0f}%\n" if q.get("price_chg_1y") is not None else "")
        + f"· 배당을 다 합친 총수익: {q['total_ret']:+.0f}%\n"
        "배당을 많이 주는 만큼 주가가 계속 내려가서, 1년 뒤에는 같은 배당을 받기 어려울 수 있어요. 배당률만 보고 고르면 위험한 이유예요.\n\n"
        f"※ {fdate(asof)} 기준 · 세금 15.4% 반영 · 배당은 확정 금액이 아님 · 과거 수익률은 미래 수익을 보장하지 않아요 · 특정 종목 추천이 아닌 정보예요.\n\n"
        "생각하신 정답, 맞히셨나요? 답장으로 알려 주세요 🦆\n"
        "다음 퀴즈 정답도 받고 싶다면 @golden_duck_lab 팔로우해 두세요!")}
    return save(ep)


RISK = {
    "기술·성장": "기술주에 몰려 있어 오를 때도 크게, 내릴 때도 크게 움직여요",
    "섹터": "한 업종에 몰려 있어 그 업종 경기에 따라 크게 흔들릴 수 있어요",
    "국가": "한 나라에 몰려 있어 그 나라 경기와 환율에 크게 영향을 받아요",
    "미국 대표지수": "넓게 나눠 담았지만 미국 시장 전체가 내리면 함께 내려요",
}


def answer_dm(ep, e):
    q = ep["q"]
    rows = []
    for y in (5, 10, 20):
        v = e.get(f"v{y}y_10")
        m = e.get(f"invest{y}y_months")
        if v and m:
            rows.append(f"· {y}년: {won(m * 100_000)} → {won(v)} ({e[f'ret{y}y_pct']:+,.0f}%)")
    fee = f" · 보수 연 {e['expense_ratio_pct']:.2f}%" if e.get("expense_ratio_pct") else ""
    d = ep["asof"]
    return (f"🥚 황금알 퀴즈 #{ep['no']:02d} 정답 공개!\n\n"
            f"정답은 {e['ticker']} ({e['name']}) 예요 🎉\n\n"
            f"📌 어떤 ETF?\n{e['desc']}.\n{e['first_date'][:4]}년 상장{fee}\n\n"
            "📈 월 10만원씩 모았다면 (배당 재투자·환율 반영)\n" + "\n".join(rows) + "\n\n"
            f"⚠️ 알아둘 점\n{RISK.get(e['category'], '한쪽에 몰린 상품일수록 오르내림이 커요')}.\n\n"
            f"※ {d[:4]}.{int(d[5:7])}.{int(d[8:])} 기준 · 세금·수수료 미반영 · 과거 수익률은 미래 수익을 보장하지 않아요 · 특정 종목 추천이 아닌 정보예요.\n\n"
            "생각하신 정답, 맞히셨나요? 답장으로 알려 주세요 🦆\n"
            "다음 퀴즈 정답도 받고 싶다면 @golden_duck_lab 팔로우해 두세요!")


def dm_sheet(ep):
    d = ep["dm"]
    return (f"[황금알 퀴즈 #{ep['no']:02d} · {ep.get('qtype', 'dca')} · 정답 {ep['ticker']}] 자동 대댓글·DM 문구\n\n"
            f"■ 키워드: {ep['keyword']}\n\n"
            "■ 자동 대댓글 (돌려쓰기)\n" + "\n".join(f"- {r}" for r in d["comment_replies"]) + "\n\n"
            f"■ 정답 DM\n{d['answer']}\n")


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
