"""월별 등락 바둑판 데이터 → grid/data.json (GitHub Actions에서 실행: Yahoo 접속 필요)
지수 종가 기준(배당 제외). 20년 = 2006~2025 완결 연도 240개월 + 올해 지난 달들.
"""
import json, pathlib
import yfinance as yf

ROOT = pathlib.Path(__file__).resolve().parent
IDX = {"SPX": ("^GSPC", "미국 S&P500"), "NDX": ("^IXIC", "미국 나스닥"), "KOSPI": ("^KS11", "코스피")}
out = {}
for key, (tk, name) in IDX.items():
    h = yf.Ticker(tk).history(start="2005-11-01", auto_adjust=False)["Close"].dropna()
    m = h.resample("ME").last()
    r = m.pct_change().dropna()
    last_full = h.index[-1].to_period("M") - (0 if h.index[-1].is_month_end else 1)
    rows = {}
    for d, v in r.items():
        p = d.to_period("M")
        if p.year < 2006 or p > last_full:
            continue
        rows.setdefault(str(p.year), [None] * 12)[p.month - 1] = round(float(v) * 100, 2)
    out[key] = {"ticker": tk, "name": name, "rows": rows, "last_month": str(last_full),
                "close_2005": round(float(m[m.index.year == 2005].iloc[-1]), 2), "close_last": round(float(h.iloc[-1]), 2),
                "last_date": h.index[-1].strftime("%Y-%m-%d")}
    print(key, len(rows), out[key]["last_month"])
(ROOT / "data.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
