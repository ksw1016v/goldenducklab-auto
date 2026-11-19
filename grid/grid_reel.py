"""20년 바둑판 · ○월편 릴스 (S&P500 월별 등락, 매달 첫째 월요일).

흐름: 이번 달 20칸이 한 칸씩 채워짐 → 상승 횟수·평균·최고·최악 → 240칸 전체(이번 달 줄 강조)
      → 20년 전체로는 몇 배 → "다음 달은 빨강? 파랑?" 댓글 참여
색은 국내 증시 관례: 상승 빨강, 하락 파랑. 숫자는 grid/data.json(지수 종가, 배당 제외)에서만 계산한다.
"""
import base64, json, pathlib
from html import escape as esc

ROOT = pathlib.Path(__file__).resolve().parent.parent
MON = ["1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월"]


def load(key="SPX"):
    return json.loads((ROOT / "grid/data.json").read_text(encoding="utf-8"))[key]


def ch(name):
    return "data:image/png;base64," + base64.b64encode((ROOT / "assets/chars" / f"{name}.png").read_bytes()).decode()


def color(x, scale=6.0):
    """빨강(상승)·파랑(하락), 크기에 따라 진하게."""
    a = min(abs(x) / scale, 1.0)
    if x >= 0:
        lo, hi = (253, 221, 221), (210, 32, 39)
    else:
        lo, hi = (218, 230, 252), (35, 88, 200)
    c = tuple(int(l + (h - l) * (0.25 + 0.75 * a)) for l, h in zip(lo, hi))
    return "rgb(%d,%d,%d)" % c


def stats(month, key="SPX"):
    d = load(key)
    years = [y for y in sorted(d["rows"]) if 2006 <= int(y) <= 2025]
    col = [(y, d["rows"][y][month - 1]) for y in years]
    up = sum(1 for _, x in col if x > 0)
    avg = sum(x for _, x in col) / len(col)
    avgs = []
    for i in range(12):
        xs = [d["rows"][y][i] for y in years]
        avgs.append(sum(xs) / len(xs))
    rank = sorted(range(12), key=lambda i: -avgs[i]).index(month - 1) + 1
    full = [d["rows"][y][i] for y in years for i in range(12)]
    return {"name": d["name"], "years": years, "col": col, "up": up, "down": len(col) - up, "avg": avg, "rank": rank,
            "best": max(col, key=lambda t: t[1]), "worst": min(col, key=lambda t: t[1]),
            "full_up": sum(1 for x in full if x > 0), "full_down": sum(1 for x in full if x <= 0),
            "start": d["close_2005"], "now": d["close_last"], "now_date": d["last_date"], "rows": d["rows"]}


G_CSS = """<style>
.kick{display:inline-block;align-self:flex-start;background:#1E3A5F;color:#FFE08A;font-size:40px;font-weight:900;padding:10px 28px;border-radius:999px;margin-bottom:22px}
.q{font-size:88px;font-weight:900;line-height:1.22;letter-spacing:-2px;color:#1B2A41}
.col{display:flex;flex-direction:column;gap:7px;margin-top:6px}
.cr{display:flex;align-items:center;gap:18px;height:52px}
.cr .y{width:110px;font-size:34px;font-weight:800;color:#5C6B80;text-align:right}
.cr .c{flex:1;height:52px;border-radius:12px;display:flex;align-items:center;padding:0 22px;font-size:34px;font-weight:900;color:#fff;background:#E9E3D6}
.score{display:flex;gap:26px;margin:4px 0 18px}
.score div{flex:1;border-radius:24px;padding:14px 22px;font-size:40px;font-weight:900;color:#fff}
.score .u{background:#D22027}.score .d{background:#2358C8}
.score b{font-size:64px}
.big{font-size:150px;font-weight:900;letter-spacing:-4px;line-height:1;color:#D22027}
.st{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:40px}
.st div{background:#fff;border:4px solid #E9DFC9;border-radius:28px;padding:26px 30px;font-size:36px;font-weight:700;color:#5C6B80}
.st b{display:block;font-size:62px;font-weight:900;color:#1B2A41;margin-top:6px}
.grid{display:grid;grid-template-columns:76px repeat(12,1fr);gap:5px;margin-top:6px}
.grid .h{font-size:24px;font-weight:900;color:#5C6B80;text-align:center;padding-bottom:4px}
.grid .h.on{color:#1B2A41;background:#FFE08A;border-radius:8px}
.grid .yl{font-size:24px;font-weight:800;color:#5C6B80;text-align:right;padding-right:6px;line-height:44px}
.grid .g{height:44px;border-radius:7px}
.grid .g.on{outline:4px solid #1B2A41;outline-offset:-2px}
.px{image-rendering:pixelated;position:absolute}
.sb{background:#fff;border:5px solid #5C2E0E;border-radius:36px;padding:28px 36px;font-size:52px;font-weight:900;line-height:1.3;color:#3B2A14}
.pick{display:flex;gap:28px;margin-top:40px}
.pick div{flex:1;border-radius:36px;padding:40px 20px;text-align:center;font-size:64px;font-weight:900;color:#fff}
</style>"""


