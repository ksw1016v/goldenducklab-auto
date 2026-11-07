"""아침 경제 브리핑 릴스: econ/data.json → 원고(econ/episodes/<날짜>.json) + 릴스 장면.

후킹: 데이터에서 '오늘 가장 눈에 띄는 움직임'을 점수로 골라 첫 장면 제목으로 쓴다.
  - 평소 변동폭 대비 큰 움직임(z), 사상 최고·52주 최고/최저, 둥근 숫자 돌파, 연속 상승·하락, 한 달 누적 변화
사용법: python econ/brief.py            (원고 만들고 경로 출력)
"""
import json, sys, math, pathlib, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from render import esc, uri  # noqa: E402

WD = "월화수목금토일"
WEIGHT = {"kospi": 1.4, "kosdaq": 1.15, "usdkrw": 1.4, "spx": 1.2, "ndx": 1.2, "dji": 0.9, "sox": 0.9,
          "jpykrw": 0.9, "eurkrw": 0.7, "dxy": 0.8, "us10y": 0.9, "wti": 0.9, "gold": 1.0, "btc": 1.0, "vix": 0.8}
DISC = "전 거래일 종가 기준 · 정보 제공 목적이며 투자 권유가 아니에요"


# ---------- 숫자 표기 ----------
def fmt(m, v=None):
    v = m["last"] if v is None else v
    k = m["key"]
    if k == "us10y":
        return f"{v:.2f}%"
    if k in ("wti", "gold"):
        return f"${v:,.{1 if k == 'gold' else 2}f}"
    if k == "btc":
        return f"${v:,.0f}"
    if m["group"] == "fx" and k != "dxy":
        return f"{v:,.{2 if k == 'jpykrw' else 1}f}원"
    return f"{v:,.2f}"


def chg_text(m):
    k, c, p = m["key"], m["chg"], m["pct"]
    arrow = "▲" if c > 0 else ("▼" if c < 0 else "-")
    if k == "us10y":
        return f"{arrow} {abs(c) * 100:.1f}bp"
    if m["group"] == "fx" and k != "dxy":
        return f"{arrow} {abs(c):,.{2 if k == 'jpykrw' else 1}f}원 ({p:+.2f}%)"
    return f"{arrow} {abs(p):.2f}%"


def updown(m):
    return "up" if m["chg"] > 0 else ("down" if m["chg"] < 0 else "flat")


def short(m):
    return {"usdkrw": "원/달러 환율", "jpykrw": "원/엔 환율", "eurkrw": "원/유로 환율", "us10y": "미국 10년물 금리",
            "vix": "VIX 공포지수", "sox": "반도체지수"}.get(m["key"], m["name"])


def josa_ga(w):
    ch = w[-1]
    if "가" <= ch <= "힣":
        return "이" if (ord(ch) - 0xAC00) % 28 else "가"
    return "가"


