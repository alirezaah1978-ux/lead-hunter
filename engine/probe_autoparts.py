# -*- coding: utf-8 -*-
"""سنجش زنده‌ی بازار لوازم یدکی خودروهای ایرانی روی دیوار.
هدف: ببینیم واقعاً چند آگهی عمده، چند خریدار، و چه فاصله‌ی قیمتی وجود دارد.
"""
import sys, os, json, statistics, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sources.divar_relay import crawl
from core import norm

QUERIES = [
    "لوازم یدکی پژو عمده", "لنت ترمز عمده", "فیلتر روغن عمده",
    "لوازم یدکی پراید عمده", "قطعات موتور پژو", "خرید لوازم یدکی",
]
CITIES = ("tehran", "isfahan", "mashhad")

rows = crawl(QUERIES, cities=CITIES, cache_ttl=6 * 3600)
print(f"\n🔎 کل آگهی‌های خام: {len(rows)}")

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
raw = json.dumps(rows, ensure_ascii=False)
json.dump(rows, open(f"{OUT}/autoparts_raw.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

BUY = ["خریدار", "خرید", "میخرم", "می‌خرم", "متقاضی", "نیاز به", "خریداری"]
PART = {
    "لنت ترمز": ["لنت"], "فیلتر روغن": ["فیلتر روغن", "فیلترروغن"], "فیلتر هوا": ["فیلتر هوا"],
    "تسمه تایم": ["تسمه تایم", "تسمه"], "دیسک و صفحه": ["دیسک", "صفحه کلاچ", "کلاچ"],
    "شمع/وایر": ["شمع", "وایر"], "دینام/استارت": ["دینام", "استارت"], "ECU/کامپیوتر": ["ecu", "کامپیوتر"],
    "رادیاتور/کولر": ["رادیاتور", "کولر", "کمپرسور"], "گیربکس": ["گیربکس"], "موتور": ["موتور"],
    "چراغ": ["چراغ", "لامپ"], "بدنه (گلگیر/کاپوت/سپر/در)": ["گلگیر", "کاپوت", "سپر", "درب", "در "],
}
CARS = ["پژو", "پراید", "سمند", "تیبا", "کوییک", "ساینا", "دنا", "رانا", "پارس", "شاهین", "تارا", "۴۰۵", "405", "206", "۲۰۶", "207", "آریسان", "پیکان"]

def hit(text, words):
    t = norm(text)
    return any(norm(w).strip() in t for w in words)

demand, supply, both = 0, 0, 0
by_city = collections.Counter()
by_car = collections.Counter()
buckets = collections.defaultdict(list)
for r in rows:
    text = f"{r.get('title','')} {r.get('desc','')}"
    if r.get("city"): by_city[r["city"]] += 1
    for c in CARS:
        if norm(c) in norm(text): by_car[c] += 1
    isbuy = hit(r.get("title", ""), BUY) or any(m in norm(text) for m in ["خریدار", "متقاضی خرید", "نیاز به خرید"])
    if isbuy: demand += 1
    else: supply += 1
    for label, words in PART.items():
        if hit(text, words): buckets[label].append(r)

print(f"\n📊 عرضه (فروشنده): {supply} | تقاضا (خریدار): {demand}")
print(f"🏙 شهرها: " + " ، ".join(f"{c}={n}" for c, n in by_city.most_common()))
print(f"🚗 پرتکرارترین خودروها: " + " ، ".join(f"{c}={n}" for c, n in by_car.most_common(8)))

print(f"\n🔧 تفکیک قطعات (تعداد آگهی | با قیمت | کمینه | میانه | بیشینه — تومان):")
report = {}
for label, items in sorted(buckets.items(), key=lambda x: -len(x[1])):
    prices = sorted(i["price"] for i in items if i.get("price") and 50_000 <= i["price"] <= 2_000_000_000)
    if not prices:
        print(f"  {label:28s} {len(items):4d} | 0 آگهی قیمت‌دار")
        continue
    med = statistics.median(prices)
    report[label] = {"n": len(items), "priced": len(prices), "min": prices[0], "med": med, "max": prices[-1]}
    fa = lambda v: f"{int(v):,}"
    print(f"  {label:28s} {len(items):4d} | {len(prices):4d} | {fa(prices[0])} | {fa(med)} | {fa(prices[-1])}")

print("\n🧾 نمونه‌های قیمت‌دار (برای اعتبارسنجی چشمی):")
shown = 0
for label, items in buckets.items():
    for i in items:
        if i.get("price") and 50_000 <= i["price"] <= 2_000_000_000:
            print(f"  [{label}] {i['title'][:70]} | {int(i['price']):,} | {i.get('city','')} | ن/{i.get('age_hours','?')}ساعته")
            shown += 1
            break
    if shown >= 10: break

json.dump(report, open(f"{OUT}/autoparts_report.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\n💾 خروجی: output/autoparts_report.json + output/autoparts_raw.json")
