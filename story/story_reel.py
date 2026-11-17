"""골든에그의 월급일기 릴스 장면 (공감 → 선배 조언 → 실제 데이터 희망).

- 골든에그: 33살 직장인(캐릭터, 세후 월급 290만원), 골든덕: 조언하는 선배
- 원고(story/NN.json)의 scenes 를 순서대로 그린다. 장면 종류:
  hook · countdown · talk · rule · dca · mdd · dip · ask
- 실제 숫자는 자리표시자로 쓴다. {VOO.value} {VOO.invested} {VOO.ret} (etf/results.json: 매달 10만원 10년, 원화·배당 재투자)
  {VOO.mdd} {VOO.peak} {VOO.trough} {VOO.dip_ret} {VOO.dip_months} (story/data.json: Yahoo 수정주가, 달러 기준)
- 생활비 같은 이야기 숫자는 예시라고 화면 끝에 밝힌다.
"""
import base64, json, math, pathlib, re
from html import escape as esc  # render.py 를 불러오면 playwright 가 필요해서 직접 씀

ROOT = pathlib.Path(__file__).resolve().parent.parent


def ch(name):
    return "data:image/png;base64," + base64.b64encode((ROOT / "assets/chars" / f"{name}.png").read_bytes()).decode()


def won(v):
    v = int(v)
    if v >= 100_000_000:
        e, m = divmod(v, 100_000_000); m //= 10_000
        return f"{e}억 {m:,}만원" if m else f"{e}억원"
    return f"{v // 10_000:,}만원"


def r0(x):
    """반올림(0.5는 0에서 먼 쪽) — 화면 카운트(JS)와 캡션 숫자를 똑같이 맞춘다."""
    return int(math.copysign(math.floor(abs(x) + 0.5), x))


def ym(d):
    return f"{d[:4]}년 {int(d[5:7])}월"


def facts():
    res = {e["ticker"]: e for e in json.loads((ROOT / "etf/results.json").read_text(encoding="utf-8"))["etfs"]}
    p = ROOT / "story/data.json"
    sd = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"tickers": {}}
    return res, sd


def resolve(text, ep=None):
    """{TICKER.key} 자리표시자를 실제 숫자로 바꾼다. 없는 값이 있으면 멈춘다(지어낸 숫자 방지)."""
    res, sd = facts()

    def one(m):
        t, k = m.group(1), m.group(2)
        if k in ("value", "invested", "ret", "name", "asof"):
            e = res.get(t)
            if not e:
                raise SystemExit(f"results.json 에 {t} 없음")
            inv = e["invest10y_months"] * 100_000
            return {"value": won(e["v10y_10"]), "invested": won(inv), "ret": f"{(e['v10y_10'] / inv - 1) * 100:+,.0f}",
                    "name": e["name"], "asof": e["last_date"]}[k]
        e = sd["tickers"].get(t)
        if not e:
            raise SystemExit(f"story/data.json 에 {t} 없음 (fetch_story.py 먼저)")
        return {"mdd": f"{r0(e['mdd'])}", "peak": ym(e["peak"]), "trough": ym(e["trough"]),
                "dip_ret": f"{r0(e['dip_ret']):+d}", "dip_months": str(e["dip_months"])}[k]
    return re.sub(r"\{([A-Z0-9]+)\.([a-z_]+)\}", one, text)


S_CSS = """<style>
.px{image-rendering:pixelated;position:absolute}
.sb{background:#fff;border:5px solid #5C2E0E;border-radius:40px;padding:36px 44px;font-size:62px;font-weight:900;line-height:1.3;color:#3B2A14;position:relative}
.sb.dk{background:#3B2A14;color:#FFE08A;border-color:#3B2A14}
.pay{font-size:70px;font-weight:900;color:#3E5674;line-height:1.35}
.bal{font-size:150px;font-weight:900;letter-spacing:-4px;color:#1B2A41;line-height:1.05}
.bal.red{color:#E5383B}.bal.green{color:#2E7D4F}
.spend{display:flex;justify-content:space-between;background:#fff;border:4px solid #F5DFA8;border-radius:24px;padding:22px 34px;margin-bottom:16px;font-size:50px;font-weight:700;color:#5C2E0E}
.spend b{color:#E5383B;font-weight:900}
.rule{display:flex;align-items:center;gap:30px;border-radius:34px;padding:38px 40px;margin-bottom:30px;font-size:58px;font-weight:900;line-height:1.3}
.rule.no{background:#F3E3E3;color:#8A3A3A}.rule.ok{background:#1E3A5F;color:#fff}
.rule .ic{flex:none;font-size:80px}
.vrow{display:flex;align-items:baseline;gap:20px;font-size:54px;font-weight:700;color:#3E5674;margin-top:16px}
.vrow b{font-size:66px;color:#1B2A41}
.ret{display:inline-block;margin-top:24px;background:#2E7D4F;color:#fff;border-radius:999px;padding:14px 40px;font-size:56px;font-weight:900}
.ret.red{background:#E5383B}
.q{font-size:96px;font-weight:900;line-height:1.25;letter-spacing:-2px;color:#1B2A41}
.ep{display:inline-block;align-self:flex-start;background:#F5B800;color:#3B2A14;font-size:40px;font-weight:900;padding:10px 28px;border-radius:999px;margin-bottom:24px}
.ddrow{background:#fff;border:4px solid #F5DFA8;border-radius:30px;padding:30px 36px;margin-bottom:26px}
.ddrow .nm{font-size:44px;font-weight:900;color:#3B2A14}.ddrow .pd{font-size:32px;color:#7a4a28;margin-top:4px}
.ddbar{height:56px;background:#F1E8D6;border-radius:14px;margin-top:18px;overflow:hidden}
.ddbar i{display:block;height:100%;background:#E5383B;transform-origin:left}
.ddv{font-size:80px;font-weight:900;color:#E5383B;letter-spacing:-2px;margin-top:10px}
</style>"""

