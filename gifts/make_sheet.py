"""DM 선물용 월 10만원 배당 달력 조합 4가지 정리표 한 장 (가로 1080, 세로는 내용만큼)."""
import json, pathlib, os
from playwright.sync_api import sync_playwright
ROOT = pathlib.Path(__file__).resolve().parent.parent


def won(v):
    v = int(v)
    if v >= 100_000_000:
        e, m = divmod(v, 100_000_000); m //= 10_000
        return f"{e}억 {m:,}만원" if m else f"{e}억원"
    return f"{v // 10_000:,}만원"


NOTE = {"": "지급 달이 다른 세 종목으로 12달을 고르게",
        "-2": "통신사 배당이 높아 원금이 가장 적게 드는 3종목 조합",
        "-3": "ETF 하나로 매달. 다만 분배금이 달마다 달라요",
        "-4": "가장 단순. 대신 3·6·9·12월에만 30만원씩"}
NAME = {"": "① 3종목 분산", "-2": "② 원금 줄이기", "-3": "③ 월배당 ETF 하나", "-4": "④ SCHD 하나만"}


def combos():
    out = []
    for f in ["", "-2", "-3", "-4"]:
        d = json.loads((ROOT / f"etf/specials/dividend-calendar{f}.json").read_text(encoding="utf-8"))
        out.append({**d, "nm": NAME[f], "note": NOTE[f]})
    return out


def html():
    cs = combos()
    rows = ""
    for c in cs:
        cells = ""
        for m in range(1, 13):
            g = next((g for g in c["groups"] if m in g["months"]), None)
            cells += f'<div class="m" style="{"background:" + g["color"] + ";color:#fff" if g else ""}">{m}</div>'
        legend = " · ".join(f'<i style="background:{g["color"]}"></i>{g["label"]} {won(g["need"])}' for g in c["groups"])
        rows += f'''<div class="row"><div class="hd"><b>{c["nm"]}</b><span>{won(c["total"])}</span></div>
<div class="months">{cells}</div><div class="lg">{legend}</div><div class="nt">{c["note"]}</div></div>'''
    asof = cs[0]["asof"]
    return f"""<html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;background:#FFF6E0;font-family:'Noto Sans CJK KR',sans-serif;color:#1B2A41;word-break:keep-all;padding:56px 60px}}
.k{{font-size:30px;font-weight:700;color:#C98A3D}}
h1{{font-size:62px;font-weight:900;letter-spacing:-1.5px;line-height:1.2;margin:10px 0 8px}}
h1 mark{{background:linear-gradient(transparent 50%,#F5B800 50%);color:inherit}}
.s{{font-size:28px;color:#3E5674;margin-bottom:26px}}
.row{{background:#fff;border:3px solid #F5DFA8;border-radius:26px;padding:20px 26px;margin-bottom:16px}}
.hd{{display:flex;justify-content:space-between;align-items:baseline}}.hd b{{font-size:36px}}.hd span{{font-size:40px;font-weight:900;color:#E5383B}}
.months{{display:grid;grid-template-columns:repeat(12,1fr);gap:6px;margin:12px 0 10px}}
.m{{height:52px;border-radius:10px;background:#EEE8DA;color:#B5AA98;font-size:24px;font-weight:900;display:flex;align-items:center;justify-content:center}}
.lg{{font-size:23px;font-weight:700;color:#3E5674}}.lg i{{display:inline-block;width:18px;height:18px;border-radius:5px;margin-right:6px;vertical-align:-2px}}
.nt{{font-size:23px;color:#7a4a28;margin-top:4px}}
.f{{font-size:19px;color:#9a7a5a;line-height:1.5;margin-top:10px}}
.by{{position:absolute;right:60px;top:60px;font-size:26px;font-weight:900;color:#C98A3D}}
</style></head><body><div class="by">@golden_duck_lab</div>
<div class="k">골든덕랩 선물 · 저장해 두고 보세요</div>
<h1>매달 <mark>10만원</mark> 배당 달력<br>조합 4가지 한 장 정리</h1>
<div class="s">칸 색 = 그 달에 배당이 들어오는 종목 · 오른쪽 = 필요한 원금(세후 기준)</div>
{rows}
<div class="f">{asof[:4]}.{int(asof[5:7])}.{int(asof[8:])} 기준 · 최근 1년 배당이 이어진다고 가정 · 배당소득세 15.4% 반영 · 원달러 환율 반영 · 국내 계좌 입금은 며칠 늦을 수 있어요<br>배당은 확정 금액이 아니며 과거 실적이 미래를 보장하지 않아요 · 특정 종목 추천이 아닌 정보 제공이에요</div>
</body></html>"""


def render(out):
    with sync_playwright() as p:
        exe = os.environ.get("CHROME_PATH")
        b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        pg.set_content(html(), wait_until="load"); pg.wait_for_timeout(200)
        over = False
        if over: print("!! overflow", pg.evaluate("document.body.scrollHeight"))
        pg.screenshot(path=str(out), type="jpeg", quality=92, full_page=True)
        b.close()
    print("sheet", out)


if __name__ == "__main__":
    render(ROOT / "gifts" / "dividend-calendar.jpg")
