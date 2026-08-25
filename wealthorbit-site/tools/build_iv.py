#!/usr/bin/env python3
"""
WealthOrbit Volatility Table — builds the public page from iv_rank.csv

USAGE   python build_iv.py
OUTPUT  volatility.html  -> upload to wealthorbit.ca/volatility/

IV rank = (current IV - 52w low) / (52w high - 52w low) x 100
Compares a stock to its own history, which absolute IV cannot do.
"""

import csv, os
from datetime import datetime, date

CSV_FILE = "iv_rank.csv"
OUT_FILE = "volatility.html"


def load():
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def n(v, d=0.0):
    try:    return float(v)
    except: return d


def rank(r):
    lo, hi, cur = n(r["iv_52w_low"]), n(r["iv_52w_high"]), n(r["iv"])
    return 0.0 if hi <= lo else max(0.0, min(100.0, (cur - lo) / (hi - lo) * 100))


def band(pct):
    if pct >= 70: return "hi",  "Rich"
    if pct >= 40: return "mid", "Middling"
    return "lo", "Cheap"


def days_to(d):
    try:    return (datetime.strptime(d, "%Y-%m-%d").date() - date.today()).days
    except: return None


def row(r):
    pct = rank(r)
    cls, word = band(pct)
    lo, hi, cur = n(r["iv_52w_low"]), n(r["iv_52w_high"]), n(r["iv"])
    dte = days_to(r.get("earnings_date", ""))
    if dte is None:
        earn = '<span class="none">\u2014</span>'
    elif dte < 0:
        earn = '<span class="none">\u2014</span>'
    elif dte <= 14:
        earn = f'<span class="soon">{dte}d</span>'
    else:
        earn = f'<span class="far">{dte}d</span>'

    return f"""        <tr>
          <td class="sym">{r['symbol']}</td>
          <td class="nm">{r['name']}</td>
          <td class="sec">{r['sector']}</td>
          <td class="num">{cur:.1f}</td>
          <td class="range">
            <div class="bar"><span class="lo">{lo:.0f}</span>
              <div class="track"><i class="mark {cls}" style="left:{pct:.1f}%"></i></div>
              <span class="hi">{hi:.0f}</span></div>
          </td>
          <td class="rk {cls}">{pct:.0f}</td>
          <td class="bd {cls}">{word}</td>
          <td class="ev">{earn}</td>
        </tr>"""


def build(rows):
    rows = sorted(rows, key=rank, reverse=True)
    hi  = sum(1 for r in rows if rank(r) >= 70)
    lo  = sum(1 for r in rows if rank(r) < 40)
    soon = sum(1 for r in rows
               if (d := days_to(r.get("earnings_date",""))) is not None and 0 <= d <= 14)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Volatility Table \u00b7 WealthOrbit</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{
  --paper:#0d0f12; --card:#15181d; --rule:#242830; --rule-2:#1e2229;
  --ink:#e8eaed; --ink-2:#b4bbc4; --ink-3:#8b939d;
  --hi:#f87171; --mid:#fbbf24; --lo:#4ade80; --live:#60a5fa;
  --mono:'IBM Plex Mono',ui-monospace,monospace;
  --body:'IBM Plex Sans',system-ui,sans-serif;
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 var(--body);
     -webkit-font-smoothing:antialiased}}
.wrap{{max-width:1140px;margin:0 auto;padding:52px 24px 100px}}
.eyebrow{{font:500 11px/1 var(--mono);letter-spacing:.16em;text-transform:uppercase;
         color:var(--ink-3);margin:0 0 12px}}
h1{{font-size:34px;letter-spacing:-.02em;margin:0 0 10px}}
.sub{{color:var(--ink-2);margin:0 0 32px;max-width:60ch}}

.order{{background:var(--card);border:1px solid var(--rule);border-left:3px solid var(--ink-2);
       border-radius:6px;padding:20px 24px;margin-bottom:28px}}
.order h2{{font:500 11px/1 var(--mono);letter-spacing:.14em;text-transform:uppercase;
          color:var(--ink-3);margin:0 0 10px}}
.order p{{margin:0 0 10px;font-size:15px}}
.order p:last-child{{margin:0}}
.order code{{font-family:var(--mono);font-size:13.5px;color:var(--ink);
            background:var(--rule-2);padding:2px 6px;border-radius:3px}}

.figs{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1px;
      background:var(--rule);border:1px solid var(--rule);border-radius:6px;
      overflow:hidden;margin-bottom:28px}}
.fig{{background:var(--card);padding:18px 20px}}
.fig .k{{font:400 11px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;
        color:var(--ink-3);display:block;margin-bottom:8px}}
.fig .v{{font:600 26px/1 var(--mono);display:block}}
.fig .s{{font-size:12.5px;color:var(--ink-3);display:block;margin-top:7px}}

.scroll{{overflow-x:auto;margin:0 -24px;padding:0 24px}}
table{{width:100%;min-width:900px;border-collapse:collapse}}
th{{text-align:left;font:500 11px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;
   color:var(--ink-3);padding:0 16px 12px 0;border-bottom:1px solid var(--rule);white-space:nowrap}}
td{{padding:13px 16px 13px 0;border-bottom:1px solid var(--rule-2);font-size:14px}}
tr:last-child td{{border-bottom:none}}
.sym{{font:600 14px/1 var(--mono)}}
.nm{{color:var(--ink-2)}}
.sec{{color:var(--ink-3);font-size:13px}}
.num{{font-family:var(--mono);font-size:13.5px;text-align:right;width:70px}}
th.num,th.rk,th.ev{{text-align:right}}

