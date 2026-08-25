#!/usr/bin/env python3
"""
WealthOrbit Idea Intelligence — builds the public page from ideas.csv

USAGE   python build_log.py
OUTPUT  idea-intelligence.html   -> upload to wealthorbit.ca/idea-intelligence/

The CSV is the source of truth. Never edit the HTML by hand.
"""

import csv, os
from datetime import datetime

CSV_FILE = "ideas.csv"
OUT_FILE = "idea-intelligence.html"

STANDING_ORDER = (
    "Every idea our system grades A+ is published here, without exception, "
    "before the outcome is known. Ideas are never removed, never edited after "
    "publication, and never selected for inclusion based on how they performed."
)


def load():
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(v, d=0.0):
    try:    return float(v)
    except: return d


def money(v, sign=True):
    s = ("+" if v >= 0 else "\u2212") if sign else ""
    return f"{s}${abs(v):,.0f}"


def fmt_date(d):
    try:    return datetime.strptime(d, "%Y-%m-%d").strftime("%d %b %Y")
    except: return d


def aggregates(rows):
    closed = [r for r in rows if r["status"].upper() in ("CLOSED", "RESOLVED")]
    live   = [r for r in rows if r["status"].upper() == "OPEN"]
    ds     = [num(r["result_dollars"]) for r in closed]
    wins   = [d for d in ds if d > 0]
    losses = [d for d in ds if d <= 0]
    n      = len(ds)
    return {
        "published": len(rows), "closed": len(closed), "live": len(live),
        "win_pct":   f"{len(wins)/n*100:.0f}"   if n else "\u2014",
        "loss_pct":  f"{len(losses)/n*100:.0f}" if n else "\u2014",
        "win_n": len(wins), "loss_n": len(losses),
        "won":       money(sum(wins), False)        if wins   else "$0",
        "lost":      money(abs(sum(losses)), False) if losses else "$0",
        "avg_win":   money(sum(wins)/len(wins), False)          if wins   else "\u2014",
        "avg_loss":  money(abs(sum(losses)/len(losses)), False) if losses else "\u2014",
        "net":       money(sum(ds)) if n else "\u2014",
        "net_dir":   ("up" if sum(ds) >= 0 else "down") if n else "",
    }


def curve(rows):
    """Cumulative dollar result over time, as an inline SVG."""
    closed = sorted([r for r in rows if r["status"].upper() in ("CLOSED", "RESOLVED")],
                    key=lambda r: r.get("exit_date") or r["published"])
    if len(closed) < 2:
        return ""
    run, pts = 0.0, [0.0]
    for r in closed:
        run += num(r["result_dollars"]); pts.append(run)

    W, H, P = 760, 96, 8
    lo, hi = min(pts + [0]), max(pts + [0])
    span = (hi - lo) or 1
    step = (W - 2*P) / (len(pts) - 1)
    xy = [(P + i*step, H - P - (v - lo)/span * (H - 2*P)) for i, v in enumerate(pts)]
    line = " ".join(f"{'M' if i==0 else 'L'}{x:.1f},{y:.1f}" for i,(x,y) in enumerate(xy))
    zero = H - P - (0 - lo)/span * (H - 2*P)
    area = line + f" L{xy[-1][0]:.1f},{zero:.1f} L{xy[0][0]:.1f},{zero:.1f} Z"
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.5"/>' for x,y in xy[1:])
    cls  = "up" if pts[-1] >= 0 else "down"
    return f"""<svg class="curve {cls}" viewBox="0 0 {W} {H}" preserveAspectRatio="none" aria-hidden="true">
      <line class="zero" x1="{P}" y1="{zero:.1f}" x2="{W-P}" y2="{zero:.1f}"/>
      <path class="fill" d="{area}"/><path class="stroke" d="{line}"/><g class="dot">{dots}</g>
    </svg>"""


