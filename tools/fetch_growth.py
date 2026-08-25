#!/usr/bin/env python3
"""
Pull 15 years of monthly total-return prices from IBKR -> growth_data.json
Full S&P 500 + benchmark ETFs (~495 symbols).

USAGE
  python fetch_growth.py              # fetch everything not already saved
  python fetch_growth.py --retry      # retry only the ones that failed
  python fetch_growth.py AAPL NVDA    # specific symbols

REQUIRES
  pip install ib_insync
  TWS / IB Gateway running, API enabled

NOTES
  This takes 25-40 minutes for the full list. It SAVES AS IT GOES to
  growth_cache.json, so you can stop it (Ctrl+C) and rerun to continue.
  Nothing is lost.

  whatToShow="ADJUSTED_LAST" gives split- AND dividend-adjusted closes.
  Over 15 years dividends are a large part of the answer.
"""

import json, os, sys, time
from datetime import date
from ib_insync import IB, Stock
from sp500 import UNIVERSE

HOST, PORT, CLIENT_ID = "127.0.0.1", 7497, 92
CACHE  = "growth_cache.json"
FAILED = "growth_failed.json"
OUT    = "growth_data.json"
YEARS  = 15
BENCH  = "SPY"
PACE   = 1.1          # seconds between symbols — IBKR pacing


def load(path, default):
    try:    return json.load(open(path, encoding="utf-8"))
    except Exception: return default


def monthly(ib, contract):
    bars = ib.reqHistoricalData(
        contract, endDateTime="", durationStr=f"{YEARS} Y",
        barSizeSetting="1 month", whatToShow="ADJUSTED_LAST",
        useRTH=True, formatDate=1, timeout=45)
    return [(str(b.date), round(b.close, 4)) for b in bars if b.close and b.close > 0]


def main(only=None, retry=False):
    cache  = load(CACHE, {})
    failed = load(FAILED, [])

    if only:
        todo = [u for u in UNIVERSE if u[0] in only]
    elif retry:
        todo = [u for u in UNIVERSE if u[0] in set(failed)]
        print(f"Retrying {len(todo)} previously failed symbols\n")
    else:
        todo = [u for u in UNIVERSE if u[0] not in cache]

    if not todo:
        print("Nothing to fetch — cache is complete.")
    else:
        ib = IB(); ib.connect(HOST, PORT, clientId=CLIENT_ID)
        print(f"Connected  ·  {len(todo)} to fetch  ·  {len(cache)} already cached")
        print(f"Estimated time: {len(todo)*PACE/60:.0f} min\n")

        new_failed = []
        for i, (sym, name, sector) in enumerate(todo, 1):
            c = Stock(sym.replace(".", " "), "SMART", "USD")
            try:
                ib.qualifyContracts(c)
                s = monthly(ib, c)
                if len(s) < 24:
                    raise ValueError(f"only {len(s)} bars")
                cache[sym] = {"name": name, "sector": sector, "series": s}
                mult = s[-1][1] / s[0][1]
                print(f"[{i:>3}/{len(todo)}] {sym:<7}{len(s):>4} bars  {mult:>7.2f}x  {name}")
            except Exception as e:
                new_failed.append(sym)
                print(f"[{i:>3}/{len(todo)}] {sym:<7}FAILED  {str(e)[:44]}")

            if i % 20 == 0:                       # checkpoint
                json.dump(cache, open(CACHE, "w"), separators=(",", ":"))
            time.sleep(PACE)

        ib.disconnect()
        json.dump(cache, open(CACHE, "w"), separators=(",", ":"))
        failed = sorted(set(failed if retry else []) | set(new_failed)) if not only else new_failed
        json.dump(failed, open(FAILED, "w"))
        if new_failed:
            print(f"\n{len(new_failed)} failed. Rerun with:  python fetch_growth.py --retry")

    # ---- write the page data ----
    payload = {
        "generated": date.today().isoformat(),
        "benchmark": BENCH,
        "basis": "Dividend and split adjusted (total return)",
        "symbols": cache,
    }
    json.dump(payload, open(OUT, "w", encoding="utf-8"), separators=(",", ":"))
    kb = os.path.getsize(OUT) / 1024
    print(f"\nWrote {OUT}  ·  {len(cache)} symbols  ·  {kb/1024:.1f} MB")
    print("Now run: python build_growth.py")


if __name__ == "__main__":
    args  = [a for a in sys.argv[1:] if not a.startswith("--")]
    retry = "--retry" in sys.argv
    main(set(a.upper() for a in args) or None, retry)
