"""매일 아침 경제 브리핑용 데이터 수집 (GitHub Actions에서 실행).
시장: yfinance / 미국 경제지표: 미국 노동통계국(BLS) 공개 API / 한·미 기준금리: econ/manual.json(수동, 결정 후 갱신)
결과: econ/data.json
"""
import json, io, time, datetime, pathlib, urllib.request
import numpy as np, pandas as pd, yfinance as yf

ROOT = pathlib.Path(__file__).parent
# key, 심볼, 이름, 그룹, 단위, 소수점, 둥근 숫자 간격(돌파 판정)
MARKETS = [
    ("kospi", "^KS11", "코스피", "kr", "pt", 2, 100),
    ("kosdaq", "^KQ11", "코스닥", "kr", "pt", 2, 50),
    ("spx", "^GSPC", "S&P 500", "us", "pt", 2, 100),
    ("ndx", "^IXIC", "나스닥", "us", "pt", 2, 1000),
    ("dji", "^DJI", "다우", "us", "pt", 2, 1000),
    ("sox", "^SOX", "필라델피아 반도체", "us", "pt", 2, 500),
    ("usdkrw", "KRW=X", "원/달러", "fx", "원", 1, 10),
    ("jpykrw", "JPYKRW=X", "원/엔(100엔)", "fx", "원", 2, 10),
    ("eurkrw", "EURKRW=X", "원/유로", "fx", "원", 1, 10),
    ("dxy", "DX-Y.NYB", "달러인덱스", "fx", "", 2, 1),
    ("us10y", "^TNX", "미국 10년 국채금리", "rate", "%", 3, 0.25),
    ("wti", "CL=F", "WTI 유가", "cmd", "$", 2, 10),
    ("gold", "GC=F", "금", "cmd", "$", 1, 100),
    ("btc", "BTC-USD", "비트코인", "cmd", "$", 0, 10000),
    ("vix", "^VIX", "VIX 공포지수", "cmd", "", 2, 5),
]
BLS = [  # 미국 노동통계국 공개 API(키 없이 하루 25회) · id, 이름, 변환
    ("CUUR0000SA0", "미국 소비자물가(CPI)", "yoy"),
    ("CUUR0000SA0L1E", "미국 근원 CPI", "yoy"),
    ("LNS14000000", "미국 실업률", "level"),
    ("CES0000000001", "미국 비농업 고용", "diff"),
]


def series(sym):
    h = yf.Ticker(sym).history(period="max", interval="1d", auto_adjust=False)
    h.index = pd.to_datetime(h.index).tz_localize(None).normalize()
    c = h["Close"].dropna()
    return c[~c.index.duplicated(keep="last")]


def market(key, sym, name, group, unit, dec, step):
    c = series(sym)
    if key == "jpykrw":
        c = c * 100
    last, prev = float(c.iloc[-1]), float(c.iloc[-2])
    chg = last - prev
    pct = chg / prev * 100 if prev else 0
    y1 = c[c.index > c.index[-1] - pd.DateOffset(years=1)]
    ret = c.pct_change().dropna()
    vol = float(ret[ret.index > c.index[-1] - pd.DateOffset(years=1)].std() * 100) or 1
    streak = 0
    d = np.sign(np.diff(c.values[-30:]))
    if len(d) and d[-1] != 0:
        for s in d[::-1]:
            if s == d[-1]:
                streak += 1
            else:
                break
        streak *= int(d[-1])
    hi52, lo52 = float(y1.max()), float(y1.min())
    ath = float(c.max())
    m1 = c[c.index > c.index[-1] - pd.DateOffset(days=31)]
    return {"key": key, "symbol": sym, "name": name, "group": group, "unit": unit, "dec": dec, "step": step,
            "date": c.index[-1].strftime("%Y-%m-%d"), "prev_date": c.index[-2].strftime("%Y-%m-%d"),
            "last": round(last, 4), "prev": round(prev, 4), "chg": round(chg, 4), "pct": round(pct, 3),
            "z": round(pct / vol, 2), "vol_1y": round(vol, 3), "streak": streak,
            "hi52": round(hi52, 4), "lo52": round(lo52, 4), "ath": round(ath, 4),
            "is_hi52": last >= hi52 * 0.9999, "is_lo52": last <= lo52 * 1.0001, "is_ath": last >= ath * 0.9999,
            "m1": [round(float(v), 4) for v in m1.values],
            "chg_1m_pct": round((last / float(m1.iloc[0]) - 1) * 100, 2),
            "chg_ytd_pct": round((last / float(c[c.index < pd.Timestamp(c.index[-1].year, 1, 1)].iloc[-1]) - 1) * 100, 2)}


def bls_all():
    y = datetime.date.today().year
    body = json.dumps({"seriesid": [b[0] for b in BLS], "startyear": str(y - 2), "endyear": str(y)}).encode()
    req = urllib.request.Request("https://api.bls.gov/publicAPI/v1/timeseries/data/", data=body,
                                 headers={"Content-Type": "application/json", "User-Agent": "goldenducklab-brief"})
    res = json.loads(urllib.request.urlopen(req, timeout=90).read())
    out = {}
    for ser in res["Results"]["series"]:
        sid = ser["seriesID"]
        name, how = next((b[1], b[2]) for b in BLS if b[0] == sid)
        rows = [r for r in ser["data"] if r["period"].startswith("M") and r["period"] != "M13" and r["value"] not in ("-", "")]
        pts = sorted((f"{r['year']}-{r['period'][1:]}", float(r["value"])) for r in rows)
        d = dict(pts)
        keys = [k for k, _ in pts]
        def val(k):
            if how == "yoy":
                y0, m0 = k.split("-")
                b = d.get(f"{int(y0) - 1}-{m0}")
                return (d[k] / b - 1) * 100 if b else None
            if how == "diff":
                i = keys.index(k)
                return d[k] - d[keys[i - 1]] if i > 0 else None
            return d[k]
        last, prev = keys[-1], keys[-2]
        out[sid] = {"id": sid, "name": name, "how": how, "date": last, "value": round(val(last), 2),
                    "prev": round(val(prev), 2) if val(prev) is not None else None, "prev_date": prev}
    return out


def main():
    out = {"generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), "markets": {}, "macro": {}, "errors": []}
    for m in MARKETS:
        try:
            out["markets"][m[0]] = market(*m)
            print(m[0], out["markets"][m[0]]["date"], out["markets"][m[0]]["last"], out["markets"][m[0]]["pct"])
        except Exception as ex:
            out["errors"].append(f"{m[0]}: {ex}")
            print("ERR", m[0], ex)
        time.sleep(0.5)
    for i in range(3):
        try:
            out["macro"] = bls_all()
            print(out["macro"])
            break
        except Exception as ex:
            print("ERR bls", ex)
            if i == 2:
                out["errors"].append(f"bls: {ex}")
            time.sleep(10)
    man = ROOT / "manual.json"
    if man.exists():
        out["manual"] = json.loads(man.read_text(encoding="utf-8"))
    (ROOT / "data.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