POS = {  # 장면별 캐릭터 기본 위치
    "hook": "right:110px;bottom:330px;width:330px",
    "countdown": "right:90px;bottom:170px;width:220px",
    "rule": "right:90px;bottom:180px;width:300px",
    "dca": "right:100px;bottom:200px;width:230px",
    "mdd": "right:90px;bottom:170px;width:200px",
    "dip": "right:100px;bottom:200px;width:230px",
    "ask": "right:110px;bottom:420px;width:220px",
}


def img(who, style, anim):
    return f'<img class="px" src="{ch(who)}" style="{style}" {anim}>'


def scene(ep, s):
    t = s["type"]
    who = s.get("char", "duck" if t == "rule" else "egg")
    R = lambda x: resolve(x)
    if t == "hook":
        return (S_CSS + f'''<div class="main"><div class="ep" data-in="0.1">{esc(ep["series"])} #{ep["no"]:02d}</div>
<div class="pay" data-in="0.3">{R(s["kicker"])}</div>
<div class="bal {s.get("color", "")}" style="margin-top:20px;font-size:{s.get("size", 128)}px" data-pop="0.4">{R(s["big"])}</div>
<div class="sb" style="margin-top:60px;width:{s.get("w", 640)}px" data-pop="1.0">{R(s["say"])}</div></div>
{img(who, POS[t], 'data-pop="0.7"')}''', s.get("dur", 2.8))
    if t == "countdown":
        items = s["items"]
        left = s["start"] - sum(v for _, v in items)
        rows = "".join(f'<div class="spend" data-drop="{1.0 + 0.55 * i:.2f}"><span>{esc(k)}</span><b>-{v // 10_000:,}만</b></div>' for i, (k, v) in enumerate(items))
        te = 1.0 + 0.55 * len(items)
        return (S_CSS + f'''<div class="main"><div class="pay" data-in="0.1">{R(s["title"])}</div>
<div data-shake="{te:.2f},0.8,14"><div class="bal" style="margin:16px 0 30px"><span data-count="0.9,{te - 0.7:.2f}" data-from="{s["start"]}" data-to="{left}" data-fmt="num" data-suf="원">{s["start"]:,}원</span></div></div>
{rows}</div>{img(who, POS[t], f'data-shake="{te:.2f},0.8,10"')}''', te + 1.4)
    if t == "talk":
        # 두 줄 대화: 위 말풍선(오른쪽 캐릭터), 아래 말풍선(왼쪽 캐릭터)
        a, b = s["lines"]
        ca = {"egg": "egg", "duck": "duck"}[a["who"]]
        cb = {"egg": "egg", "duck": "duck_wow"}[b["who"]]
        wa = "right:90px;top:600px;width:200px" if ca == "egg" else "right:90px;top:560px;width:260px"
        wb = "left:90px;bottom:200px;width:330px" if cb != "egg" else "left:110px;bottom:200px;width:230px"
        return (S_CSS + f'''<div class="main"><div class="sb {"dk" if a["who"] == "duck" else ""}" data-pop="0.2" style="width:780px">{R(a["text"])}</div>
<div class="sb {"dk" if b["who"] == "duck" else ""}" data-pop="1.6" style="margin-top:auto;margin-bottom:440px;margin-left:200px">{R(b["text"])}</div></div>
{img(ca, wa, 'data-in="0.1"')}{img(cb, wb, 'data-pop="1.3"')}''', s.get("dur", 4.4))
    if t == "rule":
        return (S_CSS + f'''<div class="main"><div class="h1" data-in="0.1" style="margin-top:0">{R(s["title"])}</div>
<div style="margin-top:50px"><div class="rule no" data-pop="0.6"><span class="ic">❌</span><span>{R(s["no"])}</span></div>
<div class="rule ok" data-pop="1.4"><span class="ic">⭕</span><span>{R(s["ok"])}</span></div></div>
<div class="subt" data-in="2.2">{R(s["sub"])}</div></div>{img(who, POS[t], 'data-pop="0.3"')}''', s.get("dur", 4.8))
    if t == "dca":
        tk = s["ticker"]
        res, _ = facts()
        e = res[tk]
        inv = e["invest10y_months"] * 100_000
        return (S_CSS + f'''<div class="main"><div class="pay" data-in="0.1" style="font-size:56px;line-height:1.4">{R(s["title"])}</div>
<div class="vrow" data-in="0.9">넣은 돈 <b>{won(inv)}</b></div>
<div data-shake="3.0,0.6,10"><div class="bal green" style="margin-top:30px" data-in="1.3"><span data-count="1.3,1.6" data-from="{inv}" data-to="{e["v10y_10"]}" data-fmt="won">{won(inv)}</span></div></div>
<div data-pop="3.0"><span class="ret">{(e["v10y_10"] / inv - 1) * 100:+,.0f}%</span></div>
<div class="disc" data-in="3.4">{esc(tk)} 기준 · 매달 같은 날 10만원 · 배당 재투자 · 원달러 환율 반영 · {e["last_date"]} 기준</div></div>
{img(who, POS[t], 'data-pop="3.2"')}''', s.get("dur", 5.6))
    if t == "mdd":
        _, sd = facts()
        rows = ""
        for i, tk in enumerate(s["tickers"]):
            d = sd["tickers"][tk]
            st = 0.6 + 0.9 * i
            rows += f'''<div class="ddrow" data-in="{st:.2f}"><div class="nm">{esc(s.get("labels", {}).get(tk, tk))}</div><div class="pd">{ym(d["peak"])} 고점 → {ym(d["trough"])} 바닥</div>
<div class="ddbar"><i data-grow="{st + 0.3:.2f},0.9,{-d["mdd"] / 100:.3f}"></i></div>
<div class="ddv"><span data-count="{st + 0.3:.2f},0.9" data-from="0" data-to="{r0(d["mdd"])}" data-fmt="num" data-suf="%">0%</span></div></div>'''
        te = 0.6 + 0.9 * len(s["tickers"]) + 0.6
        return (S_CSS + f'''<div class="main"><div class="pay" data-in="0.1" style="font-size:58px">{R(s["title"])}</div><div style="margin-top:36px">{rows}</div>
<div class="subt" data-in="{te:.2f}" style="font-weight:700">{R(s.get("sub", ""))}</div>
<div class="disc" data-in="{te:.2f}">최근 10년 수정주가(배당 포함) 기준 최대 하락률 · 달러 기준 · {sd.get("asof", "")} 기준</div></div>
{img(who, POS[t], f'data-shake="{te:.2f},0.8,8"')}''', te + s.get("hold", 2.4))
    if t == "dip":
        _, sd = facts()
        d = sd["tickers"][s["ticker"]]
        return (S_CSS + f'''<div class="main"><div class="pay" data-in="0.1" style="font-size:56px;line-height:1.4">{R(s["title"])}</div>
<div class="vrow" data-in="0.9">{ym(d["peak"])}부터 <b>{d["dip_months"]}개월</b> 동안</div>
<div class="bal green" style="margin-top:30px" data-in="1.3"><span data-count="1.3,1.6" data-from="0" data-to="{r0(d["dip_ret"])}" data-fmt="num" data-pre="{"+" if d["dip_ret"] >= 0 else ""}" data-suf="%">0%</span></div>
<div class="subt" data-in="3.0" style="font-weight:700">{R(s.get("sub", ""))}</div>
<div class="disc" data-in="3.2">{esc(s["ticker"])} · 고점 달부터 매달 첫 거래일에 같은 금액 · 배당 재투자 · 달러 기준 · {d["last"]} 기준</div></div>
{img(who, POS[t], 'data-pop="3.0"')}''', s.get("dur", 5.6))
    if t == "ask":
        return (S_CSS + f'''<div class="main"><div class="q" data-in="0.1">{R(s["q"])}</div>
<div class="subt" data-in="0.8" style="font-size:52px;font-weight:700">{R(s["sub"])}</div>
<div class="sb" data-pop="1.5" style="margin-top:60px;width:600px;font-size:52px">다음 화:<br>{R(s["next"])}</div>
<div class="disc" data-in="2.0" style="margin-top:auto">에그·덕은 캐릭터예요 · 생활비 등 이야기 속 금액은 예시 · 수익률·하락률은 실제 과거 데이터(배당 재투자, 세금·수수료 미반영) · 과거 수익률은 미래를 보장하지 않음 · 특정 종목 추천 아님</div></div>
{img(who, POS[t], 'data-pop="1.2"')}''', s.get("dur", 4.6))
    raise SystemExit(f"모르는 장면 종류 {t}")


def scenes_story(ep):
    return [scene(ep, s) for s in ep["scenes"]]


def cover_story(ep):
    c = ep["cover"]
    return S_CSS + f'''<div class="main cov"><div class="ep">{esc(ep["series"])} #{ep["no"]:02d}</div>
<div class="h1" style="margin-top:10px">{resolve(c["h1"])}</div>
<div class="bal {c.get("color", "red")}" style="margin-top:30px;font-size:{c.get("size", 150)}px">{resolve(c["big"])}</div>
<div class="h1" style="font-size:80px">{resolve(c["sub"])}</div></div>
{img(c.get("char", "egg"), "right:110px;bottom:260px;width:300px", "")}'''
