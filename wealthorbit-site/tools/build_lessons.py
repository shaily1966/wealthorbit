#!/usr/bin/env python3
"""
Build the whole course as self-contained lesson pages.

Reads:   day-XX/01-slides.md   +   audio/day-XX/*.mp3
Writes:  lessons/day-XX.html   +   lessons/index.html

One HTML file per session. Slides render from the markdown, audio plays
per slide, autoplay advances to the next slide. No PowerPoint, no video
export, no Canva. Cost: nothing.

USAGE
  python build_lessons.py            # all sessions
  python build_lessons.py day-01     # one session
"""

import os, re, sys, json, html

SESSIONS = ["day-01","day-02","day-02-lab","day-03","day-04","day-05","day-06",
            "day-06-lab","day-07","day-08","day-09","day-10","day-11","day-12",
            "day-13","day-14","day-15","day-16","day-17"]

TITLES = {
 "day-01":"Introduction to options","day-02":"Brokerage accounts and buying power",
 "day-02-lab":"Lab · Setting up IBKR","day-03":"Market terminology",
 "day-04":"Call options","day-05":"Put options","day-06":"The option chain",
 "day-06-lab":"Lab · Placing an order","day-07":"Option pricing",
 "day-08":"Time decay and volatility","day-09":"The Greeks",
 "day-10":"Strategy foundation","day-11":"Spreads",
 "day-12":"Condors, straddles and strangles","day-13":"Calendars and diagonals",
 "day-14":"Trade selection","day-15":"Risk and position management",
 "day-16":"Building your process","day-17":"The Canadian layer",
}
NUM = {s: (i+1) for i, s in enumerate(SESSIONS)}
OUT = "lessons"


# ---------- tiny markdown renderer (only what the slides use) ----------
def md(text):
    out, i = [], 0
    lines = text.split("\n")
    while i < len(lines):
        ln = lines[i]

        if not ln.strip():
            i += 1; continue

        # table
        if ln.lstrip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append(lines[i].strip()); i += 1
            cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
            body = [r for r in cells if not re.match(r'^[\s:\-]+$', "".join(r))]
            head, rest = (body[0], body[1:]) if len(body) > 1 else (None, body)
            t = ['<table>']
            if head and any(h for h in head):
                t.append("<thead><tr>" + "".join(f"<th>{inl(c)}</th>" for c in head) + "</tr></thead>")
            else:
                rest = body
            t.append("<tbody>")
            for r in rest:
                t.append("<tr>" + "".join(f"<td>{inl(c)}</td>" for c in r) + "</tr>")
            t.append("</tbody></table>")
            out.append("".join(t)); continue

        # big statement
        if ln.startswith("# "):
            out.append(f"<p class='shout'>{inl(ln[2:])}</p>"); i += 1; continue

        # quote
        if ln.startswith("> "):
            q = []
            while i < len(lines) and lines[i].startswith("> "):
                q.append(lines[i][2:]); i += 1
            out.append(f"<blockquote>{inl(' '.join(q))}</blockquote>"); continue

        # list (incl. checkboxes)
        if re.match(r'^\s*[-*]\s', ln):
            items = []
            while i < len(lines) and re.match(r'^\s*[-*]\s', lines[i]):
                t = re.sub(r'^\s*[-*]\s', '', lines[i])
                box = ""
                if t.startswith("[ ] "):
                    t, box = t[4:], "<i class='box'></i>"
                items.append(f"<li>{box}{inl(t)}</li>"); i += 1
            out.append("<ul>" + "".join(items) + "</ul>"); continue

        # numbered
        if re.match(r'^\s*\d+\.\s', ln):
            items = []
            while i < len(lines) and re.match(r'^\s*\d+\.\s', lines[i]):
                items.append(f"<li>{inl(re.sub(r'^\s*\d+\.\s','',lines[i]))}</li>"); i += 1
            out.append("<ol>" + "".join(items) + "</ol>"); continue

        out.append(f"<p>{inl(ln)}</p>"); i += 1
    return "".join(out)


