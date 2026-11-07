"""현금흐름 황금알: 국내·미국 배당주·배당 ETF 건전성·위험성 점검 (GitHub Actions에서 실행)

후보: etf/dividend_candidates.csv
각 종목마다
- 배당: 최근 1년 배당, 배당수익률, 지급 주기·지급 월, 연속 배당 연수, 최근 5년 삭감 여부, 5년 배당 성장
- 건전성: 배당성향, 부채비율, 시가총액
- 위험성: 최근 3년 변동성(연율), 최근 5년 최대 낙폭
- 월 50·100·300만원 현금흐름에 필요한 원금(세전, 현재 배당수익률 유지 가정, 원화)
을 계산하고 기준을 통과한 종목만 발행 대상(pass=True)으로 표시한다.
결과: etf/income.json
"""
import csv, json, time, datetime, pathlib
import numpy as np
import pandas as pd
import yfinance as yf

ROOT = pathlib.Path(__file__).parent

# 건전성·위험성 기준
RULES = {
    "min_years": 10,          # 연속 배당 연수
    "max_payout": 80,         # 배당성향(%) 상한 (리츠·인프라 제외)
    "max_de": 200,            # 부채비율(%) 상한 (금융·리츠·인프라 제외)
    "max_vol": 35,            # 3년 변동성(연율 %) 상한
    "min_mdd": -50,           # 5년 최대 낙폭(%) 하한
    "yield_lo": 1.5, "yield_hi": 9.0,
    "min_cap_usd": 30e9, "min_cap_krw": 3e12,
    # ETF 기준
    "etf_min_years": 5,       # 연속 분배 연수
    "etf_min_aum_usd": 1e9, "etf_min_aum_krw": 1e11,
    "etf_max_fee": 0.6,       # 총보수(%) 상한
}
NO_PAYOUT = {"리츠", "인프라"}
NO_DEBT = {"금융", "리츠", "인프라"}


def naive(idx):
    return pd.to_datetime(idx).tz_localize(None)


