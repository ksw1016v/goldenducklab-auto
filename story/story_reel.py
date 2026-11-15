"""골든에그의 월급일기 (공감 → 선배 조언 → 실제 데이터 희망) 릴스 장면.

- 골든에그: 33살 직장인(캐릭터), 골든덕: 조언하는 선배
- 숫자 중 '실제 과거 데이터'는 etf/results.json 계산값만 쓴다. 생활비 숫자는 예시라고 밝힌다.
"""
import base64, json, pathlib
from render import esc

ROOT = pathlib.Path(__file__).resolve().parent.parent


def ch(name):
    return "data:image/png;base64," + base64.b64encode((ROOT / "assets/chars" / f"{name}.png").read_bytes()).decode()


def won(v):
    v = int(v)
    if v >= 100_000_000:
        e, m = divmod(v, 100_000_000); m //= 10_000
        return f"{e}억 {m:,}만원" if m else f"{e}억원"
    return f"{v // 10_000:,}만원"


S_CSS = """<style>
.px{image-rendering:pixelated;position:absolute}
.sb{background:#fff;border:5px solid #5C2E0E;border-radius:40px;padding:36px 44px;font-size:62px;font-weight:900;line-height:1.3;color:#3B2A14;position:relative}
.sb.dk{background:#3B2A14;color:#FFE08A;border-color:#3B2A14}
.pay{font-size:70px;font-weight:900;color:#3E5674}
.bal{font-size:150px;font-weight:900;letter-spacing:-4px;color:#1B2A41;line-height:1.05}
.bal.red{color:#E5383B}
.spend{display:flex;justify-content:space-between;background:#fff;border:4px solid #F5DFA8;border-radius:24px;padding:22px 34px;margin-bottom:16px;font-size:50px;font-weight:700;color:#5C2E0E}
.spend b{color:#E5383B;font-weight:900}
.rule{display:flex;align-items:center;gap:30px;border-radius:34px;padding:38px 40px;margin-bottom:30px;font-size:58px;font-weight:900;line-height:1.3}
.rule.no{background:#F3E3E3;color:#8A3A3A}.rule.ok{background:#1E3A5F;color:#fff}
.rule .ic{flex:none;font-size:80px}
.vrow{display:flex;align-items:baseline;gap:20px;font-size:54px;font-weight:700;color:#3E5674;margin-top:16px}
.vrow b{font-size:66px;color:#1B2A41}
.ret{display:inline-block;margin-top:24px;background:#2E7D4F;color:#fff;border-radius:999px;padding:14px 40px;font-size:56px;font-weight:900}
.q{font-size:96px;font-weight:900;line-height:1.25;letter-spacing:-2px;color:#1B2A41}
.ep{display:inline-block;align-self:flex-start;background:#F5B800;color:#3B2A14;font-size:40px;font-weight:900;padding:10px 28px;border-radius:999px;margin-bottom:24px}
</style>"""