def inl(t):
    t = html.escape(t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', t)
    t = re.sub(r'`(.+?)`', r'<code>\1</code>', t)
    t = t.replace("---", "&mdash;").replace("--", "&ndash;")
    return t


# ---------- parse ----------
def slides(session):
    p = f"{session}/01-slides.md"
    if not os.path.exists(p): return []
    txt = open(p, encoding="utf-8").read()
    out = []
    for m in re.finditer(r'^### SLIDE ([0-9A-Z]+)\s*$(.*?)(?=^### SLIDE |\Z)',
                         txt, re.S | re.M):
        sid, blk = m.group(1), m.group(2)
        tm = re.search(r'\*\*Title:\*\*\s*(.+)', blk)
        title = tm.group(1).strip() if tm else ""
        body = blk
        if tm: body = body[tm.end():]
        body = re.split(r'\*\*Design:\*\*', body)[0]
        body = body.replace("---", "").strip()
        out.append({"id": sid, "title": title, "html": md(body)})
    return out


def audio_map(session):
    d = os.path.join("audio", session)
    if not os.path.isdir(d): return {}
    m = {}
    for f in os.listdir(d):
        g = re.match(rf'{re.escape(session)}_slide-([0-9A-Z]+)\.mp3$', f)
        if g: m[g.group(1)] = f"../audio/{session}/{f}"
    return m


# ---------- page ----------
PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__NUM__. __TITLE__ · WealthOrbit Trader</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{--paper:#0d0f12;--card:#15181d;--card2:#1a1e24;--rule:#242830;--rule2:#1e2229;
 --ink:#e8eaed;--ink2:#b4bbc4;--ink3:#8b939d;--live:#60a5fa;--up:#4ade80;--down:#f87171;
 --mono:'IBM Plex Mono',ui-monospace,monospace;--body:'IBM Plex Sans',system-ui,sans-serif}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 var(--body);
 -webkit-font-smoothing:antialiased}
.top{position:sticky;top:0;z-index:20;background:rgba(13,15,18,.94);
 backdrop-filter:blur(8px);border-bottom:1px solid var(--rule)}
.topin{max-width:1080px;margin:0 auto;padding:14px 24px;display:flex;
 align-items:center;justify-content:space-between;gap:16px}
.back{color:var(--ink3);text-decoration:none;font:500 12px/1 var(--mono);letter-spacing:.08em}
.back:hover{color:var(--ink)}
.sess{font:500 12px/1 var(--mono);letter-spacing:.08em;color:var(--ink3);text-align:right}
.sess b{color:var(--ink);font-weight:600}
.prog{height:2px;background:var(--rule2)}
.prog i{display:block;height:100%;background:var(--live);width:0;transition:width .3s}

.stage{max-width:1080px;margin:0 auto;padding:36px 24px 0}
.slide{background:var(--card);border:1px solid var(--rule);border-radius:10px;
 padding:52px 56px;min-height:440px;display:flex;flex-direction:column;justify-content:center}
.sn{font:500 11px/1 var(--mono);letter-spacing:.16em;color:var(--ink3);margin:0 0 20px}
.slide h2{font-size:31px;line-height:1.2;letter-spacing:-.02em;margin:0 0 26px;font-weight:600}
.slide p{margin:0 0 15px;font-size:17px;color:var(--ink2)}
.slide p:last-child{margin-bottom:0}
.slide .shout{font-size:29px;line-height:1.28;font-weight:600;color:var(--ink);
 margin:22px 0;letter-spacing:-.01em}
.slide ul,.slide ol{margin:0 0 16px;padding-left:22px}
.slide li{margin-bottom:11px;font-size:17px;color:var(--ink2)}
.slide li::marker{color:var(--ink3)}
.slide ul li .box{display:inline-block;width:13px;height:13px;border:1.5px solid var(--ink3);
 border-radius:3px;margin-right:11px;vertical-align:-1px}
.slide blockquote{margin:22px 0;padding:2px 0 2px 20px;border-left:2px solid var(--live);
 color:var(--ink);font-size:17px}
.slide strong{color:var(--ink);font-weight:600}
.slide code{font-family:var(--mono);font-size:15px;background:var(--rule2);
 padding:2px 6px;border-radius:3px;color:var(--ink)}
.slide table{width:100%;border-collapse:collapse;margin:18px 0;font-size:15.5px}
.slide th{text-align:left;font:500 11px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;
 color:var(--ink3);padding:0 16px 11px 0;border-bottom:1px solid var(--rule)}
.slide td{padding:12px 16px 12px 0;border-bottom:1px solid var(--rule2);color:var(--ink2)}
.slide tr:last-child td{border-bottom:none}
.slide td strong{color:var(--ink)}

