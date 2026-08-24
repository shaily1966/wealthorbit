# WealthOrbit — Site Package

Everything built. Upload as-is.

---

## Structure

```
/                          index.html            Homepage
/about/                    about/index.html
/disclosures/              disclosures/index.html
/course/                   course/index.html     Sales page
/course/lessons.html                             Session list  ← GATE THIS
/course/day-01.html …                            19 lesson pages ← GATE THESE
/idea-intelligence/        idea-intelligence/index.html
/volatility/               volatility/index.html
/growth/                   growth/index.html
/markets/                  markets/index.html
/tools/                    build scripts — DO NOT UPLOAD
```

**Upload everything except `/tools/`.** Those are your build scripts, they stay on your machine.

---

## One thing to get right

Upload your `audio/` folder to the **site root**, not inside `/course/`:

```
wealthorbit.ca/
  audio/day-01/day-01_slide-1.mp3
  course/day-01.html
```

The lesson pages look for `../audio/…`. Wrong location and no audio plays.

---

## What to gate behind login

| Page | Access |
|---|---|
| `/course/index.html` | **Public** — it's the sales page |
| `/course/day-01.html` | **Public** — the free session |
| `/course/lessons.html` | **Paid** |
| `/course/day-02.html` … `day-17.html` | **Paid** |
| Everything else | Public |

---

## Before it goes live

- [ ] Set up `wealthorbit9@gmail.com` — it's referenced on every page
- [ ] Wire the **Get the course** button on `/course/` to payment
- [ ] Paste the TradingView ticker tape into `index.html` where the comment marks it
- [ ] Point the domain / upload to your host

---

## Two gates still open

**Idea Intelligence** — compliance opinion before it goes live.

**Session 17** — Canadian tax professional review before it reaches a paying student.
Everything else is unaffected.

---

## Keeping it updated

From your `wealthorbit-course` folder:

```
python build_lessons.py            # course pages, after any slide edit
python build_log.py                # Idea Intelligence, when an idea posts or closes
python fetch_iv.py && python build_iv.py     # volatility table, daily
python fetch_growth.py && python build_growth.py   # growth calculator, monthly
```

Then re-upload the changed page. Markets updates itself.

---

## Pricing as set

| | |
|---|---|
| Founding | **$197 CAD** |
| Standard | $397 |
| Plan | 3 × $79 |
| Included | 3 months Idea Intelligence |

Change these in `course/index.html` if you decide differently.
