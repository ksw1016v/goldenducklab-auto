"""ETF 특별편 '월 10만원 배당 달력' 릴스 장면 (네이비 ETF 테마 위에 얹음).
첫 장면에 결론(필요 원금)을 먼저 보여 주고, 달력이 세 색으로 채워지는 흐름.
"""
from render import esc, uri

SP_CSS = """<style>
.spc{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;margin:34px 0 30px}
.spc .c{position:relative;height:190px}
.spc .b,.spc .l{position:absolute;inset:0;border-radius:30px;display:flex;flex-direction:column;align-items:center;justify-content:center;font-weight:900}
.spc .b{background:#fff;border:4px solid #C9D7E6;color:#9DB3CC;font-size:54px}
.spc .b small{font-size:30px;margin-top:4px;color:#B8C8DA}
.spc .l{color:#fff;font-size:54px}.spc .l small{font-size:30px;margin-top:4px;font-weight:700}
.lgd{display:flex;align-items:center;gap:18px;font-size:42px;padding:10px 0;color:#3E5674}
.lgd span{flex:none;width:44px;height:44px;border-radius:12px}.lgd b{color:#1B2A41}
.big2{font-size:150px;font-weight:900;letter-spacing:-4px;color:#1B2A41;line-height:1.05}
.zero{font-size:96px;font-weight:900;color:#4A6A8F;margin-top:10px}
.tot{margin-top:34px;background:#1E3A5F;color:#fff;border-radius:30px;padding:34px 40px;font-size:52px;font-weight:900;text-align:center}
.tot b{color:#F5B800}
</style>"""


def cal(groups, lit_start=1.0, step=0.18, per_group_gap=0.5, zero=False):
    mg = {}
    t = lit_start
    for g in groups:
        for m in g["months"]:
            mg[m] = (g, t)
            t += step
        t += per_group_gap
    cells = ""
    for m in range(1, 13):
        lit = ""
        if m in mg:
            g, at = mg[m]
            lit = f'<div class="l" data-pop="{at:.2f}" style="background:{g["color"]}">{m}월<small>{esc(g["label"])}</small></div>'
        base = f'<div class="b">{m}월{"<small>0원</small>" if zero and m not in mg else ""}</div>'
        cells += f'<div class="c" data-in="{0.3 + 0.03 * m:.2f}">{base}{lit}</div>'
    return f'<div class="spc">{cells}</div>', t


