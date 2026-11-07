"""income.json 의 ETF 하나로 '현금흐름 황금알' 카드뉴스 원고를 만든다.
사용법: python etf/make_income.py next        (대기열 다음 편, '경로 티커' 출력)
       python etf/make_income.py <티커> <편번호> [다음편제목]
"""
import json, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DISC = "배당은 확정된 금액이 아니고 바뀔 수 있어요 · 최근 1년 배당 기준, 세금·수수료 미반영 · 특정 종목 추천이 아닌 정보 제공"

NOTES = {
    "배당·커버드콜": [["분배금이 높은 대신 상승이 제한돼요", "옵션을 팔아 받은 돈을 나눠 주는 구조라 주가가 크게 올라도 다 따라가지 못해요"],
                  ["분배금은 매달 달라져요", "시장 변동성에 따라 늘었다 줄었다 해요"]],
    "채권": [["금리가 오르면 가격이 내려가요", "만기가 길수록 금리 영향이 커요"],
           ["이자 성격의 분배금", "주식보다 변동은 작지만 성장도 작아요"]],
    "섹터": [["한 업종에 집중된 상품", "업종 경기에 따라 배당과 가격이 함께 흔들릴 수 있어요"],
           ["배당이 꾸준한 업종 위주", "대신 성장 속도는 느릴 수 있어요"]],
}
DEFAULT = [["배당은 회사 이익에서 나와요", "경기가 나빠지면 배당이 줄 수도 있어요"],
           ["수익률이 높을수록 좋은 건 아니에요", "주가가 떨어져서 수익률이 높아 보일 때도 있어요"]]
TAX_US = ["세금도 미리 알아두기", "해외 ETF 배당은 현지에서 15% 떼고 들어오고, 금융소득이 연 2,000만원을 넘으면 종합과세 대상이에요"]
TAX_KR = ["세금도 미리 알아두기", "분배금에서 15.4%를 떼고 들어오고, 금융소득이 연 2,000만원을 넘으면 종합과세 대상이에요"]


def won(v):
    if v in ("", None):
        return "-"
    v = int(v)
    if v >= 100_000_000:
        e, m = divmod(v, 100_000_000)
        m //= 10_000
        return f"{e}억 {m:,}만원" if m else f"{e}억원"
    return f"{v // 10_000:,}만원"


def label(e):
    return e["ticker"] if e["market"] == "US" else e["name"]


def load(t):
    d = json.loads((ROOT / "etf" / "income.json").read_text(encoding="utf-8"))
    return d, next(x for x in d["etfs"] if x["ticker"].upper() == t.upper())


def dps(e, v):
    return f"${v:.2f}" if e["market"] == "US" else f"{v:,.0f}원"