def live_card(r):
    return f"""      <article class="live-card">
        <header><span class="tick">{r['underlying']}</span><span class="grade">{r['grade']}</span></header>
        <p class="struct">{r['structure']}</p>
        <dl>
          <div><dt>Published</dt><dd>{fmt_date(r['published'])}</dd></div>
          <div><dt>Expiry</dt><dd>{fmt_date(r['expiry'])}</dd></div>
          <div><dt>Break-even</dt><dd>{r['breakeven']}</dd></div>
          <div><dt>Invalidation</dt><dd>{r['invalidation']}</dd></div>
        </dl>
      </article>"""


def closed_row(r):
    d = num(r["result_dollars"])
    cls = "up" if d > 0 else "down"
    return f"""        <tr>
          <td class="d">{fmt_date(r['published'])}</td>
          <td class="d">{fmt_date(r.get('exit_date') or '')}</td>
          <td class="tk">{r['underlying']}</td>
          <td class="st">{r['structure']}</td>
          <td class="n">{r['iv_rank']}</td>
          <td class="why">{r['exit_reason']}</td>
          <td class="res {cls}">{money(d)}</td>
        </tr>"""


def build(rows, a):
    live   = [r for r in rows if r["status"].upper() == "OPEN"]
    closed = sorted([r for r in rows if r["status"].upper() in ("CLOSED","RESOLVED")],
                    key=lambda r: r.get("exit_date") or r["published"], reverse=True)

    live_html = ("\n".join(live_card(r) for r in live) if live
                 else '      <p class="empty">No live ideas right now. New ideas appear here the day they are published.</p>')

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Idea Intelligence \u00b7 WealthOrbit</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{
  --paper:#0d0f12; --card:#15181d; --card-2:#1a1e24;
  --rule:#242830; --rule-2:#1e2229;
  --ink:#e8eaed; --ink-2:#b4bbc4; --ink-3:#8b939d;
  --up:#4ade80; --down:#f87171; --live:#60a5fa;
  --display:'Space Grotesk',system-ui,sans-serif;
  --body:'IBM Plex Sans',system-ui,sans-serif;
  --mono:'IBM Plex Mono',ui-monospace,monospace;
}}
*{{box-sizing:border-box}}
html{{-webkit-text-size-adjust:100%}}
body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.65 var(--body);
     -webkit-font-smoothing:antialiased}}
.wrap{{max-width:1000px;margin:0 auto;padding:56px 28px 120px}}

/* ---- masthead ---- */
.mast{{padding-bottom:28px}}
.eyebrow{{font:500 11px/1 var(--mono);letter-spacing:.18em;text-transform:uppercase;
         color:var(--ink-3);margin:0 0 14px}}
h1{{font:700 38px/1.1 var(--display);letter-spacing:-.02em;margin:0 0 10px}}
.thesis{{font-size:17px;color:var(--ink-2);margin:0;max-width:52ch}}

/* ---- standing order ---- */
.order{{background:var(--card);border:1px solid var(--rule);border-left:3px solid var(--ink-2);
       border-radius:6px;padding:20px 24px;margin-bottom:8px}}
.order h2{{font:500 11px/1 var(--mono);letter-spacing:.14em;text-transform:uppercase;
          color:var(--ink-3);margin:0 0 10px}}
.order p{{margin:0;font-size:15px;line-height:1.7;color:var(--ink)}}

/* ---- figures ---- */
section{{padding:32px 0 0}}
.lbl{{font:500 11px/1 var(--mono);letter-spacing:.14em;text-transform:uppercase;
     color:var(--ink-3);margin:0 0 20px}}
.figs{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1px;
       background:var(--rule);border:1px solid var(--rule);border-radius:6px;overflow:hidden}}
.fig{{background:var(--card);padding:18px 20px}}
.fig .k{{font:400 11px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;
        color:var(--ink-3);display:block;margin-bottom:8px}}
.fig .v{{font:600 26px/1 var(--mono);letter-spacing:-.02em;display:block}}
.fig .v .pc{{font-size:17px;font-weight:500;color:var(--ink-3);margin-left:1px}}
.fig .s{{font-size:12.5px;color:var(--ink-3);display:block;margin-top:7px}}
.up{{color:var(--up)}} .down{{color:var(--down)}}

