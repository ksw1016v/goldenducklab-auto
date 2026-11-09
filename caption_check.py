"""캡션 점검기 — 게시 전에 캡션이 STYLE.md 규칙에 맞는지 확인한다.

게시를 막지는 않는다. 문제를 찾으면 GitHub Actions 화면에 경고(노란 줄)로 남긴다.
(아이디어 출처: Jakeschincariol/instagram-agent-skill 의 caption.py·detect.py, MIT.
 골든덕랩 한국어 캡션 규칙에 맞게 새로 작성함)

사용법
  python3 caption_check.py episodes/18.json          한 편 점검
  python3 caption_check.py --all                     저장소의 모든 원고 점검
  python3 caption_check.py 원고.json --strict        오류가 있으면 실패(종료코드 1)
"""
import json, os, re, sys, pathlib

ROOT = pathlib.Path(__file__).parent
LIMIT = 2200            # 인스타 캡션 최대 글자 수
HOOK_MAX = 70           # '더 보기' 전에 보이는 첫 두 줄 권장 길이(한글 기준 대략값)
TAG_MIN, TAG_MAX = 5, 10

# 규제·신뢰: 쓰면 안 되는 표현 (STYLE.md '꼭 지킬 것')
BANNED = {
    "오픈채팅": "오픈채팅 유입 문구 금지", "오픈톡": "오픈채팅 유입 문구 금지",
    "카카오톡": "카카오톡 유입 문구 금지", "카톡": "카카오톡 유입 문구 금지",
    "무조건": "확정 표현 금지", "100% 수익": "수익 보장 표현 금지",
    "수익 보장": "수익 보장 표현 금지", "수익보장": "수익 보장 표현 금지",
    "확정 수익": "확정 표현 금지", "확정수익": "확정 표현 금지",
    "사세요": "매수 권유 금지", "매수하세요": "매수 권유 금지", "매도하세요": "매도 권유 금지",
    "강력 추천": "추천 표현 금지", "강력추천": "추천 표현 금지", "추천 종목": "종목 추천 금지",
    "받아가세요": "자료 배포 문구 금지",
}
# '추천 종목이 아닌' 같은 부정 문맥은 허용
NEGATED = re.compile(r"(추천\s*종목)(이|은)?\s*아닌|(특정\s*종목\s*추천)\s*(이|은)?\s*아닌")

# AI가 남기는 흔적 문자
FINGERPRINT = {
    "—": "긴 줄표(—)", "–": "중간 줄표(–)",
    "​": "보이지 않는 문자(ZWSP)", "‌": "보이지 않는 문자(ZWNJ)",
    "‍": "보이지 않는 문자(ZWJ, 이모지 결합이 아니면)", "﻿": "보이지 않는 문자(BOM)",
    " ": "줄바꿈 안 되는 공백",
}
# 한국어 AI 상투어 (경고만)
SLOP = ["결론적으로", "요약하자면", "다양한 측면", "중요한 역할을 합니다", "살펴보겠습니다",
        "알아보겠습니다", "함께 알아봐요", "꼭 기억하세요!", "핵심은 바로", "여정", "게임 체인저"]

TAG_RE = re.compile(r"#[0-9A-Za-z_가-힣]+")


def series_of(ep, path):
    slug = str(ep.get("slug", ""))
    p = str(path)
    if slug.startswith("etf-") or "etf/episodes" in p:
        return "etf"
    if slug.startswith("inc-") or "income_episodes" in p:
        return "income"
    if slug.startswith("brief-") or "econ/" in p:
        return "brief"
    if slug.startswith("toon-") or "toon/" in p:
        return "toon"
    return "basic"


