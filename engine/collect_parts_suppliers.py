# -*- coding: utf-8 -*-
"""ساخت دفترچه‌ی تأمین‌کننده‌های لوازم یدکی از کانال‌های عمومی تلگرام.
چرا تلگرام؟ چون دیوار شماره تماس را مخفی می‌کند (در تست: از ۲۳۹ آگهی، صفر شماره)،
ولی کانال‌های پخش یدکی شماره و قیمت را علنی می‌گذارند.
خروجی: output/parts_suppliers.csv + output/parts_prices.csv
"""
import sys, os, re, csv, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sources.telegram_public import crawl

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

CHANNELS = [
    ("Iranianautopartssuppliers", "کانون صنفی فروشندگان و تولیدکنندگان قطعات خودرو"),
    ("yadakwin", "یدک وین — پخش عمده لوازم یدکی"),
    ("pridyadak", "پراید یدک — فروش عمده"),
    ("importkhodroyadak", "واردات لوازم یدکی نو و استوک"),
    ("ariayadak", "آریا یدک — پخش ایران‌خودرو/سایپا"),
    ("fidarpakhsh", "فیدار پخش"),
    ("pishroyadak1399", "پیشرو یدک — پخش عمده طرح‌ویو"),
    ("pakhshyadak", "پخش یدک"),
    ("partshop_ir", "پارت‌شاپ"),
    ("yadak_market", "یدک مارکت"),
]

AREA = {"021": "تهران", "041": "تبریز", "031": "اصفهان", "051": "مشهد", "034": "کرمان",
        "026": "کرج", "025": "قم", "071": "شیراز", "013": "رشت", "011": "ساری", "081": "همدان"}
FA = "۰۱۲۳۴۵۶۷۸۹"

def to_en(t):
    for i, d in enumerate(FA): t = t.replace(d, str(i))
    return t

GREETS = ["با سلام", "سلام", "عرض ادب", "باسلام", "خدمت همکاران", "احترام", "درود", "همکاران عزیز", "روز بخیر"]
CITY_WORDS = {"تبریز": "تبریز", "تهران": "تهران", "اصفهان": "اصفهان", "مشهد": "مشهد", "کرمان": "کرمان",
              "قم": "قم", "کرج": "کرج", "شیراز": "شیراز", "رشت": "رشت", "اراک": "اراک", "یزد": "یزد",
              "اهواز": "اهواز", "همدان": "همدان", "زنجان": "زنجان", "قزوین": "قزوین", "البرز": "کرج"}

def city_of(phones):
    for p in phones:
        for code, city in AREA.items():
            if p.startswith(code): return city
    return ""

rows = crawl(channels=CHANNELS, pages=8)
import json
json.dump(rows, open(os.path.join(OUT, "parts_channels_raw.json"), "w", encoding="utf-8"), ensure_ascii=False)
print(f"\n📥 پست‌های دریافتی: {len(rows)}")

suppliers, prices = {}, []
for r in rows:
    text = (r.get("text") or "").strip()
    ph = tuple(r.get("phones") or [])
    if not ph: continue
    city = city_of(ph)
    if not city and any(p.startswith("09") for p in ph): city = "نامعلوم (موبایل)"
    key = ph
    if not city or "نامعلوم" in city:
        for c in CITY_WORDS:
            if c in text: city = CITY_WORDS[c]; break
    if key not in suppliers:
        # نام فروشگاه: اولین خط تمیز و غیرتعارفی
        name = ""
        for line in text.split("\n"):
            clean_line = re.sub(r"[*_~|#✅💥🔴👉🏻]", " ", line).strip(" -:،.")
            if len(clean_line) < 4: continue
            if any(g in clean_line for g in GREETS): continue
            if len(clean_line) > 55: clean_line = clean_line[:55] + "…"
            name = clean_line; break
        name = name or r.get("channel", "") + " — " + ph[0][-4:]
        suppliers[key] = {"نام/کانال": name, "شهر": city, "تلفن": "، ".join(ph),
                          "کانال": r.get("channel", ""), "لینک": r.get("url", "")}
    for it in (r.get("price_list") or []):
        prices.append({"قلم": str(it.get("name"))[:60], "قیمت": it.get("price"),
                       "شهر": city, "فروشنده": suppliers[key]["نام/کانال"][:30]})

sup_path = os.path.join(OUT, "parts_suppliers.csv")
with open(sup_path, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["نام/کانال", "شهر", "تلفن", "کانال", "لینک"])
    w.writeheader(); w.writerows(suppliers.values())

pr_path = os.path.join(OUT, "parts_prices.csv")
with open(pr_path, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["قلم", "قیمت", "شهر", "فروشنده"])
    w.writeheader(); w.writerows(prices)

print(f"🏪 تأمین‌کننده با شماره تماس: {len(suppliers)}")
bysity = collections.Counter(s["شهر"] for s in suppliers.values())
print("   شهرها:", dict(bysity))
print(f"💰 ردیف قیمت استخراج‌شده: {len(prices)}")
print(f"💾 {sup_path}\n💾 {pr_path}")
print("\n📋 نمونه تأمین‌کننده‌ها:")
for s in list(suppliers.values())[:12]:
    print(f"   • {s['نام/کانال'][:42]:44s} | {s['شهر']:16s} | ☎ {s['تلفن']}")
