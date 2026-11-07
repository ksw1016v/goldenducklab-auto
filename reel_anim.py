"""ETF 릴스의 장면과 애니메이션 정의 (reel.py가 사용).

각 장면은 HTML 한 장 + 시간표(data-* 속성)로 만들고, 페이지 안의 setT(t)가
그 시각의 모습(나타나기, 숫자 카운트업, 황금알 떨어지기, 오리 튀어나오기)을 그린다.
"""
import json, pathlib
from render import esc, uri

ROOT = pathlib.Path(__file__).parent

ANIM_JS = r"""
<script>
const ease = x => 1 - Math.pow(1 - x, 3);
const clamp = x => Math.min(1, Math.max(0, x));
const won = v => { v = Math.round(v);
  if (v >= 1e8) { const e = Math.floor(v / 1e8), m = Math.floor((v % 1e8) / 1e4);
    return m ? `${e}억 ${m.toLocaleString('en-US')}만원` : `${e}억원`; }
  return `${Math.floor(v / 1e4).toLocaleString('en-US')}만원`; };
window.setT = (t) => {
  const dur = +document.body.dataset.dur, out = clamp((dur - t) / 0.3);
  document.querySelectorAll('[data-in]').forEach(el => {
    const p = clamp((t - +el.dataset.in) / 0.4);
    el.style.opacity = p * out; el.style.transform = `translateY(${(1 - ease(p)) * 36}px)`; });
  document.querySelectorAll('[data-pop]').forEach(el => {
    const p = clamp((t - +el.dataset.pop) / 0.5);
    const k = p <= 0 ? 0.3 : (p < 1 ? 0.3 + 0.7 * ease(p) + 0.18 * Math.sin(p * Math.PI) : 1);
    el.style.opacity = clamp(p * 2.5) * out; el.style.transform = `scale(${k})`; });
  document.querySelectorAll('[data-drop]').forEach(el => {
    const p = clamp((t - +el.dataset.drop) / 0.55);
    let y = -160 * Math.pow(1 - Math.min(1, p / 0.7), 2);
    if (p > 0.7) y = -26 * Math.sin((p - 0.7) / 0.3 * Math.PI);
    el.style.opacity = (p > 0 ? 1 : 0) * out; el.style.transform = `translateY(${y}px)`; });
  document.querySelectorAll('[data-count]').forEach(el => {
    const [s, d] = el.dataset.count.split(',').map(Number);
    const p = clamp((t - s) / d), v = +el.dataset.from + (+el.dataset.to - +el.dataset.from) * ease(p);
    el.textContent = el.dataset.fmt === 'year' ? `${Math.round(v)}년` : won(v); });
  document.querySelectorAll('[data-zoom]').forEach(el => {
    const p = clamp((t - +el.dataset.zoom) / 0.6);
    el.style.opacity = clamp(p * 2) * out; el.style.transform = `scale(${0.6 + 0.4 * ease(p)})`; });
};
</script>
"""


def raw_numbers(ticker):
    data = json.loads((ROOT / "etf" / "results.json").read_text(encoding="utf-8"))
    return next(x for x in data["etfs"] if x["ticker"].upper() == ticker.upper())


