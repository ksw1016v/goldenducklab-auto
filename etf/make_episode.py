"""results.json의 ETF 하나로 카드뉴스 원고(episodes/NN.json)를 만든다.
사용법: python etf/make_episode.py next   (대기열 다음 ETF)
       python etf/make_episode.py <티커> <편번호> [다음편제목]
"""
import json, datetime, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DISC = "과거 수익률은 미래 수익을 보장하지 않아요 · 분배금 재투자, 세금·수수료 미반영 · 특정 종목 추천이 아닌 정보 제공"

NOTES = {
    "레버리지": [["하루 수익률의 배수를 추구", "오래 보유하면 지수 수익률의 배수와 달라질 수 있어요"], ["하락장에선 손실도 몇 배", "짧은 기간에 큰 손실이 날 수 있어요"], ["초보 장기투자용으론 주의", "구조를 충분히 이해한 뒤 판단하세요"]],
    "인버스": [["지수가 내려야 수익", "장기적으로 시장이 오르면 손실이 커져요"], ["하루 수익률 기준 상품", "오래 보유하면 기대와 다를 수 있어요"], ["단기 대응용 성격", "장기 적립식과는 맞지 않을 수 있어요"]],
    "채권": [["금리가 오르면 가격 하락", "만기가 길수록 금리 영향이 커요"], ["주식과 다르게 움직이는 경우가 많음", "분산 투자 재료로 많이 쓰여요"], ["분배금은 이자 성격", "세금 처리를 미리 확인하세요"]],
    "원자재": [["실물·선물 가격을 따라가요", "기업 이익이 아니라 원자재 가격이 수익의 원천"], ["선물형은 교체 비용 발생", "장기 수익률이 현물과 달라질 수 있어요"], ["인플레이션 시기에 주목받는 자산", "변동성이 큰 편이에요"]],
}
DEFAULT = [["한 번에 여러 종목에 분산", "개별 종목보다 위험이 나뉘어요"], ["총보수는 매일 조금씩 빠져요", "같은 지수라면 보수가 낮은 쪽이 유리해요"], ["시장이 내리면 함께 내려요", "적립식은 오래·꾸준히가 핵심이에요"]]
US_NOTE = ["환율도 수익에 영향", "원화로 투자하면 달러 가치 변화가 함께 반영돼요"]


def won(v):
    if v == "" or v is None:
        return None
    v = int(v)
    if v >= 100_000_000:
        eok, man = divmod(v, 100_000_000)
        man //= 10_000
        return f"{eok}억 {man:,}만원" if man else f"{eok}억원"
    return f"{v // 10_000:,}만원"


