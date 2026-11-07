"""income.json 의 배당주·배당 ETF 하나로 '현금흐름 황금알' 카드뉴스 원고를 만든다.
(ETF편과 겹치지 않게 적립식 수익 계산은 넣지 않고 건전성·필요 원금·배당 달력에 집중)
사용법: python etf/make_income.py next        (대기열 다음 편, '경로 티커' 출력)
       python etf/make_income.py <티커> <편번호> [다음편제목]
       python etf/make_income.py queue       (통과 종목으로 income_queue.txt 다시 만들기)
"""
import json, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DISC = "배당은 확정된 금액이 아니고 바뀔 수 있어요 · 최근 1년 배당 기준, 세금·수수료 미반영 · 특정 종목 추천이 아닌 정보 제공"

NOTES = {
    "배당·커버드콜": [["분배금이 높은 대신 상승이 제한돼요", "옵션을 팔아 받은 돈을 나눠 주는 구조라 주가가 크게 올라도 다 따라가지 못해요"],
                  ["분배금은 매달 달라져요", "시장 변동성에 따라 늘었다 줄었다 해요"]],
    "리츠": [["임대료가 배당의 재료예요", "금리가 오르면 이자 부담이 커져 가격이 흔들릴 수 있어요"],
           ["부동산 경기를 함께 타요", "공실이 늘면 배당이 줄 수도 있어요"]],
    "인프라": [["통행료·사용료가 배당의 재료예요", "금리가 오르면 가격이 흔들릴 수 있어요"],
            ["투자 자산의 계약이 끝나면 수입이 바뀔 수 있어요", "운용 보고서로 자산 구성을 확인해 보세요"]],
    "금융": [["경기와 금리에 민감한 업종이에요", "대출이 부실해지면 배당이 줄 수 있어요"],
           ["주주환원 정책을 같이 보세요", "배당뿐 아니라 자사주 매입도 늘리는 추세예요"]],
    "통신": [["매달 요금이 들어오는 안정적인 사업", "대신 성장 속도는 느린 편이에요"],
           ["설비 투자가 많은 업종이에요", "투자 부담이 커지면 배당 여력이 줄 수 있어요"]],
    "에너지": [["유가에 따라 이익이 크게 변해요", "유가가 크게 떨어지면 주가도 흔들릴 수 있어요"],
            ["배당은 꾸준했지만 경기를 타요", "이익이 줄어도 배당을 유지할 힘이 있는지 봐야 해요"]],
    "유틸리티": [["전기·가스처럼 늘 쓰는 서비스", "경기가 나빠도 수요가 크게 줄지 않아요"],
              ["금리에 민감해요", "빚을 내 설비를 짓는 업종이라 금리가 오르면 부담이 커요"]],
    "필수소비재": [["경기와 상관없이 사는 물건", "불황에도 이익이 비교적 꾸준해요"],
               ["대신 크게 성장하긴 어려워요", "배당과 안정성을 보고 담는 종목이에요"]],
    "섹터": [["한 업종에 집중된 상품", "업종 경기에 따라 배당과 가격이 함께 흔들릴 수 있어요"],
           ["배당이 꾸준한 업종 위주", "대신 성장 속도는 느릴 수 있어요"]],
}
DEFAULT_STOCK = [["배당은 회사 이익에서 나와요", "이익이 줄면 배당도 줄 수 있어요"],
                 ["한 종목에만 담으면 위험이 커요", "여러 종목·업종에 나눠 담는 게 기본이에요"]]
DEFAULT_ETF = [["여러 종목에 나눠 담은 상품", "한 회사가 배당을 줄여도 영향이 작아요"],
               ["분배금은 매번 조금씩 달라요", "담긴 기업들의 배당에 따라 늘었다 줄었다 해요"]]
TAX_US = ["세금도 미리 알아두기", "배당소득세는 15.4% 수준이에요 (미국 상장 주식·ETF는 미국에서 15%를 먼저 떼고 들어와요). 금융소득이 연 2,000만원을 넘으면 종합과세 대상이에요"]
TAX_KR = ["세금도 미리 알아두기", "배당소득세는 15.4% 수준이에요. 금융소득이 연 2,000만원을 넘으면 종합과세 대상이에요"]


def won(v):
    if v in ("", None):
        return "-"
    v = int(v)
    if v >= 100_000_000:
        e, m = divmod(v, 100_000_000)
        m //= 10_000
        return f"{e}억 {m:,}만원" if m else f"{e}억원"
    return f"{v // 10_000:,}만원"


def is_etf(e):
    return e.get("type") == "ETF"


def label(e):
    """본문에서 부르는 이름: 미국 ETF는 티커, 그 외는 한글 이름"""
    return e["ticker"] if (e["market"] == "US" and is_etf(e)) else e["name"]


