"""ETF 적립식 투자 시뮬레이션 (GitHub Actions에서 실행)

- 월 10만·30만·50만원을 매달 첫 거래일에 투자했다고 가정
- 배당·분배금은 재투자 (수정주가 auto_adjust 기준)
- 미국 ETF는 매달 그날 원달러 환율로 원화를 달러로 바꿔 매수, 평가도 최신 환율로 원화 환산
- 세금·수수료·환전비용은 반영하지 않음
결과: etf/results.csv, etf/results.json
"""
import csv, json, time, pathlib, datetime
import pandas as pd
import yfinance as yf

ROOT = pathlib.Path(__file__).parent
AMOUNTS = [100_000, 300_000, 500_000]
YEARS = [20, 10, 5]


def monthly_first(series):
    s = series.dropna()
    s.index = pd.to_datetime(s.index).tz_localize(None)
    return s.groupby(s.index.to_period("M")).first()


def main():
    fx_d = yf.Ticker("KRW=X").history(period="max", interval="1d", auto_adjust=True)["Close"]
    fx_d.index = pd.to_datetime(fx_d.index).tz_localize(None)
    fx_m = monthly_first(fx_d)
    fx_last = float(fx_d.dropna().iloc[-1])

    rows = list(csv.DictReader(open(ROOT / "etf_list.csv", encoding="utf-8")))
    out = []
    for r in rows:
        sym = r["symbol"]
        rec = {k: r[k] for k in ("ticker", "name", "market", "category", "invests", "desc")}
        try:
            t = yf.Ticker(sym)
            h = t.history(period="max", interval="1d", auto_adjust=True)["Close"].dropna()
            h.index = pd.to_datetime(h.index).tz_localize(None)
            info = {}
            try:
                info = t.get_info() or {}
            except Exception:
                pass
            rec["yahoo_name"] = info.get("longName") or info.get("shortName") or ""
            er = info.get("netExpenseRatio") or info.get("annualReportExpenseRatio")
            rec["expense_ratio_pct"] = round(float(er), 2) if er not in (None, "") else ""
            rec["first_date"] = h.index[0].strftime("%Y-%m-%d")
            rec["last_date"] = h.index[-1].strftime("%Y-%m-%d")
            m = monthly_first(h)
            last_price = float(h.iloc[-1])
            last_p = m.index[-1]
            usd = r["market"] == "US"
            for yrs in YEARS:
                start = last_p - yrs * 12 + 1
                months = pd.period_range(start, last_p, freq="M")
                if m.index[0] > start:
                    for a in AMOUNTS:
                        rec[f"v{yrs}y_{a//10000}"] = ""
                    continue
                units = 0.0
                for p in months:
                    price = float(m.get(p, float("nan")))
                    if price != price:
                        continue
                    if usd:
                        fx = float(fx_m.get(p, float("nan")))
                        if fx != fx:
                            fx = float(fx_m[fx_m.index <= p].iloc[-1])
                        units += 1.0 / (price * fx)
                    else:
                        units += 1.0 / price
                value_per_won = units * last_price * (fx_last if usd else 1.0)
                for a in AMOUNTS:
                    rec[f"v{yrs}y_{a//10000}"] = round(value_per_won * a)
                rec[f"invest{yrs}y_months"] = len(months)
                rec[f"ret{yrs}y_pct"] = round((value_per_won / len(months) - 1) * 100, 1)
            rec["status"] = "ok"
        except Exception as e:
            rec["status"] = f"error: {e}"
        out.append(rec)
        print(sym, rec.get("status"), rec.get("yahoo_name", ""))
        time.sleep(0.7)

    meta = {"generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            "fx_last_krw_per_usd": round(fx_last, 2),
            "assumptions": "매달 첫 거래일 적립, 분배금 재투자(수정주가), 미국 ETF는 매월 환율로 매수·최신 환율로 평가, 세금·수수료 미반영"}
    (ROOT / "results.json").write_text(json.dumps({"meta": meta, "etfs": out}, ensure_ascii=False, indent=1), encoding="utf-8")
    keys = sorted({k for r in out for k in r}, key=lambda k: (k not in rows[0], k))
    with open(ROOT / "results.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(out)


if __name__ == "__main__":
    main()