def build(t, no, nxt):
    data = json.loads((ROOT / "etf" / "results.json").read_text(encoding="utf-8"))
    e = next(x for x in data["etfs"] if x["ticker"].upper() == t.upper())
    asof = e["last_date"]
    us = e["market"] == "US"
    code = e["ticker"] if us else f"{e['ticker']}"
    rows = [["투자 대상", e["invests"]], ["상장일", e["first_date"][:7].replace("-", ".")]]
    if e.get("expense_ratio_pct") not in ("", None):
        rows.append(["총보수(연)", f"{e['expense_ratio_pct']}%"])
    rows.append(["거래 시장", "미국 증시 (달러)" if us else "한국거래소 (원화)"])

    def dca(amt):
        out = []
        for y in (20, 10, 5):
            v = e.get(f"v{y}y_{amt}")
            if v in ("", None):
                out.append([f"{y}년", "-", "계산 불가", ""])
                continue
            months = e[f"invest{y}y_months"]
            out.append([f"{y}년", won(amt * 10_000 * months), won(v), f"{e[f'ret{y}y_pct']:+.0f}%"])
        return out

    longest = next((y for y in (20, 10, 5) if e.get(f"v{y}y_10") not in ("", None)), None)
    title_name = e["ticker"] if us else e["name"]
    cover_name = e["ticker"] if us else e["name"].replace(" ", "<br>", 1)
    hook = f"월 10만원씩<br>{longest}년 모았다면?" if longest else "이제 막 상장한 ETF"
    notes = NOTES.get(e["category"], DEFAULT)[:]
    if us:
        notes = notes[:2] + [US_NOTE]

    slides = [
        {"type": "cover", "kicker": f"ETF 황금알 · {e['category']}", "title": f"<mark>{cover_name}</mark><br>{hook}", "sub": f"{e['invests']}에 투자하는 ETF<br>{asof[:4]}.{asof[5:7]} 기준 숫자로 알아봐요"},
        {"type": "etf_info", "ticker": e["ticker"], "name": e["name"], "category": e["category"], "desc": e["desc"], "rows": rows},
    ]
    for amt in (10, 30, 50):
        slides.append({"type": "dca", "title": f"매달 <mark>{amt}만원씩</mark><br>모았다면 지금은?", "rows": dca(amt), "note": DISC + f" · {asof} 기준"})
    slides.append({"type": "list", "title": f"{title_name}<br><mark>알아둘 점</mark>", "items": notes})
    best = e.get(f"v{longest}y_50") if longest else None
    slides.append({"type": "list", "title": "오늘의 <mark>황금알</mark> 요약", "items": [[f"{e['invests']}에 분산투자", ""], [f"월 50만원 {longest}년 → {won(best)}" if best else "아직 장기 기록이 짧아요", ""], ["숫자보다 꾸준함이 핵심", ""]], "tip": "과거 수익률은 <mark>미래를 보장하지 않아요</mark>"})
    slides.append({"type": "end", "title": "오늘의 황금알,<br>저장해 두세요", "sub": "매일 새 황금알 하나씩", "cta": "@golden_duck_lab 팔로우", "next": f"다음 편 예고 · {nxt}" if nxt else "다음 ETF도 기대해 주세요"})

    def line(amt):
        parts = []
        for y in (20, 10, 5):
            v = e.get(f"v{y}y_{amt}")
            if v not in ("", None):
                parts.append(f"{y}년 → {won(v)}")
        return " / ".join(parts) or "상장 기간이 짧아 계산 불가"

    cap = (f"{title_name}, 매달 꾸준히 모았다면 지금 얼마일까요? 🥚\n{e['desc']}.\n\n"
           f"오늘의 황금알은 'ETF {e['ticker']}'예요.\n\n"
           f"✔ 어디에 투자?\n{e['invests']}\n\n"
           f"✔ 월 10만원씩\n{line(10)}\n\n✔ 월 30만원씩\n{line(30)}\n\n✔ 월 50만원씩\n{line(50)}\n\n"
           f"📌 {asof} 기준, 매달 첫 거래일 적립·분배금 재투자 가정"
           + (", 원달러 환율 반영" if us else "") + ". 세금·수수료는 빼지 않았어요.\n"
           "과거 수익률은 미래 수익을 보장하지 않으며, 특정 종목 추천이 아닌 정보 제공이에요.\n\n"
           "여러분이 모으고 있는 ETF는 무엇인가요? 댓글로 알려주세요 👇\n\n"
           "🦆 골든덕랩은 매일 황금알 하나씩,\n기초부터 차근차근 돈 공부를 함께해요.\n\n"
           "💛 저장해두고 하나씩 따라 해보세요\n🐥 팔로우하면 매일 새 황금알이 도착해요\n\n"
           f"다음 편 예고 ▶ {nxt or '다음 ETF'}\n\n"
           f"#ETF #ETF투자 #{e['ticker'] if us else e['name'].replace(' ', '').replace('(', '').replace(')', '')} #적립식투자 #재테크 #돈공부 #골든덕랩")
    ep = {"series": "ETF 황금알", "theme": "etf", "no": no, "slug": f"etf-{no:02d}", "ticker": e["ticker"], "slides": slides, "caption": cap}
    d = ROOT / "etf" / "episodes"
    d.mkdir(exist_ok=True)
    path = d / f"{no:02d}.json"
    path.write_text(json.dumps(ep, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def label(e):
    return e["ticker"] if e["market"] == "US" else e["name"]


def hook_title(t):
    data = json.loads((ROOT / "etf" / "results.json").read_text(encoding="utf-8"))
    e = next(x for x in data["etfs"] if x["ticker"].upper() == t.upper())
    y = next((y for y in (20, 10, 5) if e.get(f"v{y}y_10") not in ("", None)), None)
    return f"{label(e)} 월 10만원씩 {y}년 모았다면?"


def specials(done):
    """etf/specials.txt: '<파일> <YYYY-MM-DD(이 날부터 게시)>' · 아직 안 올린 특별편 목록"""
    f = ROOT / "etf" / "specials.txt"
    out = []
    if f.exists():
        for l in f.read_text(encoding="utf-8").splitlines():
            l = l.split("#")[0].split()
            if len(l) >= 2:
                ep = json.loads((ROOT / "etf" / "specials" / l[0]).read_text(encoding="utf-8"))
                if ep["special_id"] not in done:
                    out.append((datetime.date.fromisoformat(l[1]), ep))
    return out


def build_special(ep, no, nxt):
    ep = json.loads(json.dumps(ep))
    ep["no"], ep["slug"] = no, f"etf-{no:02d}"
    for s in ep["slides"]:
        if s.get("next") == "{{NEXT}}":
            s["next"] = f"다음 편 예고 · {nxt}" if nxt else "다음 ETF편도 기대해 주세요"
    ep["caption"] = ep["caption"].replace("{{NEXT}}", nxt or "다음 ETF편")
    path = ROOT / "etf" / "episodes" / f"{no:02d}.json"
    path.write_text(json.dumps(ep, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def next_in_queue():
    """대기열에서 다음 ETF로 원고를 만들고 '경로 티커'를 출력. 없으면 빈 줄. 게시일이 된 특별편이 있으면 먼저."""
    st = json.loads((ROOT / "state.json").read_text()) if (ROOT / "state.json").exists() else {}
    done = st.get("etf_published", [])
    queue = [l.split("#")[0].strip() for l in (ROOT / "etf" / "queue.txt").read_text(encoding="utf-8").splitlines()]
    queue = [q for q in queue if q]
    todo = [q for q in queue if q not in done]
    today = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=9)).date()
    sp = specials(done)
    due = [ep for d, ep in sp if d <= today]
    if due:
        path = build_special(due[0], len(done) + 1, hook_title(todo[0]) if todo else "")
        print(path.relative_to(ROOT), due[0]["special_id"])
        return
    if not todo:
        print("")
        return
    tomorrow = [ep for d, ep in sp if d <= today + datetime.timedelta(days=1)]
    nxt = tomorrow[0]["teaser"] if tomorrow else (hook_title(todo[1]) if len(todo) > 1 else "")
    path = build(todo[0], len(done) + 1, nxt)
    print(path.relative_to(ROOT), todo[0])


if __name__ == "__main__":
    if sys.argv[1] == "next":
        next_in_queue()
    else:
        print(build(sys.argv[1], int(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else ""))