def scenes_story(ep):
    egg, duck, wow = ch("egg"), ch("duck"), ch("duck_wow")
    d = ep["data"]
    sp = ep["spend"]
    start, left = ep["salary"], ep["salary"] - sum(v for _, v in sp)
    rows = "".join(f'<div class="spend" data-drop="{1.0 + 0.55 * i:.2f}"><span>{esc(k)}</span><b>-{v // 10_000:,}만</b></div>' for i, (k, v) in enumerate(sp))
    t_end = 1.0 + 0.55 * len(sp)
    return [
        # 1) 공감 훅: 월급날
        (S_CSS + f'''<div class="main"><div class="ep" data-in="0.1">{esc(ep["series_ep"])}</div>
<div class="pay" data-in="0.3">월급날 오전 9시 💸</div>
<div class="bal" style="margin-top:20px;font-size:128px" data-pop="0.4">+{start:,}원</div>
<div class="sb" style="margin-top:60px;width:640px" data-pop="1.0">이번 달은<br>진짜 모은다!!</div></div>
<img class="px" src="{egg}" style="right:110px;bottom:330px;width:330px" data-pop="0.7">''', 2.7),
        # 2) 3일 뒤 통장
        (S_CSS + f'''<div class="main"><div class="pay" data-in="0.1">그리고 <b style="color:#E5383B">3일 뒤</b>…</div>
<div data-shake="{t_end:.2f},0.8,14"><div class="bal" style="margin:16px 0 30px"><span data-count="0.9,{t_end - 0.7:.2f}" data-from="{start}" data-to="{left}" data-fmt="num" data-suf="원">{start:,}원</span></div></div>
{rows}</div>
<img class="px" src="{egg}" style="right:90px;bottom:170px;width:220px" data-shake="{t_end:.2f},0.8,10">''', t_end + 1.4),
        # 3) 나만 이래?
        (S_CSS + f'''<div class="main"><div class="sb" data-pop="0.2" style="width:780px">선배…<br>나 진짜 돈 모을 수<br>있긴 한 걸까…?</div>
<div class="sb dk" data-pop="1.6" style="margin-top:300px;margin-left:200px">에그야,<br>순서가 틀렸덕.</div></div>
<img class="px" src="{egg}" style="right:90px;top:600px;width:200px" data-in="0.1">
<img class="px" src="{wow}" style="left:90px;bottom:200px;width:330px" data-pop="1.3">''', 4.2),
        # 4) 선배의 규칙
        (S_CSS + f'''<div class="main"><div class="h1" data-in="0.1" style="margin-top:0">덕 선배의 규칙</div>
<div style="margin-top:50px"><div class="rule no" data-pop="0.6"><span class="ic">❌</span><span>쓰고 <u>남는 돈</u>을 모은다</span></div>
<div class="rule ok" data-pop="1.4"><span class="ic">⭕</span><span>월급날, <u>10만원 먼저</u> 떼고 쓴다</span></div></div>
<div class="subt" data-in="2.2">남는 돈은 매달 0원이 되지만,<br>먼저 뗀 돈은 매달 쌓이덕.</div></div>
<img class="px" src="{duck}" style="right:90px;bottom:180px;width:300px" data-pop="0.3">''', 4.8),
        # 5) 희망: 실제 데이터
        (S_CSS + f'''<div class="main"><div class="pay" data-in="0.1" style="font-size:56px;line-height:1.4">10년 전부터 월급날마다<br><b style="color:#1B2A41">10만원씩 {esc(d["label"])}</b>에 먼저 넣었다면?</div>
<div class="vrow" data-in="0.9">넣은 돈 <b>{won(d["invested"])}</b></div>
<div data-shake="3.0,0.6,10"><div class="bal" style="margin-top:30px;color:#2E7D4F" data-in="1.3"><span data-count="1.3,1.6" data-from="{d["invested"]}" data-to="{d["value"]}" data-fmt="won">{won(d["invested"])}</span></div></div>
<div data-pop="3.0"><span class="ret">{d["ret"]:+.0f}%</span></div>
<div class="disc" data-in="3.4">{esc(d["note"])}</div></div>
<img class="px" src="{egg}" style="right:100px;bottom:200px;width:230px" data-pop="3.2">''', 5.6),
        # 6) 질문 CTA (참여 문턱 최소)
        (S_CSS + f'''<div class="main"><div class="q" data-in="0.1">여러분 월급은<br><mark>며칠</mark> 버텨요? 🫠</div>
<div class="subt" data-in="0.8" style="font-size:52px;font-weight:700">댓글로 알려 주세요.<br>제일 많은 답으로 다음 화 그려요!</div>
<div class="sb" data-pop="1.5" style="margin-top:60px;width:560px;font-size:52px">다음 화:<br>에그, 첫 ETF 사다</div>
<div class="disc" data-in="2.0" style="margin-top:auto">에그·덕은 캐릭터예요 · 생활비는 예시 · 수익률은 실제 과거 데이터({esc(d["asof"])} 기준, 배당 재투자·환율 반영, 세금·수수료 미반영) · 과거 수익률은 미래를 보장하지 않음 · 특정 종목 추천 아님</div></div>
<img class="px" src="{egg}" style="right:110px;bottom:420px;width:220px" data-pop="1.2">''', 4.6),
    ]


def cover_story(ep):
    egg = ch("egg")
    left = ep["salary"] - sum(v for _, v in ep["spend"])
    return S_CSS + f'''<div class="main cov"><div class="ep">{esc(ep["series_ep"])}</div>
<div class="h1" style="margin-top:10px">월급 {ep["salary"] // 10_000:,}만원,<br>3일 뒤 남은 돈</div>
<div class="bal red" style="margin-top:30px">{left:,}원</div>
<div class="h1" style="font-size:80px">나만 이래…? 🫠</div></div>
<img class="px" src="{egg}" style="right:110px;bottom:260px;width:300px">'''