def build(t, no, nxt):
    d, e = load(t)
    us = e["market"] == "US"
    asof = e["last_date"]
    name = label(e)
    cover_name = e["ticker"] if us else e["name"].replace(" ", "<br>", 1)
    y = e["yield_pct"]
    years = e["dca_months"] // 12
    period = f"{years}년" if e["dca_months"] % 12 == 0 else f"{e['dca_months']}개월"
    growth = e.get("div_growth_5y_pct")

    rows = [["투자 대상", e["invests"]], ["배당수익률", f"연 {y:.1f}% (최근 1년)"], ["배당 주기", e["freq"]]]
    if growth is not None:
        rows.append(["5년 배당 성장", f"{growth:+.0f}%"])
    rows.append(["거래 시장", "미국 증시 (달러)" if us else "한국거래소 (원화)"])

    need_rows = [[f"월{a}만", f"매달 {a}만원 받으려면", won(e[f"need_{a}"]), ""] for a in (50, 100, 300)]
    story_rows = [[period, f"월 50만원씩 · 넣은 돈 {won(e['dca_invested'])}", won(e["dca_value"]), ""],
                  ["매달", "지금 받는 배당 (세전)", f"월 {won(e['dca_monthly_income'])}", ""]]

    if growth is not None:
        gitems = [[f"5년 전 1년 배당 {dps(e, e['div_5y_ago'])}", ""], [f"최근 1년 배당 {dps(e, e['ttm_div'])}", ""],
                  [f"주당 배당이 {growth:+.0f}% 변했어요", "같은 1주를 갖고 있어도 받는 돈이 달라져요"]]
        gtitle = "배당은<br><mark>늘어났을까?</mark>"
        gtip = "배당이 꾸준히 늘면 같은 원금으로 받는 현금흐름도 커져요"
    else:
        gitems = [[f"상장 {e['first_date'][:4]}년, 아직 기록이 짧아요", "5년 비교는 기록이 쌓이면 다시 볼게요"],
                  [f"최근 1년 배당 {dps(e, e['ttm_div'])}", f"1년에 {e['pay_count']}번 나눠 받았어요"],
                  ["짧은 기록만 보고 판단하지 않기", "시장 상황이 바뀌면 배당도 달라져요"]]
        gtitle = "배당<br><mark>기록 보기</mark>"
        gtip = None

    notes = NOTES.get(e["category"], DEFAULT)[:] + [TAX_US if us else TAX_KR]
    slides = [
        {"type": "cover", "kicker": f"현금흐름 황금알 · {e['freq']} 배당", "title": f"<mark>{cover_name}</mark>로<br>월 100만원<br>받으려면?",
         "sub": f"배당수익률 연 {y:.1f}%로<br>{asof[:4]}.{asof[5:7]} 기준 계산해 봐요"},
        {"type": "etf_info", "ticker": e["ticker"], "name": e["name"], "category": e["category"], "desc": e["desc"], "rows": rows},
        {"type": "need", "title": "매달 <mark>이만큼</mark> 받으려면<br>얼마가 필요할까?", "rows": need_rows,
         "note": DISC + f" · {asof} 기준"},
        {"type": "need", "title": f"월 50만원씩<br><mark>{period}</mark> 모았다면?", "rows": story_rows,
         "tip": "모으는 동안 받은 분배금은 다시 투자했다고 계산했어요", "note": DISC + f" · {asof} 기준"},
        {"type": "list", "title": gtitle, "items": gitems, **({"tip": gtip} if gtip else {})},
        {"type": "list", "title": f"{name}<br><mark>알아둘 점</mark>", "items": notes},
        {"type": "list", "title": "오늘의 <mark>황금알</mark> 요약",
         "items": [[f"배당수익률 연 {y:.1f}%, {e['freq']} 지급", ""], [f"월 100만원엔 약 {won(e['need_100'])} 필요", ""], ["현금흐름은 꾸준히 쌓는 것", ""]],
         "tip": "과거 배당이 <mark>미래 배당을 보장하지 않아요</mark>"},
        {"type": "end", "title": "오늘의 황금알,<br>저장해 두세요", "sub": "매일 아침 9시 · 점심 12시 · 저녁 7시 새 황금알",
         "cta": "@golden_duck_lab 팔로우", "next": f"다음 편 예고 · {nxt}" if nxt else "다음 현금흐름편도 기대해 주세요"},
    ]
    tag = e["ticker"] if us else e["name"].replace(" ", "").replace("(", "").replace(")", "")
    cap = (f"{name}로 매달 100만원 받으려면 얼마가 필요할까요? 🥚\n{e['desc']}.\n\n"
           f"오늘의 황금알은 '현금흐름 만들기 · {e['ticker']}'예요.\n\n"
           f"✔ 배당 정보\n연 {y:.1f}% (최근 1년) · {e['freq']} 지급"
           + (f" · 5년 배당 {growth:+.0f}%" if growth is not None else "") + "\n\n"
           f"✔ 필요한 원금 (세전)\n월 50만원 → {won(e['need_50'])}\n월 100만원 → {won(e['need_100'])}\n월 300만원 → {won(e['need_300'])}\n\n"
           f"✔ 월 50만원씩 {period} 모았다면\n지금 {won(e['dca_value'])}, 매달 배당 약 {won(e['dca_monthly_income'])}\n\n"
           f"📌 {asof} 기준, 최근 1년 배당이 그대로라고 가정한 계산이에요"
           + (", 원달러 환율 반영" if us else "") + ". 세금·수수료는 빼지 않았어요.\n"
           "배당은 확정된 금액이 아니며, 특정 종목 추천이 아닌 정보 제공이에요.\n\n"
           "여러분은 매달 얼마의 현금흐름을 만들고 싶으세요? 댓글로 알려주세요 👇\n\n"
           "🦆 골든덕랩은 매일 황금알 하나씩,\n기초부터 차근차근 돈 공부를 함께해요.\n\n"
           "💛 저장해두고 하나씩 따라 해보세요\n🐥 팔로우하면 매일 새 황금알이 도착해요\n\n"
           f"다음 편 예고 ▶ {nxt or '다음 현금흐름편'}\n\n"
           f"#배당 #배당투자 #현금흐름 #월배당 #{tag} #재테크 #골든덕랩")
    ep = {"series": "현금흐름 황금알", "theme": "income", "kind": "income", "no": no, "slug": f"inc-{no:02d}",
          "ticker": e["ticker"], "slides": slides, "caption": cap}
    dd = ROOT / "etf" / "income_episodes"
    dd.mkdir(exist_ok=True)
    path = dd / f"{no:02d}.json"
    path.write_text(json.dumps(ep, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def next_in_queue():
    st = json.loads((ROOT / "state.json").read_text()) if (ROOT / "state.json").exists() else {}
    done = st.get("income_published", [])
    d = json.loads((ROOT / "etf" / "income.json").read_text(encoding="utf-8"))
    ok = {x["ticker"] for x in d["etfs"] if x.get("status") == "ok" and x.get("yield_pct")}
    queue = [l.split("#")[0].strip() for l in (ROOT / "etf" / "income_queue.txt").read_text(encoding="utf-8").splitlines()]
    todo = [q for q in queue if q and q in ok and q not in done]
    if not todo:
        print("")
        return
    nxt = ""
    if len(todo) > 1:
        _, n2 = load(todo[1])
        nxt = f"{label(n2)}로 월 100만원 받으려면?"
    path = build(todo[0], len(done) + 1, nxt)
    print(path.relative_to(ROOT), todo[0])


if __name__ == "__main__":
    if sys.argv[1] == "next":
        next_in_queue()
    else:
        print(build(sys.argv[1], int(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else ""))
