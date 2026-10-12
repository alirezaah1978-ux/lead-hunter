# -*- coding: utf-8 -*-
"""سیستم شهر به شهر: هر شهر «عرضه‌ی» چه جنسی است و کجاش «تقاضا»؟
روی داده‌ی زنده‌ی دیوار، ۴ حوزه × ۱۲ شهر.
خروجی: output/city_balance.json + output/city_balance.csv + چاپ ماتریس
"""
import sys, os, json, csv, statistics, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sources.divar_relay import crawl, CITIES
from core import clean_listing, norm

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

CITIES.update({"yazd": "یزد", "arak": "اراک", "sari": "ساری", "qazvin": "قزوین",
               "urmia": "ارومیه", "bandarabbas": "بندرعباس"})

CITY_LIST = ("tehran", "karaj", "isfahan", "mashhad", "tabriz", "shiraz",
             "qom", "kerman", "rasht", "arak", "yazd", "ahvaz")

# برای هر حوزه: کوئری عرضه + کوئری تقاضا
PLAN = {
    "pistachio": ("پسته عمده", "خرید پسته"),
    "steel":     ("میلگرد عمده", "خرید میلگرد"),
    "scrap":     ("آهن قراضه", "خرید ضایعات"),
    "autoparts": ("لوازم یدکی پژو عمده", "خرید لوازم یدکی"),
}
QUERIES = [q for pair in PLAN.values() for q in pair]

BUY_WORDS = ["خریدار", "میخرم", "می‌خرم", "متقاضی", "نیاز به", "خریداری", "خرید"]

def is_demand(title, desc="", kind_query=False):
    t = norm(title)
    return any(norm(w) in t for w in BUY_WORDS)

rows = crawl(QUERIES, cities=CITY_LIST, cache_ttl=12 * 3600)
print(f"\n🔎 کل آگهی‌های دریافتی: {len(rows)}")
json.dump(rows, open(f"{OUT}/city_balance_raw.json", "w", encoding="utf-8"), ensure_ascii=False)

# ساخت بانک اطلاعات
data = collections.defaultdict(lambda: {"supply": 0, "demand": 0, "prices": [], "vpts": collections.Counter()})
for r in rows:
    l = clean_listing(dict(r))
    v = l.get("vertical")
    if not v: continue
    c = r.get("city") or "?"
    d = is_demand(l.get("title", ""), l.get("desc", "")) or l.get("is_demand_post")
    cell = data[(c, v)]
    cell["demand" if d else "supply"] += 1
    if l.get("ptype"): cell["vpts"][l["ptype"]] += 1
    if l.get("unit_price"): cell["prices"].append(l["unit_price"])

# جدول‌ها
cities = sorted({c for (c, v) in data}, key=lambda c: -sum(data[(c, v)]["supply"] + data[(c, v)]["demand"] for v in PLAN))
report = {}
for city in cities:
    report[city] = {}
    for v in PLAN:
        cell = data[(city, v)]
        sup, dem = cell["supply"], cell["demand"]
        med = int(statistics.median(cell["prices"])) if cell["prices"] else None
        report[city][v] = {
            "عرضه": sup, "تقاضا": dem,
            "توازن": round(dem / sup, 2) if sup else None,     # >۱ یعنی شهر خریدار است
            "میانه_قیمت": med, "تعداد_قیمت‌دار": len(cell["prices"]),
            "اقلام": cell["vpts"].most_common(3),
        }

with open(f"{OUT}/city_balance.json", "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)

# CSV تخت
with open(f"{OUT}/city_balance.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["شهر", "حوزه", "عرضه", "تقاضا", "نسبت تقاضا/عرضه", "میانه قیمت (تومان)"])
    for city in cities:
        for v in PLAN:
            x = report[city][v]
            w.writerow([CITIES.get(city, city), v, x["عرضه"], x["تقاضا"], x["توازن"], x["میانه_قیمت"] or ""])

# چاپ ماتریس
for v in PLAN:
    print(f"\n===== {v} =====")
    print(f"{'شهر':12s} {'عرضه':>5s} {'تقاضا':>6s} {'تقاضا/عرضه':>10s} {'میانه قیمت':>14s}")
    for city in cities:
        x = report[city][v]
        b = x["توازن"] if x["توازن"] is not None else "-"
        m = f"{x['میانه_قیمت']:,}" if x["میانه_قیمت"] else "—"
        print(f"{CITIES.get(city,city):12s} {x['عرضه']:5d} {x['تقاضا']:6d} {str(b):>10s} {m:>14s}")

# مسیرهای پیشنهادی: ارزان‌ترین شهر عرضه → گران‌ترین شهر
print("\n===== 🚚 مسیرهای پیشنهادی (بخر اینجا، بفروش آنجا) =====")
routes = []
for v in PLAN:
    priced = [(c, report[c][v]["میانه_قیمت"]) for c in cities if report[c][v]["میانه_قیمت"]]
    if len(priced) < 2: continue
    priced.sort(key=lambda x: x[1])
    lo_c, lo_p = priced[0]
    hi_c, hi_p = priced[-1]
    spread = round((hi_p - lo_p) / lo_p * 100, 1)
    if spread < 5: continue
    routes.append({"حوزه": v, "بخر از": CITIES.get(lo_c, lo_c), "قیمت مبدأ": lo_p,
                   "بفروش در": CITIES.get(hi_c, hi_c), "قیمت مقصد": hi_p, "فاصله ٪": spread})
    print(f"  {v:11s}: {CITIES.get(lo_c,lo_c)} ({lo_p:,}) → {CITIES.get(hi_c,hi_c)} ({hi_p:,})  ≈ {spread}% فاصله")
json.dump(routes, open(f"{OUT}/city_routes.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n💾 city_balance.json / city_balance.csv / city_routes.json")