def scenes(ep):
    """[(inner_html, 길이초)] 반환."""
    s = ep["slides"]
    info = next(x for x in s if x["type"] == "etf_info")
    notes = next(x for x in s if x["type"] == "list" and "알아둘" in x["title"])
    end = s[-1]
    e = raw_numbers(info["ticker"])
    t = info["ticker"]
    label = t if not t.isdigit() else info["name"]
    big = 230 if len(label) <= 5 else (150 if len(label) <= 8 else 100)
    years = [y for y in (5, 10, 20) if e.get(f"v{y}y_10") not in ("", None)]
    longest = years[-1]
    duck = f'<img class="duck" data-pop="{{}}" src="{uri("duck.png")}">'
    out = []

    # 1) 표지: 티커 → 월 10만원씩 → 기간 카운트업 → 모았다면? → 설명 → 오리
    out.append((f'''<div class="main"><div class="kick" data-in="0.2">{esc(info["category"])}</div>
<div class="big" data-in="0.45" style="font-size:{big}px"><mark>{esc(label)}</mark></div>
<div class="h1"><span data-in="1.2">월 10만원씩</span><br>
<span data-in="1.6"><span data-count="1.6,1.0" data-from="1" data-to="{longest}" data-fmt="year">1년</span></span><br>
<span data-in="2.8">모았다면?</span></div>
<div class="subt" data-in="3.4">{esc(info["rows"][0][1])}에<br>투자하는 ETF</div></div>{duck.format(1.0)}''', 5.0))

    # 2) ETF 소개: 줄마다 차례로
    kv = "".join(f'<div class="kv" data-in="{1.7 + 0.45 * i:.2f}"><span>{esc(a)}</span><b>{esc(b)}</b></div>'
                 for i, (a, b) in enumerate(info["rows"]))
    out.append((f'''<div class="main"><div class="big" data-in="0.1" style="font-size:{min(big, 150)}px">{esc(label)}</div>
<div class="ename" data-in="0.45">{esc(info["name"])}</div><div class="chip" data-in="0.8">{esc(info["category"])}</div>
<div class="lead" data-in="1.15" style="margin-top:40px;font-size:46px">{esc(info["desc"])}</div>
<div style="font-size:40px">{kv}</div></div>''', 5.0 + 0.45 * max(0, len(info["rows"]) - 4)))

    # 3) 월 10만원 적립: 5년 → 10년 → 20년이 차례로, 원금에서 지금 금액까지 카운트업, 수익률은 그 뒤에
    def drow(y, amt, at, dur, hi):
        months = e[f"invest{y}y_months"]
        principal = amt * 10_000 * months
        val = e[f"v{y}y_{amt}"]
        ret = e[f"ret{y}y_pct"]
        cls = "dret neg" if ret < 0 else "dret"
        return (f'<div class="drow{" hi" if hi else ""}" data-in="{at:.2f}"><div class="dy">{y}년</div><div class="dv">'
                f'<div class="dpr">원금 {principal // 10_000:,}만원</div>'
                f'<div class="dval" data-count="{at:.2f},{dur:.2f}" data-from="{principal}" data-to="{val}">{principal // 10_000:,}만원</div></div>'
                f'<div class="{cls}" data-in="{at + dur + 0.1:.2f}">{ret:+.0f}%</div></div>')

    rows, at = "", 1.0
    for i, y in enumerate(years):
        dur = 1.4 + 0.2 * i
        rows += drow(y, 10, at, dur, y == longest)
        at += dur + 0.6
    egg_at = at + 0.1
    eggs = '<div class="eggs">' + "".join(f'<div class="egg" data-drop="{egg_at + 0.3 * k:.2f}"></div>' for k in range(3)) + "</div>"
    note = next(x for x in s if x["type"] == "dca").get("note", "")
    out.append((f'''<div class="main"><div class="h2"><span data-in="0.1"><mark>매달 10만원씩</mark></span><br><span data-in="0.45">모았다면 지금은?</span></div>
{rows}{eggs}<div class="disc" data-in="0.6">{esc(note)}</div></div>{duck.format(f"{egg_at - 0.2:.2f}")}''', egg_at + 2.2))

    # 4) 금액을 늘리면? 월 30만·50만원을 같은 기간으로 카운트업
    def mrow(amt, at):
        months = e[f"invest{longest}y_months"]
        principal = amt * 10_000 * months
        val = e[f"v{longest}y_{amt}"]
        return (f'<div class="mrow" data-in="{at:.2f}"><div class="ml">월 {amt}만원 × {longest}년</div>'
                f'<div class="mp">원금 {principal // 10_000:,}만원</div>'
                f'<div class="mv" data-count="{at:.2f},1.5" data-from="{principal}" data-to="{val}">{principal // 10_000:,}만원</div></div>')
    ret = e[f"ret{longest}y_pct"]
    out.append((f'''<div class="main"><div class="h2" data-in="0.1"><mark>금액을 늘리면?</mark></div>
{mrow(30, 0.6)}{mrow(50, 2.5)}<div class="say" data-in="4.3">같은 {ret:+.0f}%라도 금액이 클수록 황금알이 커져요</div>
<div class="disc" data-in="0.6">{esc(note)}</div></div>''', 6.0))

    # 5) 알아둘 점: 항목이 하나씩
    items = "".join(f'<div class="item" data-in="{0.8 + 0.8 * j:.2f}"><div class="num">{j + 1}</div><div><div class="it">{esc(a)}</div><div class="id">{esc(b)}</div></div></div>'
                    for j, (a, b) in enumerate(notes["items"]))
    out.append((f'<div class="main"><div class="h2" data-in="0.1">{esc(notes["title"])}</div>{items}</div>', 5.2))

    # 6) 마무리: 로고 확대 → 문구 → 팔로우 버튼 → 다음 편 예고
    out.append((f'''<div class="main end2"><img data-zoom="0.1" src="{uri("logo.png")}">
<div class="h2" data-in="0.8" style="margin-bottom:16px">{esc(end["title"])}</div>
<div class="lead" data-in="1.2" style="margin:0;font-size:40px">{esc(end["sub"])}</div>
<div data-in="1.6" style="margin-top:44px"><span class="cta">{esc(end["cta"])}</span></div>
<div class="next" data-in="2.0" style="font-size:36px">{esc(end.get("next", ""))}</div></div>''', 5.5))
    return out


