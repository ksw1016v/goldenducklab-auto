"""배당(현금흐름) 데이터 계산 (GitHub Actions에서 실행)

대상: etf/income_queue.txt 의 티커
- 최근 1년 배당 합계, 배당수익률(= 최근 1년 배당 / 현재가), 1년간 지급 횟수 → 지급 주기
- 5년 전 같은 기간 1년 배당 합계와 비교한 배당 성장률
- 월 50만원씩 최대 10년(상장이 짧으면 상장 이후) 적립했다면 지금 금액(분배금 재투자, 원화·환율 반영)
  → 그 금액이 지금 배당수익률로 매달 만들어 주는 현금흐름
- 월 50·100·300만원 현금흐름에 필요한 원금(세전, 현재 배당수익률 그대로 유지된다고 가정)
결과: etf/income.json
"""
import csv, json, time, datetime, pathlib
import pandas as pd
import yfinance as yf

ROOT = pathlib.Path(__file__).parent
AMT = 500_000
MAX_MONTHS = 120


def naive(idx):
    return pd.to_datetime(idx).tz_localize(None)


def main():
    meta = {r["ticker"]: r for r in csv.DictReader(open(ROOT / "etf_list.csv", encoding="utf-8"))}
    queue = [l.split("#")[0].strip() for l in open(ROOT / "income_queue.txt", encoding="utf-8")]
    queue = [q for q in queue if q]
    fx = yf.Ticker("KRW=X").history(period="max", interval="1d", auto_adjust=True)["Close"].dropna()
    fx.index = naive(fx.index)
    fx_m = fx.groupby(fx.index.to_period("M")).first()
    fx_last = float(fx.iloc[-1])
    out = []
    for t in queue:
        m = meta[t]
        sym = m["symbol"]
        us = m["market"] == "US"
        rec = {k: m[k] for k in ("ticker", "name", "market", "category", "invests", "desc")}
        try:
            tk = yf.Ticker(sym)
            raw = tk.history(period="max", interval="1d", auto_adjust=False)
            adj = tk.history(period="max", interval="1d", auto_adjust=True)["Close"].dropna()
            raw.index = naive(raw.index)
            adj.index = naive(adj.index)
            close = raw["Close"].dropna()
            div = raw["Dividends"]
            div = div[div > 0]
            last_date = close.index[-1]
            price = float(close.iloc[-1])
            one_y = div[div.index > last_date - pd.Timedelta(days=365)]
            ttm = float(one_y.sum())
            rec["last_date"] = last_date.strftime("%Y-%m-%d")
            rec["first_date"] = close.index[0].strftime("%Y-%m-%d")
            rec["price"] = round(price, 4)
            rec["ttm_div"] = round(ttm, 4)
            rec["pay_count"] = int(len(one_y))
            rec["freq"] = "매월" if len(one_y) >= 11 else ("분기" if len(one_y) >= 4 else ("반기" if len(one_y) >= 2 else ("연 1회" if len(one_y) == 1 else "없음")))
            rec["yield_pct"] = round(ttm / price * 100, 2) if price else None
            five = last_date - pd.DateOffset(years=5)
            past = div[(div.index > five - pd.Timedelta(days=365)) & (div.index <= five)]
            if close.index[0] <= five - pd.Timedelta(days=365) and past.sum() > 0:
                rec["div_5y_ago"] = round(float(past.sum()), 4)
                rec["div_growth_5y_pct"] = round((ttm / float(past.sum()) - 1) * 100, 1)
            else:
                rec["div_5y_ago"] = None
                rec["div_growth_5y_pct"] = None
            # 적립식: 월 50만원, 최대 10년
            am = adj.groupby(adj.index.to_period("M")).first()
            lp = am.index[-1]
            n = min(MAX_MONTHS, len(am))
            months = pd.period_range(lp - n + 1, lp, freq="M")
            units = 0.0
            for p in months:
                px = float(am.get(p, float("nan")))
                if px != px:
                    continue
                if us:
                    f = float(fx_m.get(p, float("nan")))
                    if f != f:
                        f = float(fx_m[fx_m.index <= p].iloc[-1])
                    units += AMT / (px * f)
                else:
                    units += AMT / px
            value = units * float(adj.iloc[-1]) * (fx_last if us else 1.0)
            rec["dca_months"] = len(months)
            rec["dca_invested"] = AMT * len(months)
            rec["dca_value"] = round(value)
            y = (ttm / price) if price else 0
            rec["dca_monthly_income"] = round(value * y / 12)
            for target in (500_000, 1_000_000, 3_000_000):
                rec[f"need_{target // 10000}"] = round(target * 12 / y) if y else None
            rec["status"] = "ok" if ttm > 0 else "no_dividend_data"
        except Exception as ex:
            rec["status"] = f"error: {ex}"
        out.append(rec)
        print(t, rec.get("status"), rec.get("yield_pct"), rec.get("freq"), rec.get("div_growth_5y_pct"))
        time.sleep(0.7)
    res = {"meta": {"generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                    "fx_last_krw_per_usd": round(fx_last, 2),
                    "assumptions": "배당수익률=최근 1년 배당/현재가(세전), 필요 원금은 현재 배당수익률 유지 가정, 적립은 월 50만원·분배금 재투자·환율 반영, 세금·수수료 미반영"},
           "etfs": out}
    (ROOT / "income.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