.range{{width:190px}}
.bar{{display:flex;align-items:center;gap:8px}}
.bar .lo,.bar .hi{{font:400 11px/1 var(--mono);color:var(--ink-3);width:20px}}
.bar .hi{{text-align:right}}
.track{{position:relative;flex:1;height:4px;background:var(--rule);border-radius:2px}}
.mark{{position:absolute;top:-3px;width:3px;height:10px;border-radius:1px;
      transform:translateX(-1.5px)}}
.mark.hi{{background:var(--hi)}} .mark.mid{{background:var(--mid)}} .mark.lo{{background:var(--lo)}}

.rk{{font:600 16px/1 var(--mono);text-align:right;width:56px}}
.bd{{font:500 11px/1 var(--mono);letter-spacing:.06em;text-transform:uppercase;width:84px}}
td.hi,.rk.hi{{color:var(--hi)}} td.mid,.rk.mid{{color:var(--mid)}} td.lo,.rk.lo{{color:var(--lo)}}
.ev{{text-align:right;font-family:var(--mono);font-size:13px;width:70px}}
.soon{{color:var(--live);font-weight:600}} .far{{color:var(--ink-3)}} .none{{color:var(--rule)}}

.key{{display:flex;flex-wrap:wrap;gap:22px;margin:22px 0 0;font-size:13px;color:var(--ink-3)}}
.key i{{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:7px;
       vertical-align:-1px}}
.notes{{margin-top:48px;padding-top:32px;border-top:1px solid var(--rule)}}
.notes h2{{font:500 11px/1 var(--mono);letter-spacing:.14em;text-transform:uppercase;
          color:var(--ink-3);margin:0 0 18px}}
.notes p{{margin:0 0 13px;font-size:14.5px;color:var(--ink-2);max-width:68ch}}
.notes strong{{color:var(--ink);font-weight:600}}
footer{{margin-top:40px;padding-top:20px;border-top:1px solid var(--rule);
       font:400 12.5px/1.7 var(--mono);color:var(--ink-3)}}
@media(max-width:640px){{.wrap{{padding:36px 18px 80px}}h1{{font-size:27px}}
  .scroll{{margin:0 -18px;padding:0 18px}}}}
</style>
</head>
<body>
<div class="wrap">

  <p class="eyebrow">WealthOrbit</p>
  <h1>Volatility Table</h1>
  <p class="sub">Where option premium sits today relative to each name's own twelve-month range.</p>

  <div class="order">
    <h2>What IV rank is</h2>
    <p><code>(current IV &minus; 52-week low) &divide; (52-week high &minus; 52-week low) &times; 100</code></p>
    <p>Implied volatility on its own tells you almost nothing. Thirty-six percent might be the
    calmest a name has been all year, or the most expensive. Rank compares a name to itself,
    which is the only comparison that means anything.</p>
  </div>

  <div class="figs">
    <div class="fig"><span class="k">Names tracked</span><span class="v">{len(rows)}</span><span class="s">updated daily</span></div>
    <div class="fig"><span class="k">Rich</span><span class="v hi">{hi}</span><span class="s">rank 70 and above</span></div>
    <div class="fig"><span class="k">Cheap</span><span class="v lo">{lo}</span><span class="s">rank under 40</span></div>
    <div class="fig"><span class="k">Earnings inside 14d</span><span class="v live">{soon}</span><span class="s">check before any trade</span></div>
  </div>

  <div class="scroll">
    <table>
      <thead><tr>
        <th>Symbol</th><th>Name</th><th>Sector</th><th class="num">IV</th>
        <th>52-week range</th><th class="rk">Rank</th><th>Reading</th><th class="ev">Earnings</th>
      </tr></thead>
      <tbody>
{chr(10).join(row(r) for r in rows)}
      </tbody>
    </table>
  </div>

  <div class="key">
    <span><i style="background:var(--hi)"></i>Rich \u2014 premium expensive for this name</span>
    <span><i style="background:var(--mid)"></i>Middling</span>
    <span><i style="background:var(--lo)"></i>Cheap \u2014 premium low for this name</span>
    <span><i style="background:var(--live)"></i>Earnings within fourteen days</span>
  </div>

  <div class="notes">
    <h2>How to read it, and how not to</h2>
    <p>A high rank means premium is expensive <strong>relative to this name's own history</strong>.
    It does not mean the options are overpriced. Volatility can be high for good reasons and go higher.</p>
    <p>A low rank means the opposite, and the same caution applies in reverse.</p>
    <p>Rank says nothing about <strong>direction</strong>. Volatility measures the size of expected
    movement, not which way.</p>
    <p>Where earnings fall inside the next fourteen days, expect rank to be elevated for that reason
    alone, and expect it to fall sharply after the announcement regardless of the result.</p>
    <p><strong>This is a measurement, not a recommendation. Nothing here is advice to trade.</strong></p>
  </div>

  <footer>
    Updated {datetime.now().strftime('%d %b %Y')} \u00b7 WealthOrbit<br>
    Education only. Not investment, tax or legal advice.
  </footer>

</div>
</body>
</html>"""


if __name__ == "__main__":
    if not os.path.exists(CSV_FILE):
        raise SystemExit(f"ERROR: {CSV_FILE} not found.")
    rows = load()
    open(OUT_FILE, "w", encoding="utf-8").write(build(rows))
    rs = sorted(rows, key=rank, reverse=True)
    print(f"Built {OUT_FILE}  \u00b7  {len(rows)} names")
    print(f"  Richest:  {rs[0]['symbol']:<6} rank {rank(rs[0]):.0f}")
    print(f"  Cheapest: {rs[-1]['symbol']:<6} rank {rank(rs[-1]):.0f}")
    print(f"  Rich (70+): {sum(1 for r in rows if rank(r)>=70)}  \u00b7  Cheap (<40): {sum(1 for r in rows if rank(r)<40)}")