def cover(ep):
    """릴스 미리보기(표지) 이미지용 HTML. 프로필 격자에서 가운데만 잘려 보여도 핵심이 보이게 중앙에 모은다."""
    s = ep["slides"]
    info = next(x for x in s if x["type"] == "etf_info")
    e = raw_numbers(info["ticker"])
    t = info["ticker"]
    label = t if not t.isdigit() else info["name"]
    lines = label.split(" ", 1) if " " in label else [label]
    units = max(sum(1.0 if ord(c) > 0x3000 else 0.66 for c in ln) for ln in lines)
    big = min(260, int(840 / units))
    years = [y for y in (5, 10, 20) if e.get(f"v{y}y_10") not in ("", None)]
    y = years[-1]
    principal = 10 * 10_000 * e[f"invest{y}y_months"]

    def won(v):
        v = int(v)
        if v >= 100_000_000:
            a, m = divmod(v, 100_000_000)
            m //= 10_000
            return f"{a}억 {m:,}만원" if m else f"{a}억원"
        return f"{v // 10_000:,}만원"

    return f'''<div class="main cov">
<div class="kick">{esc(info["category"])}</div>
<div class="big" style="font-size:{big}px;line-height:1.1">{"<br>".join(f"<mark>{esc(x)}</mark>" for x in lines)}</div>
<div class="h1">월 10만원씩<br>{y}년 모았다면?</div>
<div class="covnum"><span class="cp">원금 {won(principal)}</span><span class="ca">→</span><span class="cv">{won(e[f"v{y}y_10"])}</span></div>
</div><img class="duck covduck" src="{uri("duck.png")}">'''


# ───────────── 현금흐름 황금알 (income) ─────────────

def income_numbers(ticker):
    d = json.loads((ROOT / "etf" / "income.json").read_text(encoding="utf-8"))
    return next(x for x in d["etfs"] if x["ticker"].upper() == ticker.upper())


def _label_lines(info):
    t = info["ticker"]
    label = t if not t.isdigit() else info["name"]
    lines = label.split(" ", 1) if " " in label else [label]
    units = max(sum(1.0 if ord(c) > 0x3000 else 0.66 for c in ln) for ln in lines)
    return label, lines, units


