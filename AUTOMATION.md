# 인스타 자동 게시 시스템 — 전체 틀

> 콘텐츠·컨셉은 바뀌어도 그대로 쓸 수 있는 **뼈대**만 정리한 문서입니다.
> 현재 적용 사례: 골든덕랩(@golden_duck_lab) — 돈공부 카드뉴스·경제 브리핑·ETF·현금흐름·인스타툰.

---

## 1. 한 줄 구조

```
원고(JSON) ─▶ 렌더링(이미지·영상) ─▶ 저장소에 커밋 ─▶ 공개 URL(CDN) ─▶ 인스타 API 게시 ─▶ 기록(state.json)
      ▲                                                                                 │
      └──────────── 대기열 / 데이터 자동 생성  ◀──────── 성과 수집(insights) ◀──────────────┘
```

- **실행 엔진**: GitHub Actions (예약 cron + 수동 실행 버튼)
- **정시 보조 신호**: Claude 예약 작업이 목표 시각 직전에 `workflow_dispatch` 를 한 번 더 호출
- **이미지 호스팅**: 저장소 자체 + jsDelivr CDN (막히면 raw.githubusercontent.com)
- **비밀값**: GitHub Secrets `IG_TOKEN` 하나

---

## 2. 폴더 구성 (역할 기준)

| 역할 | 파일/폴더 | 컨셉이 바뀌면 |
|---|---|---|
| 원고 규칙 | `STYLE.md`, `CURRICULUM.md` | **새로 작성** (톤·금지어·슬라이드 형식) |
| 원고 대기열 | `episodes/NN.json`, `<시리즈>/...json`, `*_queue.txt` | **새로 채움** |
| 원고 자동 생성 | `etf/make_episode.py`, `econ/brief.py` 등 | 데이터형 시리즈일 때만 |
| 데이터 수집 | `econ/fetch.py`, `etf/backtest.py`, `etf/income.py` | 데이터형 시리즈일 때만 |
| 렌더링 | `render.py`(카드뉴스), `reel.py`·`reel_anim.py`(릴스), `toon_reel.py` | 디자인만 교체 |
| 디자인 자산 | `assets/`, `fonts/`, `highlights/` | **교체** (로고·캐릭터·폰트) |
| 게시 | `publish.py` | 거의 그대로 |
| 중복·시간 가드 | `guard.py` | 시리즈 이름·목표 시각만 수정 |
| 기록 | `state.json` (게시 목록·로그), `insights.json` (성과) | 그대로 |
| 산출물 | `out/<slug>/` (jpg·mp4) | 자동 생성 |
| 워크플로 | `.github/workflows/*.yml` | 시리즈 수만큼 복제 |

---

## 3. 워크플로 유형 (4가지 틀)

### A. 게시 워크플로 (시리즈 1개 = 파일 1개)
예: `daily.yml`, `brief-post.yml`, `etf-post.yml`, `income-post.yml`, `toon-post.yml`

공통 단계:
1. `git pull` → `guard.py <시리즈>` 로 **오늘 이미 올렸는지 / 아직 시간 전인지** 판단 → `skip`
2. 다음 편 고르기 (대기열 or 자동 생성) — 없으면 `::warning::` 남기고 종료
3. 한글 폰트 설치 + Playwright(Chromium) 준비
4. 렌더링 → `out/<slug>/` 커밋·푸시 → 커밋 `SHA` 확보
5. `IMAGE_BASE=https://cdn.jsdelivr.net/gh/<repo>@<SHA>` 로 공개 주소 지정, 20초 대기
6. `publish.py post|reel` 로 게시 → `state.json` 커밋·푸시
7. (선택) 릴스 추가 게시 — `continue-on-error` 로 실패해도 본편은 유지

공통 설정:
- `concurrency: instagram-post` → 모든 게시 워크플로가 **동시에 하나만** 실행
- `permissions: contents: write`
- cron은 **목표 시각 앞뒤로 5~7개** 흩어서 등록(정각 혼잡·지연 대비), 가드가 첫 실행만 통과시킴

### B. 데이터 워크플로
예: `econ-data.yml`, `etf-data.yml`, `income-data.yml`
- 매달 1일 또는 수동 → 데이터 받아 JSON/CSV 갱신 → 커밋