def kind_text(e):
    return ("미국" if e["market"] == "US" else "국내") + (" ETF" if is_etf(e) else " 주식")


def josa(word, a="으로", b="로"):
    ch = word[-1]
    if "가" <= ch <= "힣":
        jong = (ord(ch) - 0xAC00) % 28
        return a if jong not in (0, 8) else b   # ㄹ받침은 '로'
    return a if ch.upper() in "MN036" else b   # 엠·엔·영·일(ㄹ→로 예외 무시)·삼·육


def load(t):
    d = json.loads((ROOT / "etf" / "income.json").read_text(encoding="utf-8"))
    return d, next(x for x in d["etfs"] if x["ticker"].upper() == t.upper())


def dps(e, v):
    return f"${v:.2f}" if e["market"] == "US" else f"{v:,.0f}원"


def cal_tip(e):
    n = len(e["pay_months"])
    if n >= 12:
        return "매달 들어와서 생활비처럼 쓰기 좋아요"
    if n >= 4:
        return f"1년에 {n}번 들어와요. 지급 월이 다른 종목을 섞으면 <mark>매달 현금흐름</mark>을 만들 수 있어요"
    return f"1년에 {n}번 몰아서 들어와요. 다른 달에 주는 종목과 섞으면 현금흐름이 고르게 돼요"