.bar{max-width:1080px;margin:0 auto;padding:20px 24px 8px;display:flex;align-items:center;gap:16px}
audio{flex:1;height:38px}
audio::-webkit-media-controls-panel{background:var(--card)}
.nav{display:flex;gap:8px}
button{background:var(--card);border:1px solid var(--rule);color:var(--ink);
 font:500 14px/1 var(--body);padding:11px 18px;border-radius:6px;cursor:pointer}
button:hover:not(:disabled){background:var(--card2);border-color:var(--ink3)}
button:disabled{opacity:.35;cursor:default}
button:focus-visible{outline:2px solid var(--live);outline-offset:2px}
.auto{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--ink3);
 white-space:nowrap;cursor:pointer;user-select:none}
.auto input{accent-color:var(--live);width:15px;height:15px}

.rail{max-width:1080px;margin:0 auto;padding:14px 24px 60px;display:flex;flex-wrap:wrap;gap:5px}
.dot{width:26px;height:26px;border-radius:5px;border:1px solid var(--rule);background:var(--card);
 color:var(--ink3);font:500 10px/1 var(--mono);cursor:pointer;display:grid;place-items:center}
.dot:hover{border-color:var(--ink3);color:var(--ink)}
.dot.on{background:var(--live);border-color:var(--live);color:#06101f;font-weight:600}
.dot.done{color:var(--ink2);border-color:var(--rule)}
@media(max-width:720px){.slide{padding:32px 24px;min-height:340px}
 .slide h2{font-size:24px}.slide .shout{font-size:22px}.stage{padding:20px 16px 0}
 .bar{flex-wrap:wrap;padding:16px}.rail{padding:12px 16px 48px}}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
</style>
</head>
<body>

<div class="top">
  <div class="topin">
    <a class="back" href="index.html">&larr; ALL SESSIONS</a>
    <div class="sess">SESSION __NUM__ &middot; <b>__TITLE__</b></div>
  </div>
  <div class="prog"><i id="pg"></i></div>
</div>

<div class="stage">
  <div class="slide" id="slide"></div>
</div>

<div class="bar">
  <div class="nav">
    <button id="prev">&larr; Prev</button>
    <button id="next">Next &rarr;</button>
  </div>
  <audio id="au" controls preload="none"></audio>
  <label class="auto"><input type="checkbox" id="ap" checked> Auto-advance</label>
</div>

<div class="rail" id="rail"></div>

<script>
const SL = __SLIDES__, AU = __AUDIO__, KEY = 'wo-__SESSION__';
let i = 0;
const $ = x => document.getElementById(x);

function paint(){
  const s = SL[i];
  $('slide').innerHTML = `<p class="sn">SLIDE ${s.id} / ${SL.length}</p>` +
                         (s.title ? `<h2>${s.title}</h2>` : '') + s.html;
  const src = AU[s.id];
  if(src){ $('au').src = src; $('au').style.visibility='visible'; }
  else   { $('au').removeAttribute('src'); $('au').style.visibility='hidden'; }
  $('prev').disabled = i===0;
  $('next').disabled = i===SL.length-1;
  $('pg').style.width = ((i+1)/SL.length*100)+'%';
  document.querySelectorAll('.dot').forEach((d,n)=>{
    d.className = 'dot' + (n===i?' on':(n<i?' done':''));
  });
  try{ localStorage.setItem(KEY, i); }catch(e){}
  window.scrollTo({top:0,behavior:'smooth'});
}
function go(n){ if(n>=0 && n<SL.length){ i=n; paint(); } }

SL.forEach((s,n)=>{
  const b=document.createElement('button');
  b.className='dot'; b.textContent=s.id; b.title='Slide '+s.id;
  b.onclick=()=>go(n); $('rail').appendChild(b);
});

$('prev').onclick = ()=>go(i-1);
$('next').onclick = ()=>go(i+1);
$('au').addEventListener('ended', ()=>{
  if($('ap').checked && i<SL.length-1){ go(i+1); setTimeout(()=>$('au').play().catch(()=>{}),350); }
});
document.addEventListener('keydown', e=>{
  if(e.target.tagName==='INPUT') return;
  if(e.key==='ArrowRight') go(i+1);
  if(e.key==='ArrowLeft')  go(i-1);
  if(e.key===' '){ e.preventDefault(); $('au').paused ? $('au').play() : $('au').pause(); }
});
try{ const v=parseInt(localStorage.getItem(KEY)); if(v>0 && v<SL.length) i=v; }catch(e){}
paint();
</script>
</body>
</html>"""


INDEX = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>WealthOrbit Trader · Course</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{--paper:#0d0f12;--card:#15181d;--card2:#1a1e24;--rule:#242830;--rule2:#1e2229;
 --ink:#e8eaed;--ink2:#b4bbc4;--ink3:#8b939d;--live:#60a5fa;
 --mono:'IBM Plex Mono',ui-monospace,monospace;--body:'IBM Plex Sans',system-ui,sans-serif}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 var(--body);
 -webkit-font-smoothing:antialiased}
.wrap{max-width:860px;margin:0 auto;padding:56px 24px 100px}
.eyebrow{font:500 11px/1 var(--mono);letter-spacing:.16em;text-transform:uppercase;
 color:var(--ink3);margin:0 0 12px}
h1{font-size:36px;letter-spacing:-.02em;margin:0 0 10px}
.sub{color:var(--ink2);margin:0 0 36px;max-width:56ch}
.list{border:1px solid var(--rule);border-radius:8px;overflow:hidden}
a.row{display:flex;align-items:center;gap:18px;padding:17px 22px;background:var(--card);
 border-bottom:1px solid var(--rule);text-decoration:none;color:var(--ink)}
a.row:last-child{border-bottom:none}
a.row:hover{background:var(--card2)}
.n{font:600 13px/1 var(--mono);color:var(--ink3);width:26px;flex:none}
.t{flex:1;font-size:16px}
.t small{display:block;color:var(--ink3);font:400 12.5px/1.5 var(--mono);margin-top:3px}
.lab{font:500 10px/1 var(--mono);letter-spacing:.1em;color:var(--live);
 border:1px solid var(--live);border-radius:3px;padding:3px 6px}
.go{color:var(--ink3);font-size:18px}
footer{margin-top:40px;padding-top:20px;border-top:1px solid var(--rule);
 font:400 12.5px/1.7 var(--mono);color:var(--ink3)}
@media(max-width:640px){.wrap{padding:36px 18px 70px}h1{font-size:28px}}
</style>
</head>
<body><div class="wrap">
  <p class="eyebrow">WealthOrbit</p>
  <h1>WealthOrbit Trader</h1>
  <p class="sub">Nineteen sessions. __SLIDES__ slides. __HOURS__ hours of narration.
  Work through them in order &mdash; each one assumes the last.</p>
  <div class="list">__ROWS__</div>
  <footer>Education only. Not investment, tax or legal advice.<br>
  Profitability is not a learning outcome.</footer>
</div></body></html>"""


def build(sessions):
    os.makedirs(OUT, exist_ok=True)
    rows, total_slides, total_audio = [], 0, 0

    for s in sessions:
        sl = slides(s)
        if not sl:
            print(f"{s:<12} no slides — skipped"); continue
        au = audio_map(s)
        total_slides += len(sl); total_audio += len(au)

        page = (PAGE.replace("__SLIDES__", json.dumps(sl, separators=(",",":")))
                    .replace("__AUDIO__",  json.dumps(au, separators=(",",":")))
                    .replace("__SESSION__", s)
                    .replace("__NUM__", str(NUM[s]))
                    .replace("__TITLE__", TITLES.get(s, s)))
        open(os.path.join(OUT, f"{s}.html"), "w", encoding="utf-8").write(page)

        lab = '<span class="lab">LAB</span>' if "lab" in s else ""
        rows.append(f'<a class="row" href="{s}.html"><span class="n">{NUM[s]}</span>'
                    f'<span class="t">{TITLES.get(s,s)}'
                    f'<small>{len(sl)} slides · {len(au)} audio</small></span>'
                    f'{lab}<span class="go">&rarr;</span></a>')
        print(f"{s:<12}{len(sl):>4} slides{len(au):>5} audio   {'OK' if len(au)==len(sl) else 'AUDIO MISSING'}")

    idx = (INDEX.replace("__ROWS__", "".join(rows))
                .replace("__SLIDES__", str(total_slides))
                .replace("__HOURS__", "7.8"))
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(idx)

    print(f"\nBuilt {len(rows)} lesson pages + index in ./{OUT}/")
    print(f"  {total_slides} slides · {total_audio} audio files matched")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    build(args or SESSIONS)
