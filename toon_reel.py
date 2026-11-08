"""골든튠(인스타툰) 원고(toon/NN.json)와 만화 이미지로 릴스 영상(1080x1920)을 만든다.

- 이미지: out/<slug>/golden_duck_lab_<slug>_NN.jpg (1080x1350, 피드용 그대로 사용)
- 장면마다 크림색 세로 화면 가운데에 만화 한 장을 놓고, 장면 사이를 부드럽게 넘긴다.
- 배경음: 엉뚱하고 발랄한 마림바·통통 베이스·우드블록을 직접 합성 (외부 음원 없음 → 저작권 걱정 없음)
결과: out/<slug>/reel.mp4, out/<slug>/cover.jpg
사용법: python toon_reel.py toon/00.json
"""
import json, sys, pathlib, subprocess, tempfile, wave
import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).parent
W, H, FPS = 1080, 1920, 30
SEC, FADE = 4.0, 0.4
BG = (255, 246, 220)

try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG = "ffmpeg"


def playful_music(path, seconds, sr=48000):
    """엉뚱·발랄한 배경음: 통통 튀는 마림바 멜로디 + 쿵짝 베이스 + 우드블록 + '띠용' 효과 (BPM 128)."""
    n = int(seconds * sr)
    out = np.zeros(n)
    beat = 60.0 / 128
    eighth = beat / 2
    bar = beat * 4
    f = lambda m: 440.0 * 2 ** ((m - 69) / 12)

    def add(start, sig):
        s = int(start * sr)
        if s >= n:
            return
        e = min(n, s + len(sig))
        out[s:e] += sig[: e - s]

    def marimba(m, dur=0.32, vol=0.22):
        t = np.arange(int(dur * sr)) / sr
        fr = f(m)
        return vol * (np.sin(2 * np.pi * fr * t) * np.exp(-t * 9) + 0.35 * np.sin(2 * np.pi * 4 * fr * t) * np.exp(-t * 30))

    def pluck(m, dur=0.22, vol=0.28):
        t = np.arange(int(dur * sr)) / sr
        fr = f(m)
        return vol * (np.sin(2 * np.pi * fr * t) + 0.25 * np.sin(2 * np.pi * 2 * fr * t)) * np.exp(-t * 11)

    def stab(ms, dur=0.11, vol=0.06):
        t = np.arange(int(dur * sr)) / sr
        env = np.minimum(1, t / 0.005) * np.exp(-t * 18)
        return sum(vol * env * (np.sin(2 * np.pi * f(m) * t) + 0.3 * np.sin(2 * np.pi * 3 * f(m) * t)) for m in ms)

    def block(dur=0.05, vol=0.08):
        t = np.arange(int(dur * sr)) / sr
        return vol * np.sin(2 * np.pi * 1250 * t) * np.exp(-t * 70)

    def boing(dur=0.42, vol=0.16):
        t = np.arange(int(dur * sr)) / sr
        fr = 260 + 520 * (t / dur) ** 0.6 + 18 * np.sin(2 * np.pi * 16 * t)
        ph = 2 * np.pi * np.cumsum(fr) / sr
        return vol * np.sin(ph) * np.exp(-t * 4)

    chords = [[60, 64, 67], [65, 69, 72], [67, 71, 74], [60, 64, 67]]  # C F G C
    roots = [48, 53, 55, 48]
    mel = [
        [72, None, 76, 79, 77, 76, None, 72],
        [77, None, 81, 84, 83, 81, None, 77],
        [79, 78, 79, None, 83, None, 86, None],
        [84, None, 79, None, 76, None, None, None],
    ]
    nbars = int(np.ceil(seconds / bar))
    for b in range(nbars):
        k = b % 4
        t0 = b * bar
        for i in range(4):  # 쿵짝: 1·3박 베이스, 2·4박 화음
            if i % 2 == 0:
                add(t0 + i * beat, pluck(roots[k] + (7 if i == 2 else 0)))
            else:
                add(t0 + i * beat, stab(chords[k]))
        for j, m in enumerate(mel[k]):
            if m is not None:
                add(t0 + j * eighth, marimba(m))
            if j % 2 == 1:
                add(t0 + j * eighth, block())
        if k == 3:
            add(t0 + 5 * eighth, boing())
    out[: int(0.3 * sr)] *= np.linspace(0, 1, int(0.3 * sr))
    fade = int(1.2 * sr)
    out[-fade:] *= np.linspace(1, 0, fade)
    out = out / (np.max(np.abs(out)) + 1e-9) * 0.7
    st = np.stack([out, out], axis=1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((st * 32767).astype("<i2").tobytes())


def frame(img_path, dst):
    canvas = Image.new("RGB", (W, H), BG)
    im = Image.open(img_path).convert("RGB")
    if im.size != (1080, 1350):
        im = im.resize((1080, 1350))
    canvas.paste(im, (0, (H - 1350) // 2))
    canvas.save(dst, quality=95)


def build(path):
    ep = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    slug = ep["slug"]
    out_dir = ROOT / "out" / slug
    imgs = [out_dir / f"golden_duck_lab_{slug}_{i:02d}.jpg" for i in range(1, len(ep["slides"]) + 1)]
    n = len(imgs)
    total = n * SEC - (n - 1) * FADE
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        frames = []
        for i, p in enumerate(imgs):
            fp = td / f"f{i}.jpg"
            frame(p, fp)
            frames.append(fp)
        frame(imgs[0], out_dir / "cover.jpg")
        playful_music(td / "bgm.wav", total + 0.2)
        args = [FFMPEG, "-y", "-v", "error"]
        for fp in frames:
            args += ["-loop", "1", "-t", str(SEC), "-framerate", str(FPS), "-i", str(fp)]
        args += ["-i", str(td / "bgm.wav")]
        chain, last = [], "[0:v]"
        for i in range(1, n):
            lab = f"[v{i}]"
            chain.append(f"{last}[{i}:v]xfade=transition=slideleft:duration={FADE}:offset={i * (SEC - FADE):.2f}{lab}")
            last = lab
        chain.append(f"{last}format=yuv420p[vout]")
        args += ["-filter_complex", ";".join(chain), "-map", "[vout]", "-map", f"{n}:a",
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", str(FPS),
                 "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-shortest", "-movflags", "+faststart",
                 str(out_dir / "reel.mp4")]
        subprocess.run(args, check=True)
    print("ok", out_dir / "reel.mp4", f"{total:.1f}s")


if __name__ == "__main__":
    build(sys.argv[1])