# ---------- 후킹 이벤트 ----------
def events(d):
    ev = []
    for k, m in d["markets"].items():
        w = WEIGHT.get(k, 0.8)
        z, p, up = abs(m["z"]), m["pct"], m["chg"] > 0
        nm = short(m)
        # 큰 움직임
        if z >= 1.3 or (m["group"] in ("kr", "us") and abs(p) >= 2):
            word = ("급등" if up else "급락") if (z >= 2.2 or abs(p) >= 3) else ("큰 폭 상승" if up else "큰 폭 하락")
            if k == "usdkrw":
                amt = f"{abs(m['chg']):.0f}원"
            elif k == "us10y":
                amt = f"{abs(m['chg']) * 100:.0f}bp"
            else:
                amt = f"{abs(p):.1f}%"
            bonus = 25 if (m["group"] in ("kr", "us") and abs(p) >= 3) else 0
            ev.append({"key": k, "type": "move", "score": (z * 10 + bonus) * w,
                       "name": nm, "phrase": f"하루 새 {amt} {word}", "line": f"{nm} 하루 새 {amt} {word}"})
        # 신고가·신저가
        if m["is_ath"] and up:
            ev.append({"key": k, "type": "ath", "score": 40 * w, "name": nm, "phrase": "사상 최고치", "line": f"{nm} 사상 최고치 경신"})
        elif m["is_hi52"] and up:
            ev.append({"key": k, "type": "hi52", "score": 28 * w, "name": nm, "phrase": "1년 중 최고", "line": f"{nm} 52주 최고 수준"})
        if m["is_lo52"] and not up:
            ev.append({"key": k, "type": "lo52", "score": 28 * w, "name": nm, "phrase": "1년 중 최저", "line": f"{nm} 52주 최저 수준"})
        # 둥근 숫자 돌파
        st = m["step"]
        a, b = math.floor(m["prev"] / st), math.floor(m["last"] / st)
        if a != b:
            lvl = (b if up else b + 1) * st   # 하락은 가장 낮게 뚫은 선
            lv = fmt(m, lvl).replace(".00", "").replace(".0원", "원")
            ev.append({"key": k, "type": "cross", "score": (18 + z * 5) * w, "name": nm,
                       "phrase": f"{lv} {'돌파' if up else '아래로'}", "line": f"{nm} {lv} {'돌파' if up else '아래로 내려감'}"})
        # 연속
        n = abs(m["streak"])
        if n >= 4:
            ev.append({"key": k, "type": "streak", "score": (12 + n * 2.5) * w, "name": nm,
                       "phrase": f"{n}일 연속 {'상승' if m['streak'] > 0 else '하락'}",
                       "line": f"{nm} {n}일 연속 {'상승' if m['streak'] > 0 else '하락'}"})
        # 한 달 누적
        mm = m["chg_1m_pct"]
        if k != "us10y" and ((m["group"] in ("kr", "us") and abs(mm) >= 10) or (k == "vix" and abs(mm) >= 40) or
                             (m["group"] == "fx" and abs(mm) >= 3)):
            ev.append({"key": k, "type": "month", "score": (10 + abs(mm) * 0.6) * w, "name": nm,
                       "phrase": f"한 달 새 {mm:+.0f}%", "line": f"{nm} 한 달 새 {mm:+.1f}%"})
    ev.sort(key=lambda e: -e["score"])
    return ev


def pick(ev):
    """첫 장면 후킹 1개 + 오늘의 포인트 3개(같은 지표 중복 없이)."""
    hook = ev[0] if ev else None
    pts, seen = [], set()
    for e in ev:
        if e["key"] in seen:
            continue
        seen.add(e["key"])
        pts.append(e)
        if len(pts) == 4:
            break
    same = [e for e in ev if hook and e["key"] == hook["key"] and e is not hook]
    pref = {"month": 0, "lo52": 1, "hi52": 1, "ath": 1, "streak": 2, "cross": 3, "move": 4}
    extra = sorted(same, key=lambda e: pref[e["type"]])[:1]
    return hook, pts, extra


def kday(s):
    d = datetime.date.fromisoformat(s)
    return f"{d.month}/{d.day}({WD[d.weekday()]})"