def scenes_special(ep):
    g = ep["groups"]
    R = {"total": 55000000, "hook1": "매달 <mark>10만원</mark> 배당,", "hook2": "얼마 있으면 될까?",
         "hook_sub": "세 종목으로 12달을 채우면<br>매달 세후 약 10만원", "problem": True,
         "sol1": "지급 달이 다른", "sol2": "<mark>세 종목</mark>으로 12달", "sol_zero": False,
         "total_text": "합계 약 <b>5,500만원</b>", "need_title": "<mark>필요한 원금</mark>",
         "alt_index": 1, "alt_title": "<mark>다른 조합</mark>도 있어요",
         "end_title": "나만의 배당 달력,<br>저장해 두세요", "cover_title": "매달 <mark>10만원</mark><br>배당 달력",
         "cover_tot": "세 종목 · 합계 약 <b>5,500만원</b>"}
    R.update(ep.get("reel", {}))
    out = []
    duck = f'<img class="duck" data-pop="{{}}" src="{uri("duck.png")}">'
    # 1) 결론 먼저
    out.append((SP_CSS + f'''<div class="main">
<div class="h1" data-in="0.3">{R["hook1"]}</div>
<div class="h1" data-in="0.6">{R["hook2"]}</div>
<div class="big2" style="margin-top:70px" data-in="1.1"><span data-count="1.1,1.3" data-from="0" data-to="{R["total"]}" data-fmt="won">0만원</span></div>
<div class="subt" data-in="2.3" style="font-size:52px">{R["hook_sub"]}</div></div>{duck.format(2.6)}''', 4.8))
    # 2) 문제: 배당 ETF는 3·6·9·12월에 몰림
    schd = [x for x in g if x["label"] == "SCHD"]
    c, t = cal(schd or [{"label": "SCHD", "months": [3, 6, 9, 12], "color": "#1E3A5F"}], lit_start=1.0, step=0.25, zero=True)
    if R["problem"]:
        out.append((SP_CSS + f'''<div class="main"><div class="h2" data-in="0.1">배당 ETF만 모으면</div>
<div class="h2" data-in="0.4"><mark>4달만</mark> 들어와요</div>{c}
<div class="lead" data-in="{t + 0.1:.2f}" style="font-size:44px">SCHD·VYM·DGRO 모두 3·6·9·12월<br>나머지 8달은 0원</div></div>''', t + 2.4))
    # 3) 해결: 세 종목으로 12달
    order = [x for x in g if x["label"] != "SCHD"] + schd
    c, t = cal(order, lit_start=1.0, step=0.16, per_group_gap=0.45, zero=R["sol_zero"])
    lg = "".join(f'<div class="lgd" data-in="{t + 0.2 + 0.25 * i:.2f}"><span style="background:{x["color"]}"></span><b>{esc(x["label"])}</b> {esc(x["desc"])}</div>' for i, x in enumerate(order))
    out.append((SP_CSS + f'''<div class="main"><div class="h2" data-in="0.1">{R["sol1"]}</div>
<div class="h2" data-in="0.4">{R["sol2"]}</div>{c}{lg}</div>''', t + 2.6))
    # 4) 필요 원금
    rows, at = "", 0.8
    for x in order:
        rows += (f'<div class="drow" data-in="{at:.2f}"><div class="dy" style="font-size:34px;background:{x["color"]}">{esc(x["label"])}</div>'
                 f'<div class="dv"><div class="dpr">{"매달" if len(x["months"]) == 12 else "·".join(map(str, x["months"])) + "월"} · 연 {x["yield"]:.1f}%</div>'
                 f'<div class="dval" data-count="{at:.2f},1.0" data-from="0" data-to="{x["need"]}" data-fmt="won">0만원</div></div></div>')
        at += 1.1
    out.append((SP_CSS + f'''<div class="main"><div class="h2" data-in="0.1">매달 세후 10만원</div>
<div class="h2" data-in="0.35">{R["need_title"]}</div>{rows}
<div class="tot" data-pop="{at + 0.2:.2f}">{R["total_text"]}</div>
<div class="disc" data-in="0.6">11/6 종가·최근 1년 배당·환율 1,356원 · 세금 15.4% 반영 · 과거 수익률은 미래 수익을 보장하지 않음 · 특정 종목 추천 아님</div></div>''', at + 2.6))
    # 5) 다른 조합
    alts = [x for x in ep["slides"] if x["type"] == "list"][R["alt_index"]]["items"]
    items = "".join(f'<div class="item" data-in="{0.7 + 0.7 * j:.2f}"><div class="num">{j + 1}</div><div><div class="it">{esc(a)}</div><div class="id">{esc(b)}</div></div></div>'
                    for j, (a, b) in enumerate(alts))
    out.append((f'<div class="main"><div class="h2" data-in="0.1">{R["alt_title"]}</div>{items}</div>', 3.2 + 0.7 * len(alts)))
    # 6) 마무리
    out.append((f'''<div class="main end2"><img data-zoom="0.1" src="{uri("logo.png")}">
<div class="h2" data-in="0.7" style="margin-bottom:16px">{R["end_title"]}</div>
<div data-in="1.2" style="margin-top:40px"><span class="cta">@golden_duck_lab 팔로우</span></div></div>''', 3.6))
    return out


def cover_special(ep):
    R = {"cover_title": "매달 <mark>10만원</mark><br>배당 달력", "cover_tot": "세 종목 · 합계 약 <b>5,500만원</b>"}
    R.update(ep.get("reel", {}))
    cells = ""
    mg = {m: x for x in ep["groups"] for m in x["months"]}
    for m in range(1, 13):
        x = mg.get(m)
        cells += (f'<div class="c"><div class="l" style="background:{x["color"]}">{m}월<small>{esc(x["label"])}</small></div></div>' if x
                  else f'<div class="c"><div class="b">{m}월<small>0원</small></div></div>')
    return SP_CSS + f'''<div class="main cov">
<div class="h1">{R["cover_title"]}</div>
<div class="spc" style="margin-top:40px">{cells}</div>
<div class="tot">{R["cover_tot"]}</div></div>'''
