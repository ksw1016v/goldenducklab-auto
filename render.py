"""골든덕랩 카드뉴스 렌더러: episodes/*.json -> out/<ep>/NN.png (1080x1350)"""
import json, sys, html, pathlib, base64
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).parent
ASSET = ROOT / "assets"
def uri(name):
    return "data:image/png;base64," + base64.b64encode((ASSET/name).read_bytes()).decode()

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1350px;background:#FFF6E0;font-family:'Noto Sans CJK KR',sans-serif;color:#5C2E0E;word-break:keep-all}
.frame{position:absolute;inset:28px;border:12px solid #F5B800;border-radius:44px;padding:64px 70px 50px;display:flex;flex-direction:column}
.top{display:flex;justify-content:space-between;align-items:center}
.tag{background:#5C2E0E;color:#FFF6E0;font-size:30px;font-weight:700;padding:12px 28px;border-radius:999px}
.page{font-size:28px;color:#C98A3D;font-weight:700}
.main{flex:1;display:flex;flex-direction:column;justify-content:center}
.foot{display:flex;justify-content:space-between;align-items:center;border-top:3px dashed #C98A3D;padding-top:26px;font-size:28px;font-weight:700}
.foot span:last-child{color:#C98A3D}
mark{background:linear-gradient(transparent 45%,#F5B800 45%);color:inherit;padding:0 4px}
.pink{color:#F06A8A}
.kicker{font-size:40px;color:#C98A3D;font-weight:700;margin-bottom:22px}
h1{font-size:92px;line-height:1.28;font-weight:900;letter-spacing:-2px}
.sub{font-size:40px;margin-top:34px;line-height:1.5;font-weight:500}
h2{font-size:64px;line-height:1.3;font-weight:900;letter-spacing:-1px;margin-bottom:44px}
.lead{font-size:36px;line-height:1.6;margin-bottom:34px;font-weight:500}
.item{display:flex;gap:26px;align-items:flex-start;background:#fff;border:3px solid #F5DFA8;border-radius:28px;padding:30px 34px;margin-bottom:22px}
.num{flex:none;width:64px;height:64px;border-radius:50%;background:#F5B800;color:#5C2E0E;font-size:34px;font-weight:900;display:flex;align-items:center;justify-content:center}
.it{font-size:38px;font-weight:700;line-height:1.35}
.id{font-size:30px;line-height:1.5;margin-top:8px;font-weight:400;color:#7a4a28}
.tip{background:#EEF6E2;border:3px solid #7CB342;border-radius:28px;padding:28px 34px;font-size:32px;line-height:1.55;margin-top:14px}
.tip b{color:#4E7D22}
.check{display:flex;gap:22px;align-items:center;font-size:38px;font-weight:700;padding:22px 0;border-bottom:2px solid #F5DFA8}
.box{flex:none;width:52px;height:52px;border:5px solid #C98A3D;border-radius:12px;background:#fff}
.cover-duck{position:absolute;right:56px;bottom:130px;width:300px}
.sub{max-width:600px}
.end{align-items:center;text-align:center}
.end img{width:430px;margin-bottom:30px}
.cta{background:#5C2E0E;color:#FFF6E0;font-size:40px;font-weight:900;padding:30px 50px;border-radius:999px;margin-top:40px;display:inline-block}
.next{font-size:32px;margin-top:34px;color:#C98A3D;font-weight:700}
.ticker{font-size:150px;font-weight:900;letter-spacing:-3px;line-height:1;color:#5C2E0E}
.ename{font-size:34px;color:#7a4a28;margin-top:14px;font-weight:500}
.chip{display:inline-block;align-self:flex-start;background:#F5B800;font-size:30px;font-weight:700;padding:10px 26px;border-radius:999px;margin-top:22px}
.kv{display:flex;justify-content:space-between;gap:30px;font-size:34px;padding:20px 0;border-bottom:2px solid #F5DFA8}
.kv span{color:#C98A3D;font-weight:700;flex:none}.kv b{text-align:right}
.drow{display:flex;align-items:center;gap:28px;background:#fff;border:3px solid #F5DFA8;border-radius:28px;padding:30px 36px;margin-bottom:22px}
.dy{flex:none;width:120px;height:120px;border-radius:50%;background:#F5B800;display:flex;align-items:center;justify-content:center;font-size:36px;font-weight:900}
.dv{flex:1}.dpr{font-size:30px;color:#7a4a28}.dval{font-size:56px;font-weight:900;letter-spacing:-1px}
.dret{font-size:40px;font-weight:900;color:#4E7D22}.dret.neg{color:#D9534F}
.disc{font-size:24px;color:#9a7a5a;margin-top:18px;line-height:1.5}
"""

THEMES = {
    # 현금흐름 황금알: 초록·민트 바탕 + 황금색 강조
    "income": """
body{background:#EDF8F2;color:#173B30}
.frame{border-color:#1F6B52}
.tag{background:#1F6B52;color:#FFFFFF}
.page,.kicker,.next,.foot span:last-child,.kv span{color:#3F8A6E}
.foot{border-top-color:#9FCFBA}
h1,h2,.ticker,.dval,.it,.check{color:#173B30}
.item,.drow{border-color:#CDE7DC;background:#FFFFFF}
.id,.dpr,.ename,.lead,.sub{color:#35594C}
.dy{background:#1F6B52;color:#FFFFFF}
.kv{border-bottom-color:#CDE7DC}
.check{border-bottom-color:#CDE7DC}
.box{border-color:#3F8A6E}
.tip{background:#E0F3EA;border-color:#3F9B78}
.tip b{color:#1F6B52}
.cta{background:#1F6B52}
.disc{color:#5E7F72}
.dret{color:#1F6B52}
""",
    # ETF 황금알: 네이비·블루 바탕 + 황금색 강조 (기초편 크림·골드와 구분)
    "etf": """
body{background:#EEF3F9;color:#1B2A41}
.frame{border-color:#1E3A5F}
.tag{background:#1E3A5F;color:#FFFFFF}
.page,.kicker,.next,.foot span:last-child,.kv span{color:#4A6A8F}
.foot{border-top-color:#9DB3CC}
h1,h2,.ticker,.dval,.it,.check{color:#1B2A41}
.item,.drow{border-color:#C9D7E6;background:#FFFFFF}
.id,.dpr,.ename,.lead,.sub{color:#3E5674}
.dy{background:#1E3A5F;color:#FFFFFF}
.kv{border-bottom-color:#C9D7E6}
.check{border-bottom-color:#C9D7E6}
.box{border-color:#4A6A8F}
.tip{background:#E3EEF9;border-color:#4A7FB5}
.tip b{color:#1E3A5F}
.cta{background:#1E3A5F}
.disc{color:#6B7F96}
.cover-duck,.end img{filter:drop-shadow(0 0 0 #1E3A5F)}
""",
}


def esc(s):  # 허용 태그(mark, span.pink, br)만 살리고 나머지 이스케이프
    t = html.escape(s)
    for a, b in [("&lt;mark&gt;", "<mark>"), ("&lt;/mark&gt;", "</mark>"), ("&lt;br&gt;", "<br>"),
                 ("&lt;p&gt;", '<span class="pink">'), ("&lt;/p&gt;", "</span>")]:
        t = t.replace(a, b)
    return t

def slide(ep, s, i, n):
    tag = f"{ep['series']} #{ep['no']:02d}"
    k = s["type"]
    if k == "cover":
        import re
        lines = re.sub(r"<(?!br)[^>]+>", "", s["title"]).split("<br>")
        longest = max(len(l) for l in lines)
        fs = 92 if longest <= 9 else max(54, int(92 * 9.5 / longest))
        body = f"""<div class="main"><div class="kicker">{esc(s['kicker'])}</div><h1 style="font-size:{fs}px">{esc(s['title'])}</h1>
<div class="sub">{esc(s['sub'])}</div></div><img class="cover-duck" src="{uri('duck.png')}">"""
    elif k == "list":
        items = "".join(f"""<div class="item"><div class="num">{j+1}</div><div><div class="it">{esc(t)}</div>{f'<div class="id">{esc(d)}</div>' if d else ''}</div></div>"""
                        for j, (t, d) in enumerate(s["items"]))
        lead = f'<div class="lead">{esc(s["lead"])}</div>' if s.get("lead") else ""
        tip = f'<div class="tip"><b>골든덕 팁</b> · {esc(s["tip"])}</div>' if s.get("tip") else ""
        body = f'<div class="main"><h2>{esc(s["title"])}</h2>{lead}{items}{tip}</div>'
    elif k == "check":
        items = "".join(f'<div class="check"><div class="box"></div>{esc(t)}</div>' for t in s["items"])
        tip = f'<div class="tip" style="margin-top:34px">{esc(s["tip"])}</div>' if s.get("tip") else ""
        body = f'<div class="main"><h2>{esc(s["title"])}</h2>{items}{tip}</div>'
    elif k == "etf_info":
        rows = "".join(f'<div class="kv"><span>{esc(a)}</span><b>{esc(b)}</b></div>' for a, b in s["rows"])
        body = f"""<div class="main"><div class="ticker">{esc(s['ticker'])}</div><div class="ename">{esc(s['name'])}</div>
<div class="chip">{esc(s['category'])}</div><div class="lead" style="margin-top:28px">{esc(s['desc'])}</div>{rows}</div>"""
    elif k == "dca":
        rows = "".join(f"""<div class="drow"><div class="dy">{esc(y)}</div><div class="dv"><div class="dpr">{"원금 " + esc(p) if p != "-" else "이 시점엔 아직 상장 전"}</div>
<div class="dval">{esc(v)}</div></div><div class="dret {'neg' if r.startswith('-') else ''}">{esc(r)}</div></div>""" for y, p, v, r in s["rows"])
        body = f"""<div class="main"><h2>{esc(s['title'])}</h2>{rows}<div class="disc">{esc(s.get('note', ''))}</div></div>"""
    elif k == "need":
        rows = "".join(f"""<div class="drow"><div class="dy" style="font-size:{30 if len(c) > 3 else 34}px;line-height:1.15;text-align:center">{esc(c)}</div><div class="dv"><div class="dpr">{esc(l)}</div>
<div class="dval">{esc(v)}</div></div><div class="dret">{esc(sd)}</div></div>""" for c, l, v, sd in s["rows"])
        body = f"""<div class="main"><h2>{esc(s['title'])}</h2>{rows}{f'<div class="tip" style="margin-top:10px">{esc(s["tip"])}</div>' if s.get("tip") else ""}<div class="disc">{esc(s.get('note', ''))}</div></div>"""
    elif k == "end":
        body = f"""<div class="main end"><img src="{uri('logo.png')}"><h2 style="margin-bottom:10px">{esc(s['title'])}</h2>
<div class="lead" style="margin:0">{esc(s['sub'])}</div><div><span class="cta">{esc(s['cta'])}</span></div>
{f'<div class="next">{esc(s["next"])}</div>' if s.get('next') else ''}</div>"""
    foot_r = "넘겨보기 →" if i < n else "저장하고 다시 보기"
    theme = THEMES.get(ep.get("theme", ""), "")
    return f"""<html><head><meta charset="utf-8"><style>{CSS}{theme}</style></head><body><div class="frame">
<div class="top"><span class="tag">{esc(tag)}</span><span class="page">{i} / {n}</span></div>{body}
<div class="foot"><span>@golden_duck_lab</span><span>{foot_r}</span></div></div></body></html>"""

def render(path):
    ep = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    slug = ep.get("slug") or f"{ep['no']:02d}"
    out = ROOT / "out" / slug
    out.mkdir(parents=True, exist_ok=True)
    n = len(ep["slides"])
    with sync_playwright() as p:
        import os
        exe = os.environ.get("CHROME_PATH")
        b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        for i, s in enumerate(ep["slides"], 1):
            pg.set_content(slide(ep, s, i, n), wait_until="load")
            pg.wait_for_timeout(150)
            over = pg.evaluate("(()=>{const m=document.querySelector('.frame');return m.scrollHeight>m.clientHeight+2})()")
            if over: print(f"!! overflow ep{ep['no']} slide{i}")
            pg.screenshot(path=str(out / f"golden_duck_lab_{slug}_{i:02d}.jpg"), type="jpeg", quality=92)
        b.close()
    if ep.get("caption"):
        (out / "caption.txt").write_text(ep["caption"], encoding="utf-8")
    print("rendered", out)

if __name__ == "__main__":
    for a in sys.argv[1:]: render(a)