# ---------- 원고 ----------
def build():
    d = json.loads((ROOT / "econ" / "data.json").read_text(encoding="utf-8"))
    M = d["markets"]
    ev = events(d)
    hook, pts, extra = pick(ev)
    us_date = M["spx"]["date"]
    kr_date = M["kospi"]["date"]
    slug_date = max(us_date, kr_date).replace("-", "")
    hm = M[hook["key"]] if hook else M["spx"]
    sub = [extra[0]["line"]] if extra else []
    for e in pts[1:]:
        if len(sub) >= 2:
            break
        sub.append(e["line"])
    mac = d.get("macro", {})
    man = d.get("manual", {})

    def mrow(k):
        m = M[k]
        return {"key": k, "name": m["name"], "value": fmt(m), "last": m["last"], "dec": m["dec"], "chg": chg_text(m),
                "dir": updown(m), "spark": m["m1"], "date": m["date"], "m1": m["chg_1m_pct"]}

    macro = []
    if "CUUR0000SA0" in mac:
        c = mac["CUUR0000SA0"]
        macro.append(["미국 물가(CPI)", f"{c['value']:.1f}%", f"{int(c['date'][5:])}월 · 전월 {c['prev']:.1f}%"])
    if "CUUR0000SA0L1E" in mac:
        c = mac["CUUR0000SA0L1E"]
        macro.append(["근원 물가", f"{c['value']:.1f}%", f"{int(c['date'][5:])}월 · 전월 {c['prev']:.1f}%"])
    if "LNS14000000" in mac:
        c = mac["LNS14000000"]
        macro.append(["미국 실업률", f"{c['value']:.1f}%", f"{int(c['date'][5:])}월 · 전월 {c['prev']:.1f}%"])
    if "CES0000000001" in mac:
        c = mac["CES0000000001"]
        macro.append(["미국 일자리", f"{c['value'] / 10:+.1f}만개", f"{int(c['date'][5:])}월 · 전월 {c['prev'] / 10:+.1f}만개"])
    if man.get("fed_hi"):
        macro.append(["미국 기준금리", f"{man['fed_lo']:.2f}~{man['fed_hi']:.2f}%", f"{kday(man['fed_date'])} 결정"])
    if man.get("bok_rate"):
        macro.append(["한국 기준금리", f"{man['bok_rate']:.2f}%", f"{kday(man['bok_rate_date'])} 결정"])

    ep = {"series": "아침 경제 브리핑", "theme": "brief", "kind": "brief", "no": 0, "slug": f"brief-{slug_date}",
          "date_us": us_date, "date_kr": kr_date,
          "hook": {"key": hook["key"] if hook else "spx", "name": hook["name"] if hook else "S&P 500",
                   "phrase": hook["phrase"] if hook else "오늘의 시장", "value": fmt(hm), "last": hm["last"], "dec": hm["dec"],
                   "chg": chg_text(hm), "dir": updown(hm), "sub": sub},
          "us": [mrow(k) for k in ("spx", "ndx", "dji", "sox") if k in M],
          "kr": [mrow(k) for k in ("kospi", "kosdaq") if k in M],
          "fx": [mrow(k) for k in ("usdkrw", "jpykrw", "eurkrw", "dxy") if k in M],
          "cmd": [mrow(k) for k in ("us10y", "wti", "gold", "btc", "vix") if k in M],
          "macro": macro, "points": [e["line"] for e in pts[:3]],
          "events": ev[:8]}
    ep["caption"] = caption(ep, M)
    out = ROOT / "econ" / "episodes"
    out.mkdir(exist_ok=True)
    p = out / f"{slug_date}.json"
    p.write_text(json.dumps(ep, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def caption(ep, M):
    h = ep["hook"]
    em = "📉" if h["dir"] == "down" else "📈"
    L = [f"{h['name']} {h['phrase']} {em}", f"{kday(ep['date_us'])} 마감 기준, 오늘의 아침 경제 브리핑이에요 🦆", ""]
    def block(title, rows):
        L.append(title)
        for r in rows:
            c = r['chg'].replace('▲ ', '+').replace('▼ ', '-').replace('- ', '-')
            if "원 (" in c:
                c = c.replace(" (", ", ").rstrip(")")
            L.append(f"{r['name']} {r['value']} ({c})")
        L.append("")
    block("🇺🇸 미국 증시", ep["us"])
    block(f"🇰🇷 한국 증시 ({kday(ep['date_kr'])})", ep["kr"])
    block("💱 환율", ep["fx"])
    block("📊 금리·원자재·코인", ep["cmd"])
    if ep["macro"]:
        L.append("📌 경제지표")
        L += [f"{a} {b} ({c})" for a, b, c in ep["macro"]]
        L.append("")
    L.append("✔ 오늘의 포인트")
    L += [f"· {p}" for p in ep["points"]]
    L += ["", f"📌 {DISC}. 지표는 미국 노동통계국·한국은행·연준 발표 기준이에요.", "",
          "매일 아침 시장을 한눈에 정리해 드려요. 저장해 두고 출근길에 확인하세요 💛", "",
          "#경제브리핑 #환율 #코스피 #미국증시 #나스닥 #재테크 #골든덕랩"]
    return "\n".join(L)


# ---------- 릴스 ----------
BRIEF_REEL = """
body{background:#11151D;color:#F3F1EA}
.frame{border-color:#F5B800;background:#11151D}
.tag{background:#F5B800;color:#11151D}
.foot{border-top-color:#3A4458;color:#C9CED8}.foot span:last-child{color:#F5B800}
.kick{color:#F5B800}
mark{background:linear-gradient(transparent 55%,rgba(245,184,0,.55) 55%);color:#fff}
.up{color:#FF5B5B}.down{color:#4E8FFF}.flat{color:#9AA4B5}
.hookname{font-size:104px;font-weight:900;letter-spacing:-3px;line-height:1.1;color:#fff}
.hookphrase{font-size:100px;font-weight:900;letter-spacing:-3px;line-height:1.15;margin-top:8px}
.hookval{font-size:120px;font-weight:900;letter-spacing:-3px;margin-top:60px;color:#fff}
.hookchg{font-size:58px;font-weight:900;margin-top:6px}
.hooksub{margin-top:56px}
.hooksub div{font-size:44px;font-weight:700;color:#C9CED8;padding:20px 0;border-top:2px solid #2A3345}
.sec{font-size:84px;font-weight:900;letter-spacing:-2px;margin-bottom:12px;color:#fff}
.secd{font-size:36px;color:#9AA4B5;margin-bottom:40px;font-weight:500}
.mk{background:#1B2130;border:3px solid #2A3345;border-radius:30px;padding:30px 36px 22px;margin-bottom:24px}
.mk .r1{display:flex;justify-content:space-between;align-items:baseline}
.mk .nm{font-size:42px;font-weight:700;color:#C9CED8}
.mk .vl{font-size:66px;font-weight:900;color:#fff;letter-spacing:-1px}
.mk .r2{display:flex;justify-content:space-between;align-items:center;margin-top:4px}
.mk .cg{font-size:42px;font-weight:900}
.mk .m1{font-size:30px;color:#9AA4B5}
.mk svg{display:block;margin-top:10px}
.mk.sm{padding:22px 34px 18px;margin-bottom:18px}.mk.sm .vl{font-size:56px}.mk.sm .nm{font-size:38px}.mk.sm .cg{font-size:36px}
.mg{display:grid;grid-template-columns:1fr 1fr;gap:22px}
.mc{background:#1B2130;border:3px solid #2A3345;border-radius:28px;padding:30px 30px 26px}
.mc .a{font-size:36px;font-weight:700;color:#C9CED8}.mc .b{font-size:70px;font-weight:900;color:#F5B800;letter-spacing:-1px;margin-top:6px}
.mc .c{font-size:28px;color:#9AA4B5;margin-top:4px}
.pt{display:flex;gap:26px;align-items:flex-start;background:#1B2130;border:3px solid #2A3345;border-radius:30px;padding:40px 40px;margin-bottom:28px}
.pt .n{flex:none;width:76px;height:76px;border-radius:50%;background:#F5B800;color:#11151D;font-size:42px;font-weight:900;display:flex;align-items:center;justify-content:center}
.pt .t{font-size:52px;font-weight:900;line-height:1.3;color:#fff}
.disc{color:#7E879A}
.end2 .h2{color:#fff}.end2 .lead{color:#C9CED8}
.cta{background:#F5B800;color:#11151D}
.duck{width:280px;bottom:170px}
"""


def spark(vals, dirc, w=760, h=80, start=0.0):
    if not vals or len(vals) < 2:
        return ""
    lo, hi = min(vals), max(vals)
    rng = (hi - lo) or 1
    pts = " ".join(f"{i * w / (len(vals) - 1):.1f},{h - 6 - (v - lo) / rng * (h - 12):.1f}" for i, v in enumerate(vals))
    col = {"up": "#FF5B5B", "down": "#4E8FFF"}.get(dirc, "#9AA4B5")
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}"><polyline points="{pts}" fill="none" stroke="{col}" stroke-width="5" '
            f'stroke-linejoin="round" stroke-linecap="round" pathLength="1" stroke-dasharray="1" data-draw="{start:.2f}"/></svg>')