def pct(x):
    return f"{x:+.1f}%"


def scenes_grid(ep):
    m = ep["month"]
    s = stats(m)
    M = MON[m - 1]
    nxt = MON[m % 12]
    egg = ch("egg")
    out = []
    # 1) 질문
    out.append((G_CSS + f'''<div class="main"><div class="kick" data-in="0.1">S&amp;P500 · {M}편</div>
<div class="q" data-in="0.3">지난 20년,<br><mark>{M}</mark>에 미국 주식은<br>몇 번 올랐을까?</div>
<div class="sb" data-pop="1.4" style="margin-top:70px;width:560px">20번 중에…<br>반반 아닐까?</div></div>
<img class="px" src="{egg}" style="right:110px;bottom:300px;width:260px" data-pop="1.1">''', 3.2))
    # 2) 이번 달 20칸
    step = 0.2
    rows = ""
    up_t = []
    for i, (y, x) in enumerate(s["col"]):
        t = 0.5 + step * i
        rows += f'<div class="cr" data-pop="{t:.2f}"><span class="y">{y}</span><span class="c" style="background:{color(x)}">{pct(x)}</span></div>'
    te = 0.5 + step * len(s["col"])
    out.append((G_CSS + f'''<div class="main"><div class="score"><div class="u" data-in="0.1">상승 <b><span data-count="0.5,{te - 0.5:.2f}" data-from="0" data-to="{s["up"]}" data-fmt="num">0</span></b>번</div>
<div class="d" data-in="0.1">하락 <b><span data-count="0.5,{te - 0.5:.2f}" data-from="0" data-to="{s["down"]}" data-fmt="num">0</span></b>번</div></div>
<div class="col">{rows}</div></div>''', te + 1.3))
    # 3) 성적표
    out.append((G_CSS + f'''<div class="main"><div class="kick" data-in="0.1">S&amp;P500 · {M} 성적표</div>
<div class="big" data-pop="0.3">20번 중 {s["up"]}번</div>
<div class="q" style="font-size:64px;margin-top:16px" data-in="0.8">올랐어요 (상승 확률 {s["up"] * 5}%)</div>
<div class="st"><div data-pop="1.4">평균<b style="color:#D22027">{pct(s["avg"])}</b></div><div data-pop="1.7">12달 중<b>평균 {s["rank"]}위</b></div>
<div data-pop="2.0">최고 {s["best"][0]}년<b style="color:#D22027">{pct(s["best"][1])}</b></div><div data-pop="2.3">최악 {s["worst"][0]}년<b style="color:#2358C8">{pct(s["worst"][1])}</b></div></div></div>''', 4.6))
    # 4) 240칸 전체
    head = '<span></span>' + "".join(f'<span class="h{" on" if i + 1 == m else ""}">{i + 1}</span>' for i in range(12))
    cells = ""
    for r, y in enumerate(s["years"]):
        t = 0.4 + 0.11 * r
        cells += f'<span class="yl" data-in="{t:.2f}">{y[2:]}년</span>'
        for i in range(12):
            x = s["rows"][y][i]
            cells += f'<span class="g{" on" if i + 1 == m else ""}" style="background:{color(x)}" data-pop="{t + 0.015 * i:.3f}"></span>'
    tg = 0.4 + 0.11 * len(s["years"]) + 0.3
    out.append((G_CSS + f'''<div class="main"><div class="score" style="margin:0 0 10px"><div class="u" data-in="0.1">상승 <b><span data-count="0.4,{tg - 0.4:.2f}" data-from="0" data-to="{s["full_up"]}" data-fmt="num">0</span></b>칸</div>
<div class="d" data-in="0.1">하락 <b><span data-count="0.4,{tg - 0.4:.2f}" data-from="0" data-to="{s["full_down"]}" data-fmt="num">0</span></b>칸</div></div>
<div class="grid">{head}{cells}</div></div>''', tg + 1.6))
    # 5) 20년 전체로는
    mult = s["now"] / s["start"]
    out.append((G_CSS + f'''<div class="main"><div class="q" style="font-size:72px" data-in="0.1">파란 칸 <span style="color:#2358C8">{s["full_down"]}개</span>를<br>지나오는 동안</div>
<div class="q" style="font-size:56px;margin-top:40px;color:#5C6B80" data-in="0.8">S&amp;P500 지수</div>
<div class="big" style="font-size:120px;margin-top:6px" data-in="1.1"><span data-count="1.1,1.4" data-from="{s["start"]}" data-to="{s["now"]}" data-fmt="num">{s["start"]:,.0f}</span></div>
<div class="q" style="font-size:52px;color:#5C6B80;margin-top:10px" data-in="1.1">2005년 말 {s["start"]:,.0f}에서</div>
<div data-pop="2.7"><span class="ret" style="display:inline-block;margin-top:30px;background:#D22027;color:#fff;border-radius:999px;padding:16px 44px;font-size:64px;font-weight:900">약 {mult:.1f}배</span></div></div>''', 4.6))
    # 6) 참여
    out.append((G_CSS + f'''<div class="main"><div class="q" data-in="0.1">다음 달 <mark>{nxt}</mark>은?</div>
<div class="pick"><div data-pop="0.6" style="background:#D22027">🔴 빨강<br><span style="font-size:40px">오른다</span></div><div data-pop="0.9" style="background:#2358C8">🔵 파랑<br><span style="font-size:40px">내린다</span></div></div>
<div class="subt" data-in="1.4" style="font-size:48px;font-weight:700;margin-top:40px">댓글로 빨강 / 파랑!<br>{nxt} 첫째 월요일, {nxt}편에서 확인해요</div>
<div class="disc" data-in="1.8" style="margin-top:auto">S&amp;P500 지수 월말 종가 기준(배당 제외) · 2006~2025년 · 지수 {s["now_date"]} 기준 · 과거 패턴은 미래 예측이 아니에요 · 특정 종목 추천 아님</div></div>''', 4.4))
    return out