### C. 유지보수 워크플로
- `refresh-token.yml` : 매달 1일 인스타 장기 토큰 연장 (60일 만료 방지)
- `insights.yml` : 매일 자정쯤 성과(도달·저장·프로필 방문 등) 읽어서 `insights.json` 저장 (읽기 전용)

### D. 수동 보정 워크플로
- `etf-reel-repost.yml` : 입력값(티커 목록)을 받아 특정 편만 다시 렌더·재게시

---

## 4. 게시 시간표 (현재 값 — 바꿔도 되는 부분)

| 시리즈 | 목표(KST) | 가드 키 | 비고 |
|---|---|---|---|
| 경제 브리핑 | 07:00 화~토 | `brief` | 10:30 지나면 그날 건너뜀, 릴스가 본편 |
| 기초편 | 09:00 매일 | `basic` | Claude 예약 작업이 08:56에 실행 신호 |
| 현금흐름 | 12:10 매일 | `income` | |
| ETF | 21:00 매일 | `etf` | 하루 경계를 낮 12시로 봄(새벽 지연분 = 전날 몫) |
| 인스타툰 | 수동 | — | `toon_published` 로 중복 방지 |

가드 규칙 (`guard.py`):
- 시리즈당 **하루 1편** (릴스·재게시 기록은 계산 제외)
- 목표 시각 **15분 전**부터만 게시 허용
- 수동 실행(`workflow_dispatch`)은 시간 조건 무시, 중복 조건만 적용

---

## 5. 원고 형식 (틀만)

```json
{
  "series": "시리즈 이름",
  "no": 1,
  "slug": "고유 ID (중복 판정 기준)",
  "slides": [ { "type": "cover" }, { "type": "list" }, ..., { "type": "end" } ],
  "caption": "캡션 + 해시태그"
}
```
- 슬라이드 타입(`cover`/`list`/`check`/`end` …)은 `render.py` 템플릿과 1:1 대응
- 컨셉이 바뀌면 **타입별 HTML 템플릿 + STYLE.md 규칙**만 새로 정의

---

## 6. 새 컨셉/계정으로 옮길 때 체크리스트

1. [ ] 인스타 프로페셔널 계정 + Meta 앱 → 장기 토큰 발급 → Secrets `IG_TOKEN`
2. [ ] `publish.py` 의 `IG_USER_ID` 교체
3. [ ] `STYLE.md` 새로 작성 (계정 컨셉·톤·금지 표현·슬라이드 형식)
4. [ ] `assets/`·`fonts/` 교체, `render.py` 색·레이아웃 수정
5. [ ] `guard.py` 의 `TARGET` 에 시리즈별 목표 시각 등록, slug 접두사 → 시리즈 매핑 수정
6. [ ] 시리즈마다 게시 워크플로 복제 (cron 여러 개 + `concurrency: instagram-post`)
7. [ ] 원고 3~5편 미리 채워 두기 (대기열 비면 경고만 남고 게시 안 됨)
8. [ ] `DRY_RUN=1` 로 한 번 확인 → 수동 실행으로 첫 게시
9. [ ] `refresh-token`·`insights` 워크플로 켜기
10. [ ] (선택) Claude 예약 작업으로 정시 실행 신호 등록:
    `gh api -X POST repos/<owner>/<repo>/actions/workflows/<file>.yml/dispatches -f ref=main`

---

## 7. 자주 생기는 문제

| 증상 | 원인 | 대응 |
|---|---|---|
| 예약 시간에 안 올라감 | GitHub cron 지연·누락 | cron 여러 개 + Claude 예약 신호 (이미 적용) |
| 같은 편 두 번 게시 | 실행 겹침 | `concurrency` + `guard.py` + `state.json` 확인 |
| 이미지 URL 오류 | CDN 캐시 지연 | 커밋 SHA 고정 주소 + 20초 대기, raw 주소 대체 |
| 토큰 만료 | 60일 경과 | `refresh-token` 매달 실행 |
| 대기열 비어 있음 | 원고 소진 | Actions 경고 확인 → 원고 추가 |
| 릴스만 실패 | 영상 처리 지연 | 본편은 유지, `*-reel-repost` 로 재게시 |
