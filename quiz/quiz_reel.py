"""황금알 퀴즈 릴스 장면: 결과 숫자 → 물음표 → 힌트 3개 → 정답 받는 법(팔로우 + 댓글)."""
from render import esc, uri

Q_CSS = """<style>
.qbig{font-size:150px;font-weight:900;letter-spacing:-4px;color:#1B2A41;line-height:1.05}
.qmark{display:inline-flex;align-items:center;justify-content:center;width:300px;height:300px;border-radius:60px;
 background:#1E3A5F;color:#F5B800;font-size:220px;font-weight:900;margin:30px 0}
.qrow{display:flex;align-items:baseline;gap:22px;font-size:54px;font-weight:700;color:#3E5674;margin-top:14px}
.qrow b{font-size:64px;color:#1B2A41}
.qret{display:inline-block;margin-top:26px;background:#E5383B;color:#fff;border-radius:999px;padding:14px 40px;font-size:56px;font-weight:900}
.hint{display:flex;gap:26px;align-items:center;background:#fff;border:4px solid #C9D7E6;border-radius:32px;padding:36px 40px;margin-bottom:26px}
.hint .n{flex:none;width:96px;height:96px;border-radius:50%;background:#F5B800;color:#1B2A41;font-size:52px;font-weight:900;display:flex;align-items:center;justify-content:center}
.hint .t{font-size:50px;font-weight:900;line-height:1.3;color:#1B2A41}
.step{display:flex;gap:28px;align-items:center;background:#1E3A5F;color:#fff;border-radius:34px;padding:40px 44px;margin-bottom:28px}
.step .n{flex:none;width:100px;height:100px;border-radius:50%;background:#F5B800;color:#1E3A5F;font-size:54px;font-weight:900;display:flex;align-items:center;justify-content:center}
.step .t{font-size:56px;font-weight:900;line-height:1.25}.step .t small{display:block;font-size:36px;font-weight:700;color:#C9D7E6;margin-top:6px}
.lock{font-size:64px;font-weight:900;color:#1B2A41;margin:10px 0 40px}
</style>"""


def won(v):
    v = int(v)
    if v >= 100_000_000:
        e, m = divmod(v, 100_000_000)
        m //= 10_000
        return f"{e}억 {m:,}만원" if m else f"{e}억원"
    return f"{v // 10_000:,}만원"


def scenes_quiz(ep):
    q = ep["q"]
    kw = ep["keyword"]
    duck = f'<img class="duck" data-pop="{{}}" src="{uri("duck.png")}">'
    out = []
    # 1) 결과부터: 1,200만원 → 8,132만원
    out.append((Q_CSS + f'''<div class="main"><div class="h1" data-in="0.2">월 10만원씩 10년,</div>
<div class="qrow" data-in="0.6">넣은 돈 <b>{won(q["invested"])}</b></div>
<div class="qbig" style="margin-top:50px" data-in="1.0"><span data-count="1.0,1.6" data-from="{q["invested"]}" data-to="{q["value"]}" data-fmt="won">{won(q["invested"])}</span></div>
<div data-pop="2.7"><span class="qret">수익률 {q["ret"]:+.0f}%</span></div>
<div class="h1" style="margin-top:60px" data-in="3.2">이 ETF는 <mark>뭘까요?</mark></div></div>''', 5.0))
    # 2) 물음표 + 힌트
    hs = "".join(f'<div class="hint" data-in="{0.9 + 0.9 * i:.2f}"><div class="n">{i + 1}</div><div class="t">{esc(h)}</div></div>'
                 for i, h in enumerate(q["hints"]))
    out.append((Q_CSS + f'''<div class="main"><div data-pop="0.2"><span class="qmark">?</span></div>{hs}</div>''',
                1.6 + 0.9 * len(q["hints"]) + 1.6))
    # 3) 정답 받는 법
    out.append((Q_CSS + f'''<div class="main"><div class="lock" data-in="0.1">정답은 <mark>DM</mark>으로 📩</div>
<div class="step" data-in="0.6"><div class="n">1</div><div class="t">@golden_duck_lab<br>팔로우<small>다음 퀴즈 정답도 먼저 받아요</small></div></div>
<div class="step" data-in="1.3"><div class="n">2</div><div class="t">댓글에 '{esc(kw)}'<small>자동으로 DM이 도착해요</small></div></div>
<div class="disc" data-in="1.8">{esc(ep["asof"])} 기준 · 배당 재투자 · 원달러 환율 반영 · 과거 수익률은 미래 수익을 보장하지 않음 · 특정 종목 추천 아님</div></div>{duck.format(2.2)}''', 5.2))
    return out


def cover_quiz(ep):
    q = ep["q"]
    return Q_CSS + f'''<div class="main cov">
<div class="h1">월 10만원씩 10년,<br>{won(q["invested"])}이</div>
<div class="qbig" style="margin-top:30px">{won(q["value"])}</div>
<div><span class="qmark" style="width:220px;height:220px;font-size:160px">?</span></div>
<div class="h1">이 ETF는 <mark>뭘까요?</mark></div></div>'''
