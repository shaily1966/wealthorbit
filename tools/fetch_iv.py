#!/usr/bin/env python3
"""
Backfill 52-week IV range from IBKR, and write iv_rank.csv

USAGE
  python fetch_iv.py                 # all symbols in UNIVERSE
  python fetch_iv.py NVDA AAPL       # just these

REQUIRES
  pip install ib_insync
  TWS or IB Gateway running, API enabled, port 7497 (paper) / 7496 (live)

HOW IT WORKS
  reqHistoricalData with whatToShow="OPTION_IMPLIED_VOLATILITY" returns one
  year of daily IV in a single call. Last bar = today's IV. Min/max of the
  series = the 52-week range. No stored history needed.
"""

import sys, csv, time
from datetime import date
from ib_insync import IB, Stock

HOST, PORT, CLIENT_ID = "127.0.0.1", 7497, 91
OUT = "iv_rank.csv"

# symbol, display name, sector
UNIVERSE = [
    ("SPY",   "S&P 500 ETF",             "Index"),
    ("QQQ",   "Nasdaq 100 ETF",          "Index"),
    ("IWM",   "Russell 2000 ETF",        "Index"),
    ("AAPL",  "Apple",                   "Technology"),
    ("MSFT",  "Microsoft",               "Technology"),
    ("NVDA",  "NVIDIA",                  "Technology"),
    ("AMZN",  "Amazon",                  "Consumer"),
    ("GOOGL", "Alphabet",                "Technology"),
    ("META",  "Meta Platforms",          "Technology"),
    ("TSLA",  "Tesla",                   "Consumer"),
    ("JPM",   "JPMorgan Chase",          "Financials"),
    ("XOM",   "Exxon Mobil",             "Energy"),
    ("JNJ",   "Johnson & Johnson",       "Healthcare"),
    ("WMT",   "Walmart",                 "Consumer"),
    ("UNH",   "UnitedHealth",            "Healthcare"),
    ("BAC",   "Bank of America",         "Financials"),
    ("AMD",   "Advanced Micro Devices",  "Technology"),
    ("GLD",   "Gold ETF",                "Commodity"),
    ("USO",   "Crude Oil ETF",           "Commodity"),
    ("TLT",   "20+ Year Treasury ETF",   "Rates"),
]

ETFS = {"SPY", "QQQ", "IWM", "GLD", "USO", "TLT"}


def iv_series(ib, contract):
    """One year of daily implied volatility."""
    bars = ib.reqHistoricalData(
        contract, endDateTime="", durationStr="1 Y", barSizeSetting="1 day",
        whatToShow="OPTION_IMPLIED_VOLATILITY", useRTH=True, formatDate=1)
    return [b.close * 100 for b in bars if b.close and b.close > 0]


def last_price(ib, contract):
    bars = ib.reqHistoricalData(
        contract, endDateTime="", durationStr="2 D", barSizeSetting="1 day",
        whatToShow="TRADES", useRTH=True, formatDate=1)
    return bars[-1].close if bars else 0.0


def earnings(ib, contract, is_etf):
    if is_etf:
        return ""
    try:
        for t in ib.reqFundamentalData(contract, "CalendarReport").split("<"):
            if "EarningsDate" in t or "Date type=" in t:
                pass
    except Exception:
        pass
    return ""          # fill manually, or wire your own source


def main(symbols=None):
    rows_wanted = [u for u in UNIVERSE if not symbols or u[0] in symbols]

    ib = IB()
    ib.connect(HOST, PORT, clientId=CLIENT_ID)
    print(f"Connected to IBKR  ·  {len(rows_wanted)} symbols\n")
    print(f"{'SYM':<7}{'PRICE':>9}{'IV':>7}{'52W LOW':>9}{'52W HIGH':>10}{'RANK':>7}  BARS")
    print("-" * 60)

    out = []
    for sym, name, sector in rows_wanted:
        c = Stock(sym, "SMART", "USD")
        try:
            ib.qualifyContracts(c)
            s = iv_series(ib, c)
            if len(s) < 60:
                print(f"{sym:<7}  only {len(s)} bars — skipped")
                continue
            cur, lo, hi = s[-1], min(s), max(s)
            px = last_price(ib, c)
            rank = 0 if hi <= lo else (cur - lo) / (hi - lo) * 100
            print(f"{sym:<7}{px:>9.2f}{cur:>7.1f}{lo:>9.1f}{hi:>10.1f}{rank:>7.0f}  {len(s)}")
            out.append({
                "symbol": sym, "name": name, "sector": sector,
                "price": f"{px:.2f}", "iv": f"{cur:.1f}",
                "iv_52w_low": f"{lo:.1f}", "iv_52w_high": f"{hi:.1f}",
                "earnings_date": "", "updated": date.today().isoformat(),
            })
        except Exception as e:
            print(f"{sym:<7}  FAILED: {e}")
        time.sleep(0.6)          # IBKR pacing

    ib.disconnect()

    if not out:
        raise SystemExit("\nNo data written.")

    # preserve any earnings dates already in the CSV
    try:
        existing = {r["symbol"]: r.get("earnings_date", "")
                    for r in csv.DictReader(open(OUT, newline="", encoding="utf-8"))}
        for r in out:
            r["earnings_date"] = existing.get(r["symbol"], "")
    except FileNotFoundError:
        pass

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader(); w.writerows(out)

    print(f"\nWrote {OUT}  ·  {len(out)} rows")
    print("Earnings dates preserved from the previous file. Now run: python build_iv.py")


if __name__ == "__main__":
    main(set(a.upper() for a in sys.argv[1:]) or None)