/* ---- curve ---- */
.curve{{width:100%;height:96px;display:block;margin:20px 0 0;overflow:visible;
       background:var(--card);border:1px solid var(--rule);border-radius:6px;padding:8px 0}}
.curve .zero{{stroke:var(--rule);stroke-width:1;stroke-dasharray:2 3}}
.curve .stroke{{fill:none;stroke-width:1.75;stroke-linejoin:round;stroke-linecap:round}}
.curve .dot circle{{stroke:var(--paper);stroke-width:1.5}}
.curve.up .stroke{{stroke:var(--up)}} .curve.up .fill{{fill:var(--up);opacity:.12}}
.curve.up .dot circle{{fill:var(--up)}}
.curve.down .stroke{{stroke:var(--down)}} .curve.down .fill{{fill:var(--down);opacity:.12}}
.curve.down .dot circle{{fill:var(--down)}}
.curve-cap{{font:400 12px/1 var(--mono);color:var(--ink-3);margin:12px 0 0}}

/* ---- live ---- */
.live-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(268px,1fr));gap:16px}}
.live-card{{background:var(--card);border:1px solid var(--rule);border-top:2px solid var(--live);
           border-radius:6px;padding:18px 20px 16px}}
.live-card header{{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px}}
.tick{{font:600 16px/1 var(--mono);letter-spacing:.02em}}
.grade{{font:600 11px/1 var(--mono);letter-spacing:.08em;color:var(--live);
       border:1px solid var(--live);border-radius:3px;padding:3px 6px}}
.struct{{font-size:14px;color:var(--ink-2);margin:0 0 14px}}
.live-card dl{{margin:0;display:grid;grid-template-columns:1fr;gap:7px;
              border-top:1px solid var(--rule-2);padding-top:12px}}
.live-card dl div{{display:flex;justify-content:space-between;gap:12px;font-size:13px}}
.live-card dt{{color:var(--ink-3)}}
.live-card dd{{margin:0;font-family:var(--mono);font-size:12.5px;text-align:right}}
.empty{{color:var(--ink-3);font-size:15px;margin:0}}

/* ---- table ---- */
.scroll{{overflow-x:auto;margin:0 -28px;padding:0 28px}}
table{{width:100%;min-width:720px;border-collapse:collapse}}
th{{text-align:left;font:500 11px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;
   color:var(--ink-3);padding:0 14px 12px 0;border-bottom:1px solid var(--rule);white-space:nowrap}}
td{{padding:15px 14px 15px 0;border-bottom:1px solid var(--rule);font-size:14px;vertical-align:top}}
tr:last-child td{{border-bottom:none}}
.d{{font-family:var(--mono);font-size:12.5px;color:var(--ink-3);white-space:nowrap}}
.tk{{font-family:var(--mono);font-weight:600;font-size:13.5px}}
.st{{color:var(--ink-2)}}
.n{{font-family:var(--mono);font-size:13px;color:var(--ink-2)}}
.why{{color:var(--ink-3);font-size:13.5px}}
.res{{font:600 15px/1 var(--mono);text-align:right;padding-right:0;white-space:nowrap}}
th:last-child{{text-align:right;padding-right:0}}

/* ---- note + limits ---- */
.note{{font-size:14.5px;color:var(--ink-2);margin:24px 0 0;padding-left:16px;
      border-left:2px solid var(--rule);max-width:62ch}}
.limits{{margin-top:48px;padding-top:32px;border-top:1px solid var(--rule)}}
.limits h2{{font:500 11px/1 var(--mono);letter-spacing:.14em;text-transform:uppercase;
           color:var(--ink-3);margin:0 0 18px}}
.limits p{{margin:0 0 13px;font-size:14.5px;color:var(--ink-2);max-width:66ch}}
.limits strong{{color:var(--ink);font-weight:600}}
footer{{margin-top:40px;padding-top:20px;border-top:1px solid var(--rule);
       font:400 12.5px/1.7 var(--mono);color:var(--ink-3)}}