def main():
    fx = yf.Ticker("KRW=X").history(period="5d", interval="1d")["Close"].dropna()
    fx_last = float(fx.iloc[-1])
    rows = list(csv.DictReader(open(ROOT / "dividend_candidates.csv", encoding="utf-8")))
    out = []
    for r in rows:
        rec = {k: r[k] for k in ("ticker", "name", "market", "type", "category", "invests", "desc")}
        us = r["market"] == "US"
        try:
            tk = yf.Ticker(r["symbol"])
            h = tk.history(period="max", interval="1d", auto_adjust=False)
            h.index = naive(h.index)
            close = h["Close"].dropna()
            div = h["Dividends"]
            div = div[div > 0]
            info = {}
            try:
                info = tk.get_info() or {}
            except Exception:
                pass
            last = close.index[-1]
            price = float(close.iloc[-1])
            one = div[div.index > last - pd.Timedelta(days=365)]
            ttm = float(one.sum())
            y = ttm / price * 100 if price else 0
            two = div[div.index > last - pd.Timedelta(days=730)]
            gaps = two.index.to_series().diff().dt.days.dropna()
            g = float(gaps.median()) if len(gaps) else 999
            freq = "매월" if g <= 45 else ("분기" if g <= 120 else ("반기" if g <= 220 else "연 1회"))
            months = sorted({d.month for d in one.index})
            annual = div.groupby(div.index.year).sum()
            last_full = last.year - 1
            # 연속 배당 연수: 배당 기준일이 바뀌어 한 해가 비고 다음 해에 몰린 경우(국내 2023~ 제도 변경)는 끊긴 걸로 보지 않음
            yrs = 0
            first = close.index[0].year
            yr = last_full
            while yr >= first:
                if annual.get(yr, 0) > 0:
                    yrs += 1
                elif annual.get(yr + 1, 0) > 0 and annual.get(yr - 1, 0) > 0 and annual.get(yr + 1, 0) >= 1.5 * annual.get(yr - 1, 0):
                    yrs += 1
                else:
                    break
                yr -= 1
            # 배당 삭감: 지급 시점이 옮겨 다녀도 흔들리지 않게 최근 2년 합계를 그 전 2년 합계와 비교(최근 6년 = 2년씩 3구간)
            def win(a, b):
                return float(div[(div.index > last - pd.DateOffset(years=a)) & (div.index <= last - pd.DateOffset(years=b))].sum())
            blocks = [win(6, 4), win(4, 2), win(2, 0)]
            cut = any(blocks[i] > 0 and blocks[i + 1] < blocks[i] * 0.9 for i in range(2))
            five = last - pd.DateOffset(years=5)
            past = float(div[(div.index > five - pd.Timedelta(days=365)) & (div.index <= five)].sum())
            growth = round((ttm / past - 1) * 100, 1) if past > 0 else None
            ret = close[close.index > last - pd.DateOffset(years=3)].pct_change().dropna()
            vol = float(ret.std() * np.sqrt(252) * 100)
            c5 = close[close.index > five]
            mdd = float(((c5 / c5.cummax()) - 1).min() * 100)
            payout = info.get("payoutRatio")
            payout = round(payout * 100, 1) if isinstance(payout, (int, float)) and payout > 0 else None
            de = info.get("debtToEquity")
            de = round(float(de), 1) if isinstance(de, (int, float)) and de > 0 else None
            cap = info.get("marketCap")
            cap = float(cap) if isinstance(cap, (int, float)) else None
            price_krw = price * (fx_last if us else 1.0)
            ttm_krw = ttm * (fx_last if us else 1.0)

            checks = []
            def chk(name, val, ok, rule, skip=False):
                checks.append({"name": name, "value": val, "ok": (None if skip else bool(ok)), "rule": rule})
            is_etf = r["type"] == "ETF"
            aum = fee = None
            if is_etf:
                aum = info.get("totalAssets")
                aum = float(aum) if isinstance(aum, (int, float)) and aum > 0 else None
                fee = info.get("netExpenseRatio")
                if not isinstance(fee, (int, float)):
                    fee = info.get("annualReportExpenseRatio")
                    fee = fee * 100 if isinstance(fee, (int, float)) else None
                fee = round(float(fee), 2) if isinstance(fee, (int, float)) and fee > 0 else None
                chk("연속 분배", f"{yrs}년", yrs >= RULES["etf_min_years"], f"{RULES['etf_min_years']}년 이상")
                chk("분배 삭감(최근 6년)", "없음" if not cut else "있음", not cut, "없어야 통과",
                    skip=r["category"] == "배당·커버드콜")
                aok = aum is not None and aum >= (RULES["etf_min_aum_usd"] if us else RULES["etf_min_aum_krw"])
                av = (f"${aum / 1e9:,.1f}B" if us else f"{aum / 1e8:,.0f}억원") if aum else "정보 없음"
                chk("운용 규모", av, aok, "미국 10억달러·국내 1,000억원 이상", skip=aum is None)
                chk("총보수", f"연 {fee:.2f}%" if fee else "정보 없음", (fee or 0) <= RULES["etf_max_fee"],
                    f"{RULES['etf_max_fee']}% 이하", skip=fee is None)
            else:
                chk("연속 배당", f"{yrs}년", yrs >= RULES["min_years"], f"{RULES['min_years']}년 이상")
                chk("배당 삭감(최근 6년)", "없음" if not cut else "있음", not cut, "없어야 통과")
                chk("배당성향", f"{payout:.0f}%" if payout else "정보 없음", (payout or 0) <= RULES["max_payout"], f"{RULES['max_payout']}% 이하",
                    skip=(r["category"] in NO_PAYOUT or payout is None))
                chk("부채비율", f"{de:.0f}%" if de else "정보 없음", (de or 0) <= RULES["max_de"], f"{RULES['max_de']}% 이하",
                    skip=(r["category"] in NO_DEBT or de is None))
                capok = cap is not None and cap >= (RULES["min_cap_usd"] if us else RULES["min_cap_krw"])
                capv = (f"${cap / 1e9:,.0f}B" if us else f"{cap / 1e12:,.1f}조원") if cap else "정보 없음"
                chk("시가총액", capv, capok, "미국 300억달러·국내 3조원 이상", skip=cap is None)
            chk("변동성(3년)", f"연 {vol:.0f}%", vol <= RULES["max_vol"], f"{RULES['max_vol']}% 이하")
            chk("최대 낙폭(5년)", f"{mdd:.0f}%", mdd >= RULES["min_mdd"], f"{RULES['min_mdd']}%보다 작게")
            chk("배당수익률", f"{y:.1f}%", RULES["yield_lo"] <= y <= RULES["yield_hi"], f"{RULES['yield_lo']}~{RULES['yield_hi']}%")
            risk = "낮음" if (vol < 22 and mdd > -30) else ("보통" if vol < 32 else "높음")
            passed = all(c["ok"] is not False for c in checks) and risk != "높음" and ttm > 0

            rec.update({
                "yahoo_name": info.get("longName") or info.get("shortName") or "",
                "last_date": last.strftime("%Y-%m-%d"), "first_date": close.index[0].strftime("%Y-%m-%d"),
                "price": round(price, 2), "ttm_div": round(ttm, 4), "yield_pct": round(y, 2),
                "freq": freq, "pay_months": months, "pay_count": int(len(one)),
                "years_paid": yrs, "cut_5y": cut, "div_5y_ago": round(past, 4) if past else None, "div_growth_5y_pct": growth,
                "payout_pct": payout, "debt_equity_pct": de, "market_cap": cap, "aum": aum, "fee_pct": fee,
                "vol_3y_pct": round(vol, 1), "mdd_5y_pct": round(mdd, 1), "risk": risk,
                "checks": checks, "pass": passed,
            })
            for target in (500_000, 1_000_000, 3_000_000):
                rec[f"need_{target // 10000}"] = round(target * 12 / (ttm_krw / price_krw)) if ttm_krw else None
            rec["status"] = "ok"
        except Exception as ex:
            rec["status"] = f"error: {ex}"
            rec["pass"] = False
        out.append(rec)
        print(r["ticker"], rec.get("status"), rec.get("yahoo_name", ""), rec.get("yield_pct"), rec.get("years_paid"),
              rec.get("risk"), "PASS" if rec.get("pass") else "-")
        time.sleep(0.7)
    res = {"meta": {"generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                    "fx_last_krw_per_usd": round(fx_last, 2), "rules": RULES,
                    "assumptions": "배당수익률=최근 1년 배당/현재가(세전), 필요 원금은 현재 배당수익률 유지 가정·원화 환산, 세금·수수료 미반영"},
           "etfs": out}
    (ROOT / "income.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