def scenes_income(ep):
    s = ep["slides"]
    info = next(x for x in s if x["type"] == "etf_info")
    needs = [x for x in s if x["type"] == "need"]
    lists = [x for x in s if x["type"] == "list"]
    record, notes = lists[0], lists[1]
    end = s[-1]
    e = income_numbers(info["ticker"])
    label, lines, units = _label_lines(info)
    big = min(230, int(840 / units))
    duck = f'<img class="duck" data-pop="{{}}" src="{uri("duck.png")}">'
    out = []

    # 1) 표지: 티커 → 월 0원에서 100만원까지 카운트업 → 받으려면?
    mark = "<br>".join(f"<mark>{esc(x)}</mark>" for x in lines)
    out.append((f'''<div class="main"><div class="kick" data-in="0.2">현금흐름 황금알 · {esc(e["freq"])} 배당</div>
<div class="big" data-in="0.45" style="font-size:{big}px;line-height:1.1">{mark}</div>
<div class="h1"><span data-in="1.2">로 매달</span><br>
<span data-in="1.5"><span data-count="1.5,1.2" data-from="0" data-to="1000000">0만원</span></span><br>
<span data-in="2.9">받으려면?</span></div>
<div class="subt" data-in="3.5">배당수익률 연 {e["yield_pct"]:.1f}%로<br>계산해 봐요</div></div>{duck.format(1.0)}''', 5.2))

    # 2) 소개
    kv = "".join(f'<div class="kv" data-in="{1.7 + 0.45 * i:.2f}"><span>{esc(a)}</span><b>{esc(b)}</b></div>'
                 for i, (a, b) in enumerate(info["rows"]))
    out.append((f'''<div class="main"><div class="big" data-in="0.1" style="font-size:{min(big, 150)}px;line-height:1.1">{"<br>".join(esc(x) for x in lines)}</div>
<div class="ename" data-in="0.45">{esc(info["name"])}</div><div class="chip" data-in="0.8">{esc(info["category"])}</div>
<div class="lead" data-in="1.15" style="margin-top:40px;font-size:46px">{esc(info["desc"])}</div>
<div style="font-size:40px">{kv}</div></div>''', 5.0 + 0.45 * max(0, len(info["rows"]) - 4)))

    note = needs[0].get("note", "")

    # 3) 필요한 원금: 월 50만·100만·300만 차례로 0원에서 카운트업
    rows, at = "", 1.0
    for a in (50, 100, 300):
        need = e[f"need_{a}"]
        rows += (f'<div class="drow{" hi" if a == 100 else ""}" data-in="{at:.2f}"><div class="dy" style="font-size:34px;line-height:1.15;text-align:center">월{a}만</div>'
                 f'<div class="dv"><div class="dpr">매달 {a}만원 받으려면</div>'
                 f'<div class="dval" data-count="{at:.2f},1.5" data-from="0" data-to="{need}">0만원</div></div></div>')
        at += 2.1
    eggs = '<div class="eggs">' + "".join(f'<div class="egg" data-drop="{at + 0.3 * k:.2f}"></div>' for k in range(3)) + "</div>"
    out.append((f'''<div class="main"><div class="h2" style="font-size:84px"><span data-in="0.1">매달 <mark>이만큼</mark> 받으려면</span><br><span data-in="0.45">얼마가 필요할까?</span></div>
{rows}{eggs}<div class="disc" data-in="0.6">{esc(note)}</div></div>''', at + 2.2))

    # 4) 꾸준히 모았다면: 넣은 돈 → 지금 금액, 그리고 매달 받는 배당
    m = e["dca_months"]
    period = f"{m // 12}년" if m % 12 == 0 else f"{m}개월"
    inv = e["dca_invested"]
    out.append((f'''<div class="main"><div class="h2"><span data-in="0.1">월 50만원씩</span><br><span data-in="0.45"><mark>{period}</mark> 모았다면?</span></div>
<div class="mrow" data-in="1.0"><div class="ml">넣은 돈 {inv // 10_000:,}만원</div><div class="mp">지금 금액 (분배금 재투자)</div>
<div class="mv" data-count="1.0,1.6" data-from="{inv}" data-to="{e["dca_value"]}">{inv // 10_000:,}만원</div></div>
<div class="mrow hi" data-in="3.0"><div class="ml">매달 받는 배당 (세전)</div><div class="mp">지금 배당수익률 기준</div>
<div class="mv" data-count="3.0,1.4" data-from="0" data-to="{e["dca_monthly_income"]}">0만원</div></div>
<div class="say" data-in="4.8">모아 둔 돈이 매달 월급처럼 들어와요</div>
<div class="disc" data-in="0.6">{esc(note)}</div></div>''', 6.6))

    # 5) 배당 기록 / 6) 알아둘 점
    for blk, dur in ((record, 5.0), (notes, 5.4)):
        items = "".join(f'<div class="item" data-in="{0.8 + 0.8 * j:.2f}"><div class="num">{j + 1}</div><div><div class="it">{esc(a)}</div>'
                        + (f'<div class="id">{esc(b)}</div>' if b else "") + '</div></div>' for j, (a, b) in enumerate(blk["items"]))
        tip = f'<div class="tip" data-in="{0.8 + 0.8 * len(blk["items"]) + 0.2:.2f}">{blk["tip"]}</div>' if blk.get("tip") else ""
        out.append((f'<div class="main"><div class="h2" data-in="0.1">{blk["title"]}</div>{items}{tip}</div>', dur))

    # 7) 마무리
    out.append((f'''<div class="main end2"><img data-zoom="0.1" src="{uri("logo.png")}">
<div class="h2" data-in="0.8" style="margin-bottom:16px">{end["title"]}</div>
<div class="lead" data-in="1.2" style="margin:0;font-size:40px">{esc(end["sub"])}</div>
<div data-in="1.6" style="margin-top:44px"><span class="cta">{esc(end["cta"])}</span></div>
<div class="next" data-in="2.0" style="font-size:36px">{esc(end.get("next", ""))}</div></div>''', 5.5))
    return out


def cover_income(ep):
    info = next(x for x in ep["slides"] if x["type"] == "etf_info")
    e = income_numbers(info["ticker"])
    label, lines, units = _label_lines(info)
    big = min(250, int(840 / units))

    def won(v):
        v = int(v)
        if v >= 100_000_000:
            a, mm = divmod(v, 100_000_000)
            mm //= 10_000
            return f"{a}억 {mm:,}만원" if mm else f"{a}억원"
        return f"{v // 10_000:,}만원"

    mark = "<br>".join(f"<mark>{esc(x)}</mark>" for x in lines)
    return f'''<div class="main cov">
<div class="kick">현금흐름 황금알 · {esc(e["freq"])} 배당</div>
<div class="big" style="font-size:{big}px;line-height:1.1">{mark}</div>
<div class="h1">로 매달 100만원<br>받으려면?</div>
<div class="covnum"><span class="cp">배당수익률 연 {e["yield_pct"]:.1f}%</span><span class="ca">→</span><span class="cv">{won(e["need_100"])}</span></div>
</div><img class="duck covduck" src="{uri("duck.png")}">'''