@media (max-width:640px){{
  .wrap{{padding:36px 20px 80px}}
  h1{{font-size:34px}}
  .order{{grid-template-columns:1fr;gap:12px}}
  .scroll{{margin:0 -20px;padding:0 20px}}
}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important;transition:none!important}}}}
</style>
</head>
<body>
<div class="wrap">

  <header class="mast">
    <p class="eyebrow">WealthOrbit</p>
    <h1>Idea Intelligence</h1>
    <p class="thesis">Every A&#43; idea our system generates, published the day it is generated \u2014 before anyone knows how it ends.</p>
  </header>

  <div class="order">
    <h2>Standing order</h2>
    <p>{STANDING_ORDER}</p>
  </div>

  <section>
    <p class="lbl">The record</p>
    <div class="figs">
      <div class="fig"><span class="k">Published</span><span class="v">{a['published']}</span><span class="s">all time</span></div>
      <div class="fig"><span class="k">Closed</span><span class="v">{a['closed']}</span><span class="s">outcome known</span></div>
      <div class="fig"><span class="k">Live</span><span class="v">{a['live']}</span><span class="s">still running</span></div>
      <div class="fig"><span class="k">Won</span><span class="v up">{a['win_pct']}<span class="pc">%</span></span><span class="s">{a['win_n']} of {a['closed']} \u00b7 avg {a['avg_win']}</span></div>
      <div class="fig"><span class="k">Lost</span><span class="v down">{a['loss_pct']}<span class="pc">%</span></span><span class="s">{a['loss_n']} of {a['closed']} \u00b7 avg {a['avg_loss']}</span></div>
    </div>
  </section>

  <section>
    <p class="lbl">Dollars</p>
    <div class="figs">
      <div class="fig"><span class="k">Total won</span><span class="v up">{a['won']}</span><span class="s">across {a['win_n']} ideas</span></div>
      <div class="fig"><span class="k">Total lost</span><span class="v down">{a['lost']}</span><span class="s">across {a['loss_n']} ideas</span></div>
      <div class="fig"><span class="k">Net</span><span class="v {a['net_dir']}">{a['net']}</span><span class="s">{a['closed']} closed ideas</span></div>
    </div>
    {curve(rows)}
    <p class="curve-cap">Cumulative dollar result, in the order ideas closed.</p>
    <p class="note">A win ratio describes how often, not how much. Read it against the average win
    and average loss beside it \u2014 a high ratio with larger losses than wins is still a losing record.</p>
  </section>

  <section>
    <p class="lbl">Live \u00b7 outcome not yet known</p>
    <div class="live-grid">
{live_html}
    </div>
  </section>

  <section>
    <p class="lbl">Closed</p>
    <div class="scroll">
      <table>
        <thead><tr>
          <th>Published</th><th>Closed</th><th>Underlying</th><th>Structure</th>
          <th>IV rank</th><th>Reason</th><th>Result</th>
        </tr></thead>
        <tbody>
{chr(10).join(closed_row(r) for r in closed)}
        </tbody>
      </table>
    </div>
  </section>

  <div class="limits">
    <h2>What this shows, and what it does not</h2>
    <p>This is a forward record, not a backtest. Every idea appears here before its outcome was known.</p>
    <p>It can show whether the process is followed consistently, and how the results are actually distributed.</p>
    <p>It cannot show that any of this will continue. A sample of this size cannot separate a real edge
    from a good run. Patterns you notice in it are hypotheses, not evidence.</p>
    <p>Because only A&#43; ideas are published, this page cannot demonstrate that the grading predicts
    outcomes. There is no comparison group.</p>
    <p><strong>Nothing here is a recommendation to trade.</strong></p>
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
    a = aggregates(rows)
    open(OUT_FILE, "w", encoding="utf-8").write(build(rows, a))
    print(f"Built {OUT_FILE}")
    print(f"  Published {a['published']} \u00b7 Closed {a['closed']} \u00b7 Live {a['live']}")
    print(f"  Won {a['win_pct']}% ({a['win_n']}) avg {a['avg_win']}  \u00b7  Lost {a['loss_pct']}% ({a['loss_n']}) avg {a['avg_loss']}")
    print(f"  Total won {a['won']} \u00b7 Total lost {a['lost']} \u00b7 Net {a['net']}")
