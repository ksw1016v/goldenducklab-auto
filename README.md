# 골든덕랩 카드뉴스 자동 게시

매일 09:00(KST, 기초편 · 07:00 화~토 경제 브리핑 · 12:10 현금흐름 · 21:00 ETF) GitHub Actions가 `episodes/` 대기열에서 다음 편을 골라
카드뉴스 8장을 렌더링하고 인스타그램(@golden_duck_lab)에 캐러셀로 게시합니다.

- `episodes/NN.json` : 편별 원고(슬라이드 + 캡션). 새 편은 여기에 추가
- `render.py` : 원고 → 1080×1350 JPEG
- `publish.py` : 인스타그램 API 게시, 게시 기록은 `state.json`
- Secrets `IG_TOKEN` : 인스타그램 장기 액세스 토큰 (매달 자동 연장)
- 수동 실행: Actions → daily-post → Run workflow