def cover_grid(ep):
    m = ep["month"]
    s = stats(m)
    M = MON[m - 1]
    cells = "".join(f'<span class="g" style="background:{color(x)}"></span>' for _, x in s["col"])
    return G_CSS + f'''<div class="main cov"><div class="kick">S&amp;P500 · {M}편</div>
<div class="q">지난 20년,<br>{M}에 미국 주식은<br><mark>몇 번</mark> 올랐을까?</div>
<div style="display:grid;grid-template-columns:repeat(10,1fr);gap:8px;margin-top:50px" class="grid">{cells}</div>
<div class="q" style="font-size:56px;margin-top:30px;color:#5C6B80">🔴 상승 · 🔵 하락</div></div>'''


def caption(ep):
    m = ep["month"]
    s = stats(m)
    M, nxt = MON[m - 1], MON[m % 12]
    col = "\n".join(f"{'🔴' if x > 0 else '🔵'} {y}년 {pct(x)}" for y, x in s["col"])
    return (f"지난 20년, {M}에 미국 주식은 {s['up']}번 올랐어요 📈\n다음 달 {nxt}은? 댓글로 빨강 / 파랑 👇\n\n"
            f"20년 바둑판 · {M}편\n\n"
            f"✔ S&P500 {M} 성적표 (2006~2025)\n· 20번 중 {s['up']}번 상승, {s['down']}번 하락\n· 평균 {pct(s['avg'])} (12달 중 {s['rank']}위)\n"
            f"· 최고 {s['best'][0]}년 {pct(s['best'][1])} / 최악 {s['worst'][0]}년 {pct(s['worst'][1])}\n\n"
            f"✔ 20년 240칸 전체\n상승 {s['full_up']}칸 · 하락 {s['full_down']}칸\n그 사이 지수는 2005년 말 {s['start']:,.0f} → 지금 {s['now']:,.0f} (약 {s['now'] / s['start']:.1f}배)\n\n"
            f"✔ 해마다 {M}\n{col}\n\n"
            f"매달 첫째 월요일, 그 달의 20년 성적표를 올려요. {nxt}편에서 여러분 예측도 확인해 볼게요!\n\n"
            f"📌 S&P500 지수 월말 종가 기준(배당 제외), 지수는 {s['now_date']} 기준이에요.\n"
            "과거 수익률은 미래 수익을 보장하지 않으며, 과거 패턴은 예측이 아니에요. 특정 종목 추천이 아닌 정보 제공이에요.\n\n"
            "🦆 골든덕랩은 매일 황금알 하나씩,\n기초부터 차근차근 돈 공부를 함께해요.\n\n"
            "💛 저장해두고 매달 비교해 보세요\n🐥 팔로우하면 다음 달 바둑판이 도착해요\n\n"
            f"#S앤P500 #미국주식 #{M}증시 #주식시즌 #미국ETF #재테크 #골든덕랩")