def mk_card(r, t, small=False, sp=True):
    dec = 0 if r["key"] == "btc" else (2 if r["key"] in ("us10y", "jpykrw") else (1 if r["key"] in ("usdkrw", "eurkrw", "gold") else 2))
    pre = "$" if r["key"] in ("wti", "gold", "btc") else ""
    suf = "원" if r["key"] in ("usdkrw", "jpykrw", "eurkrw") else ("%" if r["key"] == "us10y" else "")
    base = r["last"] * (0.97 if r["dir"] != "down" else 1.03)
    return (f'<div class="mk{" sm" if small else ""}" data-in="{t:.2f}"><div class="r1"><span class="nm">{esc(r["name"])}</span>'
            f'<span class="vl" data-count="{t + 0.1:.2f},0.9" data-from="{base}" data-to="{r["last"]}" data-fmt="num" data-dec="{dec}" '
            f'data-pre="{pre}" data-suf="{suf}">{esc(r["value"])}</span></div>'
            f'<div class="r2"><span class="cg {r["dir"]}">{esc(r["chg"])}</span><span class="m1">1개월 {r["m1"]:+.1f}%</span></div>'
            + (spark(r["spark"], "up" if r["m1"] > 0 else "down", start=t + 0.3) if sp else "") + "</div>")