def build(t, no, nxt):
    d, e = load(t)
    us = e["market"] == "US"
    etf = is_etf(e)
    asof = e["last_date"]
    name = label(e)
    cover_name = name if len(name) <= 6 else name.replace(" ", "<br>", 1)
    y = e["yield_pct"]
    growth = e.get("div_growth_5y_pct")
    word = "분배" if etf else "배당"

    rows = [["구분", kind_text(e) + f" · {e['category']}"], ["투자 대상" if etf else "사업", e["invests"]],
            ["배당수익률", f"연 {y:.1f}% (최근 1년)"], [f"{word} 주기", e["freq"]],
            [f"연속 {word}", f"{e['years_paid']}년째"]]
    if growth is not None and -90 < growth < 300:
        rows.append(["5년 배당 변화", f"{growth:+.0f}%"])

    hrows = [[c["name"], c["value"], c["ok"] is True, c["rule"] if c["ok"] is not None else "참고 · 이 종류엔 기준을 두지 않아요"]
             for c in e["checks"]]
    need_rows = [[f"월{a}만", f"매달 {a}만원 받으려면", won(e[f"need_{a}"]), ""] for a in (50, 100, 300)]
    notes = NOTES.get(e["category"], DEFAULT_ETF if etf else DEFAULT_STOCK)[:] + [TAX_US if us else TAX_KR]

    slides = [
        {"type": "cover", "kicker": f"현금흐름 황금알 · {kind_text(e)}",
         "title": f"<mark>{cover_name}</mark>{josa(name)}<br>매달 100만원<br>받으려면?",
         "sub": f"배당수익률 연 {y:.1f}% 기준<br>{asof[:4]}.{asof[5:7]} 데이터로 계산해 봐요"},
        {"type": "etf_info", "ticker": e["ticker"] if us else e["name"], "name": e.get("yahoo_name") if us else e["ticker"],
         "category": e["category"], "desc": e["desc"], "rows": rows},
        {"type": "health", "title": f"{word}, <mark>믿을 만할까?</mark>", "badge": f"건전성 점검 통과 · 위험도 {e['risk']}",
         "rows": hrows, "note": f"{asof} 기준 · 골든덕랩 자체 점검 기준이며 투자 권유가 아니에요"},
        {"type": "need", "title": "매달 <mark>이만큼</mark> 받으려면<br>얼마가 필요할까?", "rows": need_rows,
         "note": DISC + f" · {asof} 기준"},
        {"type": "calendar", "title": f"<mark>언제</mark> 들어올까?", "months": e["pay_months"], "tip": cal_tip(e),
         "note": "최근 1년 배당락일이 있었던 달 기준 · 실제 입금은 보통 그 뒤 1~2달 사이예요"},
        {"type": "list", "title": f"{name}<br><mark>알아둘 점</mark>", "items": notes},
        {"type": "list", "title": "오늘의 <mark>황금알</mark> 요약",
         "items": [[f"연 {y:.1f}%, {e['freq']} · {e['years_paid']}년 연속 {word}", ""],
                   [f"매달 100만원엔 약 {won(e['need_100'])} 필요", ""],
                   ["지급 월이 다른 종목을 섞으면 매달 현금흐름", ""]],
         "tip": "과거 배당이 <mark>미래 배당을 보장하지 않아요</mark>"},
        {"type": "end", "title": "오늘의 황금알,<br>저장해 두세요", "sub": "매일 아침 9시 · 점심 12시 · 저녁 7시 새 황금알",
         "cta": "@golden_duck_lab 팔로우", "next": f"다음 편 예고 · {nxt}" if nxt else "다음 현금흐름편도 기대해 주세요"},
    ]
    tag = (e["ticker"] if us else e["name"]).replace(" ", "").replace("(", "").replace(")", "").replace("&", "")
    ok_list = "\n".join(f"· {c['name']} {c['value']}" for c in e["checks"] if c["ok"])
    cap = (f"{name}{josa(name)} 매달 100만원 받으려면 얼마가 필요할까요? 🥚\n{e['desc']}.\n\n"
           f"오늘의 황금알은 '현금흐름 만들기 · {name}'예요.\n\n"
           f"✔ 배당 정보\n연 {y:.1f}% (최근 1년) · {e['freq']} 지급 · {e['years_paid']}년 연속 {word}\n\n"
           f"✔ 건전성 점검 (위험도 {e['risk']})\n{ok_list}\n\n"
           f"✔ 필요한 원금 (세전)\n월 50만원 → {won(e['need_50'])}\n월 100만원 → {won(e['need_100'])}\n월 300만원 → {won(e['need_300'])}\n\n"
           f"✔ 배당 달력\n{', '.join(f'{m}월' for m in e['pay_months'])} (배당락 기준)\n\n"
           f"📌 {asof} 기준, 최근 1년 배당이 그대로라고 가정한 계산이에요"
           + (", 원달러 환율 반영" if us else "") + ". 세금·수수료는 빼지 않았어요. 배당소득세는 15.4% 수준이에요.\n"
           "배당은 확정된 금액이 아니며, 특정 종목 추천이 아닌 정보 제공이에요.\n\n"
           "여러분은 매달 얼마의 현금흐름을 만들고 싶으세요? 댓글로 알려주세요 👇\n\n"
           "🦆 골든덕랩은 매일 황금알 하나씩,\n기초부터 차근차근 돈 공부를 함께해요.\n\n"
           "💛 저장해두고 하나씩 따라 해보세요\n🐥 팔로우하면 매일 새 황금알이 도착해요\n\n"
           f"다음 편 예고 ▶ {nxt or '다음 현금흐름편'}\n\n"
           f"#배당 #배당투자 #현금흐름 #{'배당ETF' if etf else '배당주'} #{tag} #재테크 #골든덕랩")
    ep = {"series": "현금흐름 황금알", "theme": "income", "kind": "income", "no": no, "slug": f"inc-{no:02d}",
          "ticker": e["ticker"], "slides": slides, "caption": cap}
    dd = ROOT / "etf" / "income_episodes"
    dd.mkdir(exist_ok=True)
    path = dd / f"{no:02d}.json"
    path.write_text(json.dumps(ep, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def passed():
    d = json.loads((ROOT / "etf" / "income.json").read_text(encoding="utf-8"))
    return {x["ticker"]: x for x in d["etfs"] if x.get("status") == "ok" and x.get("pass")}


def make_queue():
    """통과 종목을 미국주식 → 국내ETF·주식 → 미국ETF → 국내 순으로 번갈아 배치 (후보 파일 순서 = 인지도 순)"""
    ok = passed()
    b = {"US주식": [], "USETF": [], "KR주식": [], "KRETF": []}
    for t, e in ok.items():
        b[e["market"] + e["type"]].append(t)
    order = ["US주식", "KR주식", "USETF", "KRETF"]
    q = []
    while any(b.values()):
        for k in order:
            if b[k]:
                q.append(b[k].pop(0))
    lines = ["# 현금흐름 황금알 발행 순서 (매일 12:00 KST, 건전성 점검 통과 종목만 · make_income.py queue 로 재생성)"]
    lines += [f"{t}  # {ok[t]['name']}" for t in q]
    (ROOT / "etf" / "income_queue.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(len(q), "종목")


def next_in_queue():
    st = json.loads((ROOT / "state.json").read_text()) if (ROOT / "state.json").exists() else {}
    done = st.get("income_published", [])
    ok = passed()
    queue = [l.split("#")[0].strip() for l in (ROOT / "etf" / "income_queue.txt").read_text(encoding="utf-8").splitlines()]
    todo = [q for q in queue if q and q in ok and q not in done]
    if not todo:
        print("")
        return
    nxt = ""
    if len(todo) > 1:
        n2 = ok[todo[1]]
        nxt = f"{label(n2)}{josa(label(n2))} 매달 100만원 받으려면?"
    path = build(todo[0], len(done) + 1, nxt)
    print(path.relative_to(ROOT), todo[0])


if __name__ == "__main__":
    if sys.argv[1] == "next":
        next_in_queue()
    elif sys.argv[1] == "queue":
        make_queue()
    else:
        print(build(sys.argv[1], int(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else ""))
