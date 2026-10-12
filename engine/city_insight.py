# -*- coding: utf-8 -*-
"""تحلیل تمیز شهر به شهر از داده‌ی ذخیره‌شده (بدون کروال مجدد).
۱) تشخیص درست آگهی خریدار (بدون اشتباه «خرید و فروش» = دلال)
۲) مقایسه‌ی قیمت شهرها فقط برای «همان قلم» (سیب با سیب) و با حداقل ۳ نمونه
۳) نقش هر شهر: منبع تأمین / بازار فروش / متوازن
خروجی: output/city_insight.json + چاپ گزارش
"""
import sys, os, json, statistics, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import clean_listing, norm

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
rows = json.load(open(f"{OUT}/city_balance_raw.json", encoding="utf-8"))
print(f"📦 آگهی‌های خوانده‌شده: {len(rows)}")

HARD_BUY = ["خریدار", "میخرم", "می‌خرم", "متقاضی", "نیاز به خرید", "خریداری", "نیاز دارم", "جمع میکنم"]
TRADER = ["خرید و فروش", "خریدوفروش", "خرید فروش", "خرید و فروش"]

def classify(title):
    t = norm(title)
    if any(w in t for w in HARD_BUY): return "demand"
    if t.startswith("خرید") and not any(w in t for w in TRADER): return "demand"
    return "supply"

data = collections.defaultdict(lambda: {"supply": 0, "demand": 0, "trader": 0,
                                        "prices": collections.defaultdict(list)})
for r in rows:
    l = clean_listing(dict(r))
    v = l.get("vertical")
    if not v: continue
    c = r.get("city") or "?"
    t = norm(l.get("title", ""))
    if any(w in t for w in TRADER): k = "trader"
    else: k = classify(l.get("title", ""))
    cell = data[(c, v)]
    cell[k] += 1
    if l.get("unit_price") and l.get("ptype"):
        cell["prices"][l["ptype"]].append(l["unit_price"])

cities = sorted({c for (c, v) in data}, key=lambda c: -sum(data[(c, v)][k] for v in
       ("pistachio","steel","scrap","autoparts") for k in ("supply","demand")))

out = {}
for v in ("pistachio", "steel", "scrap", "autoparts"):
    out[v] = {}
    for c in cities:
        cell = data[(c, v)]
        s, d = cell["supply"], cell["demand"]
        role = "متوازن"
        if s + d == 0: role = "—"
        elif d >= max(3, 2 * s): role = "🔴 بازار فروش (تقاضا)"
        elif s >= max(3, 2 * d): role = "🟢 منبع تأمین (عرضه)"
        pts = {p: sorted(x) for p, x in cell["prices"].items() if len(x) >= 3}
        out[v][c] = {"عرضه": s, "تقاضا": d, "دلال": cell["trader"], "نقش": role,
                     "قیمت هر قلم": {p: int(statistics.median(x)) for p, x in pts.items()},
                     "نمونه": {p: len(x) for p, x in pts.items()}}

json.dump(out, open(f"{OUT}/city_insight.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

FA = {"tehran":"تهران","karaj":"کرج","isfahan":"اصفهان","mashhad":"مشهد","tabriz":"تبریز",
      "shiraz":"شیراز","qom":"قم","kerman":"کرمان","rasht":"رشت","arak":"اراک","yazd":"یزد","ahvaz":"اهواز"}
for v in ("scrap", "steel", "pistachio", "autoparts"):
    print(f"\n{'='*62}\n{v}\n{'='*62}")
    print(f"{'شهر':10s} {'عرضه':>5s} {'تقاضا':>6s} {'دلال':>5s}  نقش")
    for c in cities:
        x = out[v][c]
        if x["عرضه"] + x["تقاضا"] + x["دلال"] == 0: continue
        print(f"{FA.get(c,c):10s} {x['عرضه']:5d} {x['تقاضا']:6d} {x['دلال']:5d}  {x['نقش']}")
    # مقایسه‌ی همان قلم بین شهرها
    pairs = collections.defaultdict(dict)
    for c in cities:
        for p, price in out[v][c]["قیمت هر قلم"].items():
            pairs[p][c] = price
    print("  ── همان قلم در چند شهر (حداقل ۳ نمونه) ──")
    for p, cd in sorted(pairs.items(), key=lambda x: -len(x[1])):
        if len(cd) < 2: continue
        s = sorted(cd.items(), key=lambda x: x[1])
        lo, hi = s[0], s[-1]
        sp = round((hi[1] - lo[1]) / lo[1] * 100, 1)
        print(f"   {p:18s} {FA.get(lo[0],lo[0])} {lo[1]:,}  →  {FA.get(hi[0],hi[0])} {hi[1]:,}   ≈{sp}%")
print("\n💾 output/city_insight.json")
