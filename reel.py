"""ETF 카드뉴스 원고(etf/episodes/NN.json)로 릴스 영상(1080x1920, 약 35초)을 만든다.

장면마다 숫자 카운트업·순서대로 나타나기·황금알 떨어지기 같은 움직임을 1초 30장으로 찍어 잇고,
직접 합성한 배경음을 깐다(외부 음원 없음 → 저작권 걱정 없음).
결과: out/<slug>/reel.mp4
사용법: python reel.py etf/episodes/02.json
"""
import json, sys, os, pathlib, subprocess, tempfile, wave
import numpy as np
from playwright.sync_api import sync_playwright
from render import CSS, THEMES, esc, uri
from reel_anim import ANIM_JS, scenes, cover, scenes_income, cover_income
from econ.brief import scenes_brief, cover_brief, BRIEF_REEL, kday
from etf.special_reel import scenes_special, cover_special
from quiz.quiz_reel import scenes_quiz, cover_quiz

ROOT = pathlib.Path(__file__).parent
W, H, FPS = 1080, 1920, 30

try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG = "ffmpeg"

REEL_CSS = """
body{width:1080px;height:1920px}
.frame{inset:40px;padding:90px 76px 70px}
.main{justify-content:flex-start;padding-top:70px}
.big{font-size:230px;font-weight:900;letter-spacing:-6px;line-height:1}
.kick{font-size:44px;font-weight:700;color:#C98A3D;margin-bottom:10px}
.h1{font-size:104px;font-weight:900;line-height:1.25;letter-spacing:-2px;margin-top:30px}
.h2{font-size:96px;font-weight:900;line-height:1.25;letter-spacing:-2px;margin-bottom:64px}
.subt{font-size:44px;line-height:1.5;margin-top:40px;font-weight:500}
.duck{position:absolute;right:70px;bottom:190px;width:330px}
.drow{padding:46px 40px;margin-bottom:34px;gap:26px}
.dy{width:150px;height:150px;font-size:46px}
.dval{font-size:62px;white-space:nowrap;letter-spacing:-1px}.dpr{font-size:34px}.dret{font-size:40px;white-space:nowrap}
.drow.hi{border-width:5px;border-color:#F5B800}
.mrow{background:#fff;border:4px solid #F5DFA8;border-radius:30px;padding:48px 48px;margin-bottom:36px}
.mrow .ml{font-size:46px;font-weight:700;color:#C98A3D}
.mrow .mp{font-size:36px;color:#7a4a28;margin-top:8px}
.mrow .mv{font-size:96px;font-weight:900;letter-spacing:-2px;margin-top:8px}
.eggs{display:flex;gap:26px;margin-top:40px}
.egg{width:88px;height:112px;border-radius:50% 50% 46% 46%/58% 58% 42% 42%;background:radial-gradient(circle at 35% 30%,#FFF3B0,#F5B800 55%,#C98A3D)}
.say{font-size:44px;font-weight:700;color:#4E7D22;margin-top:24px;line-height:1.4}
.item{padding:44px 44px;margin-bottom:32px}.item .num{width:80px;height:80px;font-size:42px}.item .it{font-size:50px}.item .id{font-size:38px;margin-top:12px}
.disc{font-size:28px;margin-top:30px}
.end2{align-items:center;text-align:center;justify-content:center;padding-top:0}
.end2 img{width:520px;margin-bottom:40px}
.cta{font-size:46px}
span[data-in]{display:inline-block}
.cov{justify-content:center;padding-top:0;padding-bottom:260px}
.cov .h1{margin-top:36px}
.covnum{display:flex;flex-wrap:wrap;align-items:baseline;gap:18px;margin-top:56px;background:#fff;border:4px solid #F5DFA8;border-radius:30px;padding:34px 40px}
.covnum .cp{font-size:40px;color:#7a4a28;font-weight:500}.covnum .ca{font-size:44px;color:#C98A3D;font-weight:900}
.covnum .cv{flex-basis:100%;font-size:80px;font-weight:900;letter-spacing:-2px}
.covduck{bottom:150px}
.duck,.end2 img,.egg{transform-origin:center}
"""
ETF_REEL = """
.kick{color:#4A6A8F}
.drow.hi{border-color:#1E3A5F}
.mrow{border-color:#C9D7E6}
.mrow .ml{color:#4A6A8F}.mrow .mp{color:#3E5674}
.say{color:#2E6B3A}
.covnum{border-color:#C9D7E6}.covnum .cp{color:#3E5674}.covnum .ca{color:#4A6A8F}
"""

