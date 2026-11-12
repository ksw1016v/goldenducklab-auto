"""황금알 퀴즈 릴스 장면 (긴장감 버전).
숫자가 흔들리며 불어남 → 가려진 정답 + 줄어드는 타이머 + 힌트 → 3·2·1 카운트다운 → 정답은 DM으로.
"""
from render import esc, uri

Q_CSS = """<style>
.qbig{font-size:150px;font-weight:900;letter-spacing:-4px;color:#1B2A41;line-height:1.05}
.qrow{display:flex;align-items:baseline;gap:22px;font-size:54px;font-weight:700;color:#3E5674;margin-top:14px}
.qrow b{font-size:64px;color:#1B2A41}
.qline{font-size:50px;font-weight:700;color:#3E5674;margin-top:14px}.qline b{font-size:58px;color:#1B2A41}
.qret{display:inline-block;margin-top:26px;background:#E5383B;color:#fff;border-radius:999px;padding:14px 40px;font-size:56px;font-weight:900}
.warn{display:inline-block;align-self:flex-start;background:#E5383B;color:#fff;font-size:40px;font-weight:900;padding:10px 28px;border-radius:999px;margin-bottom:26px}
.ansbox{display:flex;align-items:center;gap:28px;background:#1E3A5F;border-radius:36px;padding:34px 40px;margin-bottom:22px}
.ansbox .al{font-size:50px;font-weight:900;color:#F5B800}
.rds{display:flex;gap:14px}
.rd{display:inline-block;width:92px;height:110px;border-radius:16px;background:repeating-linear-gradient(45deg,#0F2338 0 14px,#2B4A6E 14px 28px)}
.timer{height:26px;background:#D5E0EC;border-radius:999px;overflow:hidden;margin-bottom:34px}
.tb{height:100%;background:linear-gradient(90deg,#E5383B,#F5B800);transform-origin:left}
.hlabel{font-size:44px;font-weight:900;color:#3E5674;margin-bottom:24px}
.hint{display:flex;gap:26px;align-items:center;background:#fff;border:4px solid #C9D7E6;border-radius:32px;padding:34px 40px;margin-bottom:24px}
.hint .n{flex:none;width:96px;height:96px;border-radius:50%;background:#F5B800;color:#1B2A41;font-size:52px;font-weight:900;display:flex;align-items:center;justify-content:center}
.hint .t{font-size:50px;font-weight:900;line-height:1.3;color:#1B2A41}
.cnt{position:relative;height:440px;width:100%;margin:40px 0}
.cnt span{position:absolute;left:0;right:0;top:0;text-align:center;font-size:380px;font-weight:900;color:#E5383B;line-height:440px}
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


def redacted(ep):
    n = max(3, len(ep["answer"]["ticker"]))
    return "".join('<span class="rd"></span>' for _ in range(n))


def scenes_quiz(ep):
    q = ep["q"]
    kw = ep["keyword"]
    out = []
    qt = ep.get("qtype", "dca")
    if qt == "coffee":
        out.append((Q_CSS + f'''<div class="main"><div class="warn" data-blink="0.1">⚠️ 황금알 퀴즈</div>
<div class="h1" data-in="0.3">매일 커피 한 잔 ☕</div>
<div class="qline" data-in="0.6">하루 <b>5,000원</b> × 30일 = 월 <b>15만원</b></div>
<div class="qrow" data-in="1.0">10년 동안 넣은 돈 <b>{won(q["invested"])}</b></div>
<div data-shake="2.5,0.7,14"><div class="qbig" style="margin-top:40px" data-in="1.4"><span data-count="1.4,1.2" data-from="{q["invested"]}" data-to="{q["value"]}" data-fmt="won">{won(q["invested"])}</span></div></div>
<div class="h1" style="margin-top:50px" data-in="3.0">이 ETF, <mark>맞힐 수 있어요?</mark></div></div>''', 4.8))
    elif qt == "trap":
        out.append((Q_CSS + f'''<div class="main"><div class="warn" data-blink="0.1">⚠️ 함정 퀴즈</div>
<div class="h1" data-in="0.3">매달 <mark>100만원</mark> 배당 받으려면?</div>
<div class="qrow" data-in="0.8">SCHD는 <b>{won(q["anchor_need"])}</b></div>
<div class="qrow" data-in="1.4">그런데 이 ETF는 단</div>
<div data-shake="2.9,0.7,16"><div class="qbig" style="margin-top:30px;color:#E5383B" data-in="1.8"><span data-count="1.8,1.1" data-from="{q["anchor_need"]}" data-to="{q["need"]}" data-fmt="won">{won(q["anchor_need"])}</span></div></div>
<div class="h1" style="margin-top:50px" data-in="3.2">어떻게 가능할까? <mark>함정</mark>은?</div></div>''', 5.0))
    # 1) 숫자부터: 넣은 돈이 빠르게 불어나며 흔들림 → 수익률 빨간 도장
    if qt == "dca":
      out.append((Q_CSS + f'''<div class="main"><div class="warn" data-blink="0.1">⚠️ 황금알 퀴즈</div>
<div class="h1" data-in="0.3">월 10만원씩 10년,</div>
<div class="qrow" data-in="0.6">넣은 돈 <b>{won(q["invested"])}이</b></div>
<div data-shake="2.0,0.7,14"><div class="qbig" style="margin-top:46px" data-in="0.9"><span data-count="0.9,1.2" data-from="{q["invested"]}" data-to="{q["value"]}" data-fmt="won">{won(q["invested"])}</span></div></div>
<div data-pop="2.3"><span class="qret">수익률 {q["ret"]:+,.0f}%</span></div>
<div class="h1" style="margin-top:56px" data-in="3.0">이 ETF, <mark>맞힐 수 있어요?</mark></div></div>''', 4.6))
    # 2) 가려진 정답 + 줄어드는 타이머 + 힌트
    hs = "".join(f'<div class="hint" data-pop="{0.9 + 1.2 * i:.2f}"><div class="n">{i + 1}</div><div class="t">{esc(h)}</div></div>'
                 for i, h in enumerate(q["hints"]))
    hd = 0.9 + 1.2 * len(q["hints"]) + 0.9
    out.append((Q_CSS + f'''<div class="main"><div class="ansbox" data-in="0.1"><span class="al">정답</span><div class="rds" data-shake="0.3,{hd:.2f},3">{redacted(ep)}</div></div>
<div class="timer" data-in="0.2"><div class="tb" data-bar="0.3,{hd - 0.3:.2f}"></div></div>
<div class="hlabel" data-in="0.5">힌트 {len(q["hints"])}개로 맞혀 보세요</div>{hs}</div>''', hd))
    # 3) 정답 공개 카운트다운 3·2·1 → 잠금
    out.append((Q_CSS + f'''<div class="main" style="text-align:center"><div class="h1" data-in="0.1">정답 공개까지</div>
<div class="cnt"><span data-win="0.4,1.2">3</span><span data-win="1.2,2.0">2</span><span data-win="2.0,2.8">1</span><span data-win="2.8,9">🔒</span></div>
<div class="h1" data-in="3.0">{"정답과 함정은" if ep.get("qtype") == "trap" else "정답은"} <mark>DM으로만</mark> 공개!</div></div>''', 4.0))
    # 4) 정답 받는 법
    out.append((Q_CSS + f'''<div class="main"><div class="lock" data-in="0.1">정답 받는 법 📩</div>
<div class="step" data-pop="0.4"><div class="n">1</div><div class="t">@golden_duck_lab<br>팔로우<small>정답 DM이 받은 편지함으로 바로 와요</small></div></div>
<div class="step" data-pop="1.0"><div class="n">2</div><div class="t">댓글에 '{esc(kw)}'<small>안 보이면 '메시지 요청함' 확인</small></div></div>
<div class="disc" data-in="1.5">{esc(ep["asof"])} 기준 · {"최근 1년 배당 그대로 가정 · 세금 15.4% 반영 · 배당은 확정 금액이 아님" if qt == "trap" else "배당 재투자 · 원달러 환율 반영"} · 과거 수익률은 미래 수익을 보장하지 않음 · 특정 종목 추천 아님</div></div>
<img class="duck" data-pop="1.8" src="{uri("duck.png")}">''', 4.6))
    return out


def cover_quiz(ep):
    q = ep["q"]
    qt = ep.get("qtype", "dca")
    if qt == "coffee":
        return Q_CSS + f'''<div class="main cov"><div class="warn">⚠️ 황금알 퀴즈</div>
<div class="h1">매일 커피 한 잔 ☕<br>10년 모았더니</div>
<div class="qbig" style="margin-top:24px">{won(q["value"])}</div>
<div class="qrow">넣은 돈 <b>{won(q["invested"])}</b></div>
<div class="ansbox" style="margin-top:40px"><span class="al">정답</span><div class="rds">{redacted(ep)}</div></div>
<div class="h1">이 ETF는 <mark>뭘까요?</mark></div></div>'''
    if qt == "trap":
        return Q_CSS + f'''<div class="main cov"><div class="warn">⚠️ 함정 퀴즈</div>
<div class="h1">월 <mark>100만원</mark> 배당,<br>단 이만큼으로?</div>
<div class="qbig" style="margin-top:24px;color:#E5383B">{won(q["need"])}</div>
<div class="qrow">SCHD는 <b>{won(q["anchor_need"])}</b></div>
<div class="ansbox" style="margin-top:40px"><span class="al">정답</span><div class="rds">{redacted(ep)}</div></div>
<div class="h1">함정은 <mark>뭘까요?</mark></div></div>'''
    return Q_CSS + f'''<div class="main cov"><div class="warn">⚠️ 황금알 퀴즈</div>
<div class="h1">월 10만원씩 10년,<br>{won(q["invested"])}이</div>
<div class="qbig" style="margin-top:24px">{won(q["value"])}</div>
<div><span class="qret">수익률 {q["ret"]:+,.0f}%</span></div>
<div class="ansbox" style="margin-top:44px"><span class="al">정답</span><div class="rds">{redacted(ep)}</div></div>
<div class="h1">이 ETF는 <mark>뭘까요?</mark></div></div>'''
