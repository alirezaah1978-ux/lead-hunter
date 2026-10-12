# -*- coding: utf-8 -*-
"""ساخت لیست مشتری (سمت تقاضا) برای حوزه‌ی لوازم یدکی.
منبع: دیوار — آگهی‌های تعمیرگاه/یدکی‌فروشی/برق‌خودرو/صافکار + هر آگهی‌ای که شماره تماس دارد.
خروجی: output/customers_autoparts.csv
"""
import sys, os, re, csv, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sources.divar_relay import crawl

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

QUERIES = ["تعمیرگاه خودرو", "مکانیکی خودرو", "لوازم یدکی خودرو", "برق خودرو", "صافکاری و نقاشی"]
CITIES = ("tehran", "kerman", "isfahan", "mashhad")

SHOP = ["تعمیرگاه", "مکانیکی", "یدکی", "لوازم یدکی", "برق خودرو", "صافکار", "نقاشی خودرو",
        "پخش", "فروشگاه", "اتوسرویس", "سرویس خودرو", "جلوبند", "گیربکس"]
FA = "۰۱۲۳۴۵۶۷۸۹"

def to_en(t):
    for i, d in enumerate(FA): t = t.replace(d, str(i))
    t = t.replace("٠", "0").replace("١", "1").replace("٢", "2").replace("٣", "3").replace("٤", "4")
    t = t.replace("٥", "5").replace("٦", "6").replace("٧", "7").replace("٨", "8").replace("٩", "9")
    return t

PHONE = re.compile(r"(?<!\d)(0?9\d{2})[\s\-\.]?(\d{3})[\s\-\.]?(\d{4})(?!\d)|(?<!\d)(0\d{2})[\s\-\.]?(\d{4})[\s\-\.]?(\d{4})(?!\d)")

def phones(text):
    t = to_en(text)
    got = []
    for m in PHONE.finditer(t):
        g = [x for x in m.groups() if x]
        p = "".join(g)
        if len(p) == 10 and p.startswith("9"): p = "0" + p
        if 10 <= len(p) <= 11: got.append(p)
    return sorted(set(got))

rows = crawl(QUERIES, cities=CITIES, cache_ttl=24 * 3600)
print(f"\n🔎 آگهی‌های خدماتی پیدا‌شده: {len(rows)}")

leads, seen = [], set()
for r in rows:
    text = f"{r.get('title','')} {r.get('desc','')}"
    if not any(k in text for k in SHOP): continue
    ph = phones(text)
    key = (r.get("title", "")[:30], r.get("city", ""))
    if key in seen: continue
    seen.add(key)
    kind = "تعمیرگاه" if any(k in text for k in ["تعمیرگاه", "مکانیکی", "اتوسرویس", "صافکار"]) else "یدکی‌فروش/پخش"
    leads.append({
        "نوع": kind, "عنوان": (r.get("title") or "")[:60], "شهر": r.get("city", ""),
        "تلفن": "، ".join(ph), "قیمت_آگهی": r.get("price") or "", "لینک": r.get("url", ""),
    })

with_phone = [l for l in leads if l["تلفن"]]
path = os.path.join(OUT, "customers_autoparts.csv")
with open(path, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["نوع", "عنوان", "شهر", "تلفن", "قیمت_آگهی", "لینک"])
    w.writeheader(); w.writerows(leads)

print(f"📇 کاندید مشتری: {len(leads)} | از این تعداد با شماره تماس: {len(with_phone)}")
kinds = {}
for l in leads: kinds[l["نوع"]] = kinds.get(l["نوع"], 0) + 1
print("   ترکیب:", kinds)
print(f"💾 {path}")
for l in with_phone[:15]:
    print(f"   • [{l['نوع']}] {l['عنوان'][:45]} | {l['شهر']} | ☎ {l['تلفن']}")
