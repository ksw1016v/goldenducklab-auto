# 골든덕랩 원고 스킬 (한국어판)

원고·캡션·댓글·DM을 쓸 때 쓰는 클로드 스킬 5개입니다. **모두 글만 쓰고, 게시·발송은 하지 않습니다.**
모든 스킬은 저장소 루트의 `STYLE.md`(톤·금지 표현)를 먼저 따릅니다.

| 명령 | 하는 일 |
|---|---|
| `/gd-hook` | 표지 첫 줄·릴스 첫 3초 문구 후보 3개를 공식별로 쓰고 점수 매기기 |
| `/gd-caption` | STYLE.md 형식대로 캡션 쓰기 → `caption_check.py` 로 점검 |
| `/gd-human` | AI 티 나는 말투·문자 지우기 |
| `/gd-reply` | 내 게시물 댓글을 분류하고 답글 초안 쓰기 |
| `/gd-dm` | 댓글 키워드 DM, 첫 메시지, 후속 메시지 2개 쓰기 |

자동 점검: `publish.py` 가 게시 직전에 `caption_check.py` 를 돌려 문제를 Actions 경고로 남깁니다(게시는 막지 않음).
직접 점검: `python3 caption_check.py --all`

---
아이디어 출처: [Jakeschincariol/instagram-agent-skill](https://github.com/Jakeschincariol/instagram-agent-skill)
(MIT License, Copyright (c) Jake Schincariol). 골든덕랩 한국어 금융 계정에 맞게 새로 작성했습니다.
