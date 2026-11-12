"""퀴즈용 데이터 (GitHub Actions에서 실행) → quiz/quiz_data.json
- trap: 초고배당 ETF의 최근 1년 배당률, 월 100만원(세후) 받는 데 필요한 원금, 상장 후 주가·총수익 변화
"""
import json, datetime, pathlib
import pandas as pd
import yfinance as yf

ROOT = pathlib.Path(__file__).parent
TRAP = ["MSTY", "CONY", "NVDY", "TSLY", "ULTY", "YMAX", "QYLD", "XYLD", "JEPQ", "JEPI", "SCHD", "VYM"]
NET_MONTH = 1_000_000
PRE_YEAR = NET_MONTH * 12 / (1 - 0.154)


def main():
    fx = float(yf.Ticker("KRW=X").history(period="5d")["Close"].dropna().iloc[-1])
    out = {"generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), "fx": round(fx, 2), "trap": []}
    for t in TRAP:
        try:
            tk = yf.Ticker(t)
            h = tk.history(period="max", auto_adjust=False)
            h.index = pd.to_datetime(h.index).tz_localize(None)
            c = h["Close"].dropna()
            adj = tk.history(period="max", auto_adjust=True)["Close"].dropna()
            div = h["Dividends"][h["Dividends"] > 0]
            last = c.index[-1]
            one = div[div.index > last - pd.Timedelta(days=365)]
            ttm = float(one.sum()); price = float(c.iloc[-1])
            y = ttm / price
            info = {}
            try:
                info = tk.get_info() or {}
            except Exception:
                pass
            gaps = one.index.to_series().diff().dt.days.dropna()
            freq = "매주" if len(gaps) and gaps.median() <= 9 else ("매달" if len(gaps) and gaps.median() <= 45 else "분기")
            rec = {"ticker": t, "name": info.get("longName") or info.get("shortName") or t,
                   "first_date": c.index[0].strftime("%Y-%m-%d"), "last_date": last.strftime("%Y-%m-%d"),
                   "years": round((last - c.index[0]).days / 365.25, 1), "price": round(price, 2), "ttm_div": round(ttm, 4),
                   "yield_pct": round(y * 100, 2), "freq": freq, "pay_count": int(len(one)),
                   "price_chg_pct": round((price / float(c.iloc[0]) - 1) * 100, 1),
                   "total_ret_pct": round((float(adj.iloc[-1]) / float(adj.iloc[0]) - 1) * 100, 1),
                   "price_chg_1y_pct": round((price / float(c[c.index <= last - pd.Timedelta(days=365)].iloc[-1]) - 1) * 100, 1) if (last - c.index[0]).days > 370 else None,
                   "need_krw": round(PRE_YEAR / y) if y > 0 else None}
            out["trap"].append(rec)
            print(rec)
        except Exception as ex:
            print("ERR", t, ex)
    (ROOT / "quiz_data.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