def scenes_brief(ep):
    h = ep["hook"]
    duck = f'<img class="duck" data-pop="{{}}" src="{uri("duck.png")}">'
    out = []
    # 1) 후킹
    dec = h["dec"] if h["key"] not in ("btc",) else 0
    pre = "$" if h["key"] in ("wti", "gold", "btc") else ""
    suf = "원" if h["key"] in ("usdkrw", "jpykrw", "eurkrw") else ("%" if h["key"] == "us10y" else "")
    base = h["last"] * (1.04 if h["dir"] == "down" else 0.96)
    subs = "".join(f'<div data-in="{2.4 + 0.45 * i:.2f}">{esc(s)}</div>' for i, s in enumerate(h["sub"]))
    out.append((f'''<div class="main"><div class="kick" data-in="0.15">{kday(ep["date_us"])} 마감 · 아침 경제 브리핑</div>
<div class="hookname" data-in="0.4">{esc(h["name"])}</div>
<div class="hookphrase {h["dir"]}" data-pop="0.8">{esc(h["phrase"])}</div>
<div class="hookval" data-in="1.3"><span data-count="1.3,1.0" data-from="{base}" data-to="{h["last"]}" data-fmt="num" data-dec="{dec}" data-pre="{pre}" data-suf="{suf}">{esc(h["value"])}</span></div>
<div class="hookchg {h["dir"]}" data-in="1.9">{esc(h["chg"])}</div>
<div class="hooksub">{subs}</div></div>{duck.format(3.2)}''', 5.6))

    # 2) 미국 증시
    cards = "".join(mk_card(r, 0.6 + 0.45 * i, small=i >= 2, sp=i < 2) for i, r in enumerate(ep["us"]))
    out.append((f'<div class="main"><div class="sec" data-in="0.1">🇺🇸 미국 증시</div><div class="secd" data-in="0.25">{kday(ep["date_us"])} 마감</div>{cards}</div>',
                2.4 + 0.45 * len(ep["us"])))
    # 3) 한국 증시
    cards = "".join(mk_card(r, 0.6 + 0.5 * i) for i, r in enumerate(ep["kr"]))
    out.append((f'<div class="main"><div class="sec" data-in="0.1">🇰🇷 한국 증시</div><div class="secd" data-in="0.25">{kday(ep["date_kr"])} 마감</div>{cards}</div>',
                3.6))
    # 4) 환율
    cards = "".join(mk_card(r, 0.6 + 0.45 * i, small=i > 0, sp=i == 0) for i, r in enumerate(ep["fx"]))
    out.append((f'<div class="main"><div class="sec" data-in="0.1">💱 환율</div><div class="secd" data-in="0.25">{kday(ep["date_us"])} 기준</div>{cards}</div>',
                2.6 + 0.45 * len(ep["fx"])))
    # 5) 금리·원자재·코인
    cards = "".join(mk_card(r, 0.5 + 0.35 * i, small=True, sp=False) for i, r in enumerate(ep["cmd"]))
    out.append((f'<div class="main"><div class="sec" data-in="0.1">📊 금리·원자재·코인</div><div class="secd" data-in="0.25">{kday(ep["date_us"])} 기준</div>{cards}</div>',
                2.6 + 0.35 * len(ep["cmd"])))
    # 6) 경제지표
    if ep["macro"]:
        cells = "".join(f'<div class="mc" data-in="{0.6 + 0.3 * i:.2f}"><div class="a">{esc(a)}</div><div class="b">{esc(b)}</div><div class="c">{esc(c)}</div></div>'
                        for i, (a, b, c) in enumerate(ep["macro"]))
        out.append((f'<div class="main"><div class="sec" data-in="0.1">📌 경제지표</div><div class="secd" data-in="0.25">가장 최근 발표 기준</div><div class="mg">{cells}</div></div>',
                    2.8 + 0.3 * len(ep["macro"])))
    # 7) 오늘의 포인트
    pts = "".join(f'<div class="pt" data-in="{0.7 + 0.6 * i:.2f}"><div class="n">{i + 1}</div><div class="t">{esc(p)}</div></div>' for i, p in enumerate(ep["points"]))
    out.append((f'<div class="main"><div class="sec" data-in="0.1" style="margin-bottom:50px">오늘의 <mark>포인트</mark></div>{pts}<div class="disc" data-in="0.5">{DISC}</div></div>',
                2.8 + 0.6 * len(ep["points"])))
    # 8) 마무리
    out.append((f'''<div class="main end2"><img data-zoom="0.1" src="{uri("logo.png")}">
<div class="h2" data-in="0.7" style="margin-bottom:16px">매일 아침,<br>시장을 한눈에</div>
<div class="lead" data-in="1.1" style="margin:0;font-size:40px">저장해 두고 출근길에 확인하세요</div>
<div data-in="1.5" style="margin-top:44px"><span class="cta">@golden_duck_lab 팔로우</span></div></div>''', 4.2))
    return out


def cover_brief(ep):
    h = ep["hook"]
    return f'''<div class="main cov"><div class="kick">{kday(ep["date_us"])} 마감 · 아침 경제 브리핑</div>
<div class="hookname">{esc(h["name"])}</div><div class="hookphrase {h["dir"]}">{esc(h["phrase"])}</div>
<div class="hookval">{esc(h["value"])}</div><div class="hookchg {h["dir"]}">{esc(h["chg"])}</div>
</div><img class="duck covduck" src="{uri("duck.png")}">'''


if __name__ == "__main__":
    print(build().relative_to(ROOT))
