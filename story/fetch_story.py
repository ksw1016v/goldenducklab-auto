"""월급일기 원고에 쓰는 실제 데이터 계산 → story/data.json (GitHub Actions에서 실행: Yahoo 접속 필요)

티커별: 최근 10년 최대 하락률(수정주가 기준)과 고점·저점 날짜,
        그 고점 달부터 매달 같은 금액을 계속 넣었다면 지금 수익률(달러 기준)
"""
import json, pathlib, re, datetime
import yfinance as yf

ROOT = pathlib.Path(__file__).resolve().parent
tickers = set()
for p in sorted(ROOT.glob("[0-9][0-9].json")):
    tickers |= set(re.findall(r"\{([A-Z0-9]+)\.(?:mdd|peak|trough|dip_ret|dip_months)\}", p.read_text(encoding="utf-8")))
    ep = json.loads(p.read_text(encoding="utf-8"))
    for s in ep.get("scenes", []):
        if s.get("type") in ("mdd", "dip"):
            tickers |= set(s.get("tickers", [s.get("ticker")]))
tickers.discard(None)
out = {"asof": None, "tickers": {}}
for t in sorted(tickers):
    h = yf.Ticker(t).history(period="11y", auto_adjust=True)["Close"].dropna()
    h = h[h.index >= h.index[-1] - datetime.timedelta(days=3653)]
    peak = h.cummax()
    dd = h / peak - 1
    tr = dd.idxmin()
    pk = h[:tr].idxmax()
    # 고점 달부터 매달 첫 거래일에 같은 금액 매수
    m = h[h.index >= pk].groupby([h[h.index >= pk].index.year, h[h.index >= pk].index.month]).head(1)
    units = (1 / m).sum()
    val = units * h.iloc[-1]
    out["tickers"][t] = {"mdd": round(float(dd.min()) * 100, 1), "peak": pk.strftime("%Y-%m-%d"), "trough": tr.strftime("%Y-%m-%d"),
                         "dip_months": int(len(m)), "dip_ret": round(float(val / len(m) - 1) * 100, 1), "last": h.index[-1].strftime("%Y-%m-%d")}
    out["asof"] = h.index[-1].strftime("%Y-%m-%d")
    print(t, out["tickers"][t])
(ROOT / "data.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