def check(caption, series="basic"):
    """(수준, 항목, 설명) 목록을 돌려준다. 수준: ERROR / WARN"""
    out = []
    add = lambda lv, k, msg: out.append((lv, k, msg))
    text = caption or ""

    if not text.strip():
        return [("ERROR", "캡션", "캡션이 비어 있어요")]
    if len(text) > LIMIT:
        add("ERROR", "길이", f"{len(text)}자 — 인스타 한도 {LIMIT}자를 넘어요")

    # 금지 표현
    clean = NEGATED.sub("", text)
    for w, why in BANNED.items():
        if w in clean:
            add("ERROR", "금지 표현", f"'{w}' — {why}")

    # 첫 두 줄(더 보기 전에 보이는 부분)
    lines = [l for l in text.split("\n")]
    head = "\n".join(lines[:2]).strip()
    first = lines[0].strip()
    if not first:
        add("WARN", "첫 줄", "첫 줄이 비어 있어요. 후킹 문장으로 시작해 주세요")
    if first.startswith("#"):
        add("WARN", "첫 줄", "해시태그로 시작해요. 피드에서 제일 비싼 자리예요")
    if re.match(r"^(안녕하세요|오늘은|여러분 안녕)", first):
        add("WARN", "첫 줄", "인사로 시작해요. 질문이나 숫자로 바로 들어가 주세요")
    if len(head) > HOOK_MAX:
        add("WARN", "첫 두 줄", f"{len(head)}자 — '더 보기' 전에 잘릴 수 있어요(권장 {HOOK_MAX}자 이내)")
    if TAG_RE.search(head):
        add("WARN", "첫 두 줄", "해시태그가 '더 보기' 앞에 보여요")

    # 해시태그
    tags = TAG_RE.findall(text)
    if len(tags) > 30:
        add("ERROR", "해시태그", f"{len(tags)}개 — 인스타 한도 30개 초과")
    elif not (TAG_MIN <= len(tags) <= TAG_MAX) and series != "toon":
        add("WARN", "해시태그", f"{len(tags)}개 — 권장 {TAG_MIN}~{TAG_MAX}개")
    if tags and tags[-1] != "#골든덕랩":
        add("WARN", "해시태그", f"마지막 태그가 {tags[-1]} 예요. 마지막은 #골든덕랩")
    if not tags:
        add("WARN", "해시태그", "해시태그가 없어요")
    dup = sorted({t for t in tags if tags.count(t) > 1})
    if dup:
        add("WARN", "해시태그", "중복: " + " ".join(dup))

    # 행동 유도
    if "👇" not in text and "댓글" not in text:
        add("WARN", "댓글 유도", "댓글 유도 문장이 없어요")

    # 투자 정보 시리즈 면책 문구
    if series in ("etf", "income"):
        ok = ("과거 수익률" in text or "과거 성과" in text) if series == "etf" else \
             ("확정된 금액이 아니" in text or "과거 수익률" in text or "보장하지 않" in text)
        if not ok:
            need = "'과거 수익률은 미래 수익을 보장하지 않음'" if series == "etf" else "'배당은 확정된 금액이 아님'"
            add("ERROR", "면책 문구", f"{need} 문구가 없어요")
        if "추천" not in text:
            add("ERROR", "면책 문구", "'특정 종목 추천 아님' 문구가 없어요")

    # AI 흔적
    for ch, name in FINGERPRINT.items():
        n = text.count(ch)
        if ch == "‍":
            n -= len(re.findall(r"[\U0001F000-\U0001FAFF]‍[\U0001F000-\U0001FAFF]", text))
        if n > 0:
            add("WARN", "AI 흔적", f"{name} {n}개")
    slop = [s for s in SLOP if s in text]
    if slop:
        add("WARN", "AI 말투", "상투어: " + ", ".join(slop))
    return out


def check_file(path):
    ep = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    return check(ep.get("caption", ""), series_of(ep, path))


def report(path, results, gh=None):
    gh = os.environ.get("GITHUB_ACTIONS") == "true" if gh is None else gh
    rel = os.path.relpath(path, ROOT) if os.path.isabs(str(path)) else str(path)
    if not results:
        print(f"PASS  {rel}")
        return
    for lv, k, msg in results:
        if gh:
            kind = "error" if lv == "ERROR" else "warning"
            # 게시는 막지 않으므로 오류도 경고 줄로 표시하되 [오류] 표기
            print(f"::warning file={rel}::[캡션 {'오류' if kind == 'error' else '주의'}] {k}: {msg}")
        else:
            print(f"{lv:5} {rel}  {k}: {msg}")


def warn_only(path):
    """publish.py 에서 호출 — 어떤 경우에도 예외를 밖으로 던지지 않는다."""
    try:
        report(path, check_file(path))
    except Exception as e:  # 점검기 문제로 게시가 멈추면 안 됨
        print(f"::warning::캡션 점검을 건너뜀 ({e})")


def all_files():
    pats = ["episodes/*.json", "etf/episodes/*.json", "etf/income_episodes/*.json",
            "econ/episodes/*.json", "toon/*.json"]
    for p in pats:
        yield from sorted(ROOT.glob(p))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    strict = "--strict" in sys.argv
    files = list(all_files()) if "--all" in sys.argv else [pathlib.Path(a) for a in args]
    if not files:
        print(__doc__)
        sys.exit(0)
    errors = 0
    for f in files:
        r = check_file(f)
        errors += sum(1 for lv, _, _ in r if lv == "ERROR")
        report(f, r)
    sys.exit(1 if strict and errors else 0)