INCOME_REEL = """
.kick{color:#3F8A6E}
.drow.hi,.mrow.hi{border-color:#1F6B52;border-width:5px}
.mrow{border-color:#CDE7DC}
.mrow .ml{color:#3F8A6E}.mrow .mp{color:#35594C}
.say{color:#1F6B52}
.covnum{border-color:#CDE7DC}.covnum .cp{color:#35594C}.covnum .ca{color:#3F8A6E}
.hgrid{gap:20px}.hrow{padding:24px 28px 20px;border-width:4px}.hm{width:60px;height:60px;font-size:38px;right:24px;top:24px}
.hn{font-size:38px}.hv{font-size:56px;margin-top:4px}.hr{font-size:28px;margin-top:4px}
.badge{font-size:44px;padding:18px 40px}
.rcal{gap:26px;margin-bottom:46px}.mcell{position:relative}.rcal .mo{height:230px;font-size:60px}.rcal .mo small{font-size:34px}
.mo.lit{position:absolute;inset:0}
"""


def page(ep, inner, dur):
    theme = THEMES.get(ep.get("theme", ""), "")
    extra = {"etf": ETF_REEL, "income": INCOME_REEL, "brief": BRIEF_REEL}.get(ep.get("theme"), "")
    tag = (f"{ep['series']} · {kday(ep['date_us'])}" if ep.get("kind") == "brief"
           else f"{ep['series']} · 특별편" if ep.get("special_id") else f"{ep['series']} #{ep['no']:02d}")
    return f"""<html><head><meta charset="utf-8"><style>{CSS}{theme}{REEL_CSS}{extra}</style>{ANIM_JS}</head><body data-dur="{dur}">
<div class="frame"><div class="top"><span class="tag">{esc(tag)}</span><span class="page"></span></div>{inner}
<div class="foot"><span>@golden_duck_lab</span><span>저장하고 다시 보기</span></div></div></body></html>"""


