"""ETF 카드뉴스 원고(etf/episodes/NN.json)로 릴스 영상(1080x1920, 약 35초)을 만든다.

장면을 한 장씩 렌더링해서(글자·금액이 하나씩 쌓이는 연출) 페이드로 잇고,
직접 합성한 배경음을 깐다(외부 음원 없음 → 저작권 걱정 없음).
결과: out/<slug>/reel.mp4
사용법: python reel.py etf/episodes/02.json
"""
import json, sys, os, pathlib, subprocess, tempfile, wave
import numpy as np
from playwright.sync_api import sync_playwright
from render import CSS, THEMES, esc, uri

ROOT = pathlib.Path(__file__).parent
W, H, FPS = 1080, 1920, 30
FADE = 0.35

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
"""
ETF_REEL = """
.kick{color:#4A6A8F}
.drow.hi{border-color:#1E3A5F}
.mrow{border-color:#C9D7E6}
.mrow .ml{color:#4A6A8F}.mrow .mp{color:#3E5674}
.say{color:#2E6B3A}
"""


def page(ep, inner):
    theme = THEMES.get(ep.get("theme", ""), "")
    extra = ETF_REEL if ep.get("theme") == "etf" else ""
    tag = f"{ep['series']} #{ep['no']:02d}"
    return f"""<html><head><meta charset="utf-8"><style>{CSS}{theme}{REEL_CSS}{extra}</style></head><body>
<div class="frame"><div class="top"><span class="tag">{esc(tag)}</span><span class="page"></span></div>{inner}
<div class="foot"><span>@golden_duck_lab</span><span>저장하고 다시 보기</span></div></div></body></html>"""


def scenes(ep):
    s = ep["slides"]
    info = next(x for x in s if x["type"] == "etf_info")
    dcas = [x for x in s if x["type"] == "dca"]
    notes = next(x for x in s if x["type"] == "list" and "알아둘" in x["title"])
    end = s[-1]
    t = info["ticker"]
    label = t if not t.isdigit() else info["name"]
    big_size = "230px" if len(label) <= 5 else ("150px" if len(label) <= 8 else "104px")
    rows10 = [r for r in dcas[0]["rows"] if r[1] != "-"]
    longest = rows10[0][0] if rows10 else "5년"
    duck = f'<img class="duck" src="{uri("duck.png")}">'
    out = []

    head = f'<div class="kick">{esc(info["category"])}</div><div class="big" style="font-size:{big_size}">{esc(label)}</div>'
    out.append((f'<div class="main">{head}<div class="h1">월 10만원씩</div></div>{duck}', 1.6))
    out.append((f'<div class="main">{head}<div class="h1">월 10만원씩<br><mark>{esc(longest)}</mark> 모았다면?</div>'
                f'<div class="subt">{esc(info["rows"][0][1])}에<br>투자하는 ETF</div></div>{duck}', 2.6))

    kv = "".join(f'<div class="kv"><span>{esc(a)}</span><b>{esc(b)}</b></div>' for a, b in info["rows"])
    out.append((f'<div class="main"><div class="big" style="font-size:{min(int(big_size[:-2]), 150)}px">{esc(label)}</div>'
                f'<div class="ename">{esc(info["name"])}</div><div class="chip">{esc(info["category"])}</div>'
                f'<div class="lead" style="margin-top:40px;font-size:46px">{esc(info["desc"])}</div><div style="font-size:40px">{kv}</div></div>', 4.2))

    order = list(reversed(rows10))  # 짧은 기간부터 하나씩 쌓기 (5년 → 10년 → 20년)
    title = '<div class="h2"><mark>매달 10만원씩</mark><br>모았다면 지금은?</div>'
    note = f'<div class="disc">{esc(dcas[0].get("note", ""))}</div>'

    def drows(k, hi_last=False):
        h = ""
        for j, (y, p, v, r) in enumerate(order[:k]):
            hi = " hi" if hi_last and j == len(order) - 1 else ""
            h += (f'<div class="drow{hi}"><div class="dy">{esc(y)}</div><div class="dv"><div class="dpr">원금 {esc(p)}</div>'
                  f'<div class="dval">{esc(v)}</div></div><div class="dret">{esc(r)}</div></div>')
        return h

    out.append((f'<div class="main">{title}</div>', 1.2))
    for k in range(1, len(order) + 1):
        last = k == len(order)
        out.append((f'<div class="main">{title}{drows(k, last)}</div>', 2.6 if last else 1.6))
    eggs = '<div class="eggs">' + '<div class="egg"></div>' * 3 + '</div>'
    out.append((f'<div class="main">{title}{drows(len(order), True)}{eggs}{note}</div>', 2.2))

    def mrow(amt, d):
        row = next(r for r in d["rows"] if r[0] == longest)
        return (f'<div class="mrow"><div class="ml">월 {amt}만원 × {esc(longest)}</div><div class="mp">원금 {esc(row[1])}</div>'
                f'<div class="mv">{esc(row[2])}</div></div>'), row[3]
    m30, _ = mrow(30, dcas[1])
    m50, ret = mrow(50, dcas[2])
    t2 = '<div class="h2"><mark>금액을 늘리면?</mark></div>'
    out.append((f'<div class="main">{t2}{m30}</div>', 2.0))
    out.append((f'<div class="main">{t2}{m30}{m50}<div class="say">같은 {esc(ret)}라도 금액이 클수록 황금알이 커져요</div>{note}</div>', 3.2))

    items = "".join(f'<div class="item"><div class="num">{j+1}</div><div><div class="it">{esc(a)}</div><div class="id">{esc(b)}</div></div></div>'
                    for j, (a, b) in enumerate(notes["items"]))
    out.append((f'<div class="main"><div class="h2">{esc(notes["title"])}</div>{items}</div>', 4.2))

    out.append((f'<div class="main end2"><img src="{uri("logo.png")}"><div class="h2" style="margin-bottom:16px">{esc(end["title"])}</div>'
                f'<div class="lead" style="margin:0;font-size:40px">{esc(end["sub"])}</div><div style="margin-top:44px"><span class="cta">{esc(end["cta"])}</span></div>'
                f'<div class="next" style="font-size:36px">{esc(end.get("next", ""))}</div></div>', 3.6))
    return out


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
    sc = scenes(ep)
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        with sync_playwright() as p:
            exe = os.environ.get("CHROME_PATH")
            b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
            pg = b.new_page(viewport={"width": W, "height": H})
            for i, (inner, _) in enumerate(sc):
                pg.set_content(page(ep, inner), wait_until="load")
                pg.wait_for_timeout(120)
                over = pg.evaluate("(()=>{const m=document.querySelector('.frame');return m.scrollHeight>m.clientHeight+2})()")
                if over:
                    print(f"!! overflow reel scene {i+1}")
                pg.screenshot(path=str(td / f"s{i:02d}.png"))
            b.close()
        durs = [d for _, d in sc]
        total = sum(durs) - FADE * (len(durs) - 1)
        music(td / "bgm.wav", total + 0.1)
        args = [FFMPEG, "-y", "-v", "error"]
        for i, d in enumerate(durs):
            args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{d:.3f}", "-i", str(td / f"s{i:02d}.png")]
        args += ["-i", str(td / "bgm.wav")]
        fl, prev, off = [], "0:v", 0.0
        for i in range(1, len(durs)):
            off += durs[i - 1] - FADE
            lab = f"v{i}"
            fl.append(f"[{prev}][{i}:v]xfade=transition=fade:duration={FADE}:offset={off:.3f}[{lab}]")
            prev = lab
        fl.append(f"[{prev}]format=yuv420p[vout]")
        args += ["-filter_complex", ";".join(fl), "-map", "[vout]", "-map", f"{len(durs)}:a",
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", str(FPS), "-pix_fmt", "yuv420p",
                 "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-shortest", "-movflags", "+faststart",
                 str(out_dir / "reel.mp4")]
        subprocess.run(args, check=True)
    print("reel", out_dir / "reel.mp4", f"{total:.1f}s")
    return out_dir / "reel.mp4"


if __name__ == "__main__":
    for a in sys.argv[1:]:
        build(a)
