"""카드뉴스 이미지(out/<slug>/golden_duck_lab_<slug>_NN.jpg)를 세로 릴스 영상으로 만든다.

2026-11-15: 캐러셀 도달이 5~19명에 그쳐서 기초편도 릴스로만 올리기로 했어요.
카드 한 장씩 천천히 확대되며 넘어가는 슬라이드쇼 + 잔잔한 배경음.
사용법: python card_reel.py episodes/13.json   -> out/13/reel.mp4, out/13/cover.jpg
"""
import json, sys, pathlib, subprocess, tempfile
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent
try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG = "ffmpeg"

W, H, FPS = 1080, 1920, 30
BG = (255, 248, 231)          # 크림색 (기초편 카드 배경과 같은 계열)
FIRST, EACH, LAST = 3.0, 3.6, 3.0   # 표지·본문·마지막 장 노출 시간(초)


def frame(card, scale):
    """크림 배경 가운데에 카드를 scale 배율로 얹은 1080x1920 이미지."""
    bg = Image.new("RGB", (W, H), BG)
    cw = int(W * scale)
    ch = int(card.height * cw / card.width)
    im = card.resize((cw, ch), Image.LANCZOS)
    bg.paste(im, ((W - cw) // 2, (H - ch) // 2))
    return bg


def build(path):
    ep = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    slug = ep.get("slug") or f"{ep['no']:02d}"
    out = ROOT / "out" / slug
    cards = sorted(out.glob(f"golden_duck_lab_{slug}_*.jpg"))
    if not cards:
        sys.exit(f"카드 이미지가 없어요: {out} (render.py 먼저 실행)")
    durs = [FIRST] + [EACH] * (len(cards) - 2) + [LAST] if len(cards) > 1 else [FIRST]
    total = sum(durs)
    from reel import music   # 다른 릴스와 같은 배경음
    with tempfile.TemporaryDirectory() as td:
        wav = pathlib.Path(td) / "bgm.wav"
        music(wav, total + 0.2)
        p = subprocess.Popen([FFMPEG, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                              "-r", str(FPS), "-i", "-", "-i", str(wav), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                              "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart",
                              str(out / "reel.mp4")], stdin=subprocess.PIPE)
        for i, (c, d) in enumerate(zip(cards, durs)):
            card = Image.open(c).convert("RGB")
            n = int(d * FPS)
            nxt = Image.open(cards[i + 1]).convert("RGB") if i + 1 < len(cards) else None
            for f in range(n):
                t = f / n
                im = frame(card, 0.96 + 0.03 * t)              # 천천히 살짝 확대
                if nxt is not None and f >= n - 6:              # 마지막 0.2초는 다음 장과 겹쳐 넘김
                    im = Image.blend(im, frame(nxt, 0.96), (f - (n - 6)) / 6)
                p.stdin.write(im.tobytes())
        p.stdin.close()
        if p.wait():
            sys.exit("ffmpeg 실패")
    frame(Image.open(cards[0]).convert("RGB"), 1.0).save(out / "cover.jpg", quality=92)
    print("reel", out / "reel.mp4", f"{total:.1f}s")
    return out / "reel.mp4"


if __name__ == "__main__":
    build(sys.argv[1])