def music(path, seconds, sr=48000):
    """잔잔한 로파이 느낌 배경음 합성: 코드 패드 + 베이스 + 가벼운 킥·하이햇 (BPM 84)."""
    n = int(seconds * sr)
    t = np.arange(n) / sr
    bpm = 84.0
    beat = 60.0 / bpm
    bar = beat * 4
    f = lambda m: 440.0 * 2 ** ((m - 69) / 12)
    prog = [[60, 64, 67, 71], [57, 60, 64, 67], [53, 57, 60, 64], [55, 59, 62, 65]]  # Cmaj7 Am7 Fmaj7 G7
    out = np.zeros(n)
    rng = np.random.default_rng(7)
    nb = int(np.ceil(seconds / bar))
    for b in range(nb):
        ch = prog[b % 4]
        s0, s1 = int(b * bar * sr), min(n, int((b + 1) * bar * sr))
        tt = t[s0:s1] - b * bar
        env = np.minimum(1, tt / 0.4) * np.minimum(1, (bar - tt) / 0.3)
        for m in ch:
            fr = f(m)
            out[s0:s1] += 0.05 * env * (np.sin(2 * np.pi * fr * tt) + 0.3 * np.sin(2 * np.pi * 2 * fr * tt + 0.5))
        bf = f(ch[0] - 24)
        out[s0:s1] += 0.10 * env * np.sin(2 * np.pi * bf * tt)
        for k in range(4):  # 피아노풍 아르페지오
            a0 = s0 + int((k * beat + beat / 2) * sr)
            if a0 >= n:
                break
            ln = min(int(0.9 * sr), n - a0)
            ta = np.arange(ln) / sr
            fr = f(ch[(k * 2) % 4] + 12)
            out[a0:a0 + ln] += 0.06 * np.exp(-ta * 3.5) * np.sin(2 * np.pi * fr * ta)
    kick_len = int(0.25 * sr)
    tk = np.arange(kick_len) / sr
    kick = np.sin(2 * np.pi * (50 + 70 * np.exp(-tk * 25)) * tk) * np.exp(-tk * 12) * 0.35
    hat_len = int(0.05 * sr)
    hat = rng.standard_normal(hat_len) * np.exp(-np.arange(hat_len) / sr * 80) * 0.05
    nbeats = int(seconds / beat) + 1
    for i in range(nbeats):
        p = int(i * beat * sr)
        if i % 2 == 0 and p + kick_len < n:
            out[p:p + kick_len] += kick
        q = int((i + 0.5) * beat * sr)
        if q + hat_len < n:
            out[q:q + hat_len] += hat
    fade = int(1.5 * sr)
    out[:int(0.5 * sr)] *= np.linspace(0, 1, int(0.5 * sr))
    out[-fade:] *= np.linspace(1, 0, fade)
    out = out / (np.max(np.abs(out)) + 1e-9) * 0.6
    st = np.stack([out, out], axis=1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((st * 32767).astype("<i2").tobytes())


def build(path):
    ep = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    slug = ep.get("slug") or f"{ep['no']:02d}"
    out_dir = ROOT / "out" / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    kind = ep.get("kind")
    income = kind == "income"
    sc = {"income": scenes_income, "brief": scenes_brief, "special_calendar": scenes_special, "quiz": scenes_quiz}.get(kind, scenes)(ep)
    cov = {"income": cover_income, "brief": cover_brief, "special_calendar": cover_special, "quiz": cover_quiz}.get(kind, cover)
    total = sum(d for _, d in sc)
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        music(td / "bgm.wav", total + 0.2)
        enc = subprocess.Popen([FFMPEG, "-y", "-v", "error", "-f", "image2pipe", "-c:v", "mjpeg", "-framerate", str(FPS), "-i", "-",
                                "-i", str(td / "bgm.wav"), "-map", "0:v", "-map", "1:a",
                                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS),
                                "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-shortest", "-movflags", "+faststart",
                                str(out_dir / "reel.mp4")], stdin=subprocess.PIPE)
        frames = 0
        with sync_playwright() as p:
            exe = os.environ.get("CHROME_PATH")
            b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
            pg = b.new_page(viewport={"width": W, "height": H})
            pg.set_content(page(ep, cov(ep), 999), wait_until="load")
            pg.evaluate("document.fonts.ready")
            pg.screenshot(path=str(out_dir / "cover.jpg"), type="jpeg", quality=92)
            for i, (inner, dur) in enumerate(sc):
                pg.set_content(page(ep, inner, dur), wait_until="load")
                pg.evaluate("document.fonts.ready")
                pg.evaluate(f"setT({dur - 0.31})")
                if pg.evaluate("(()=>{const m=document.querySelector('.frame');return m.scrollHeight>m.clientHeight+2})()"):
                    print(f"!! overflow reel scene {i + 1}")
                for k in range(int(round(dur * FPS))):
                    pg.evaluate(f"setT({k / FPS:.4f})")
                    enc.stdin.write(pg.screenshot(type="jpeg", quality=90))
                    frames += 1
            b.close()
        enc.stdin.close()
        if enc.wait() != 0:
            raise SystemExit("영상 인코딩 실패")
    print("reel", out_dir / "reel.mp4", f"{total:.1f}s", frames, "frames")
    return out_dir / "reel.mp4"


if __name__ == "__main__":
    for a in sys.argv[1:]:
        build(a)
