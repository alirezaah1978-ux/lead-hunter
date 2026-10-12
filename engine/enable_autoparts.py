# -*- coding: utf-8 -*-
"""فعال/غیرفعال کردن حوزه‌ی «لوازم یدکی خودروهای ایرانی» در موتور.
  python3 enable_autoparts.py            → فعال‌سازی
  python3 enable_autoparts.py --disable  → برگشت کامل به حالت قبل
هر بلوک بین دو نشان‌گر قرار می‌گیرد و بکاپ خودکار گرفته می‌شود.
"""
import os, sys, shutil, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
A = "# === AUTO-PARTS BLOCK START ==="
B = "# === AUTO-PARTS BLOCK END ==="

CONFIG_BLOCK = f'''{A}
    "autoparts": {{
        "fa": "لوازم یدکی خودروهای ایرانی",
        "unit": "عدد",
        "fee_rate": 0.020,          # ۲٪ — بازار واسطه‌محور، ارزش هر قلم متوسط
        "min_fee": 1_000_000,       # کف پورسانت این حوزه (سبدها کوچک‌ترند)
        "lead_fee": 700_000,
        "assumed_qty": 100,         # فرض محافظه‌کارانه: ۱۰۰ عدد در هر معامله
        "keywords": ["لنت", "فیلتر روغن", "فیلتر هوا", "تسمه تایم", "دیسک و صفحه", "کلاچ",
                     "شمع", "وایر", "دینام", "استارت", "رادیاتور", "گیربکس", "سرسیلندر",
                     "کمک فنر", "گلگیر", "کاپوت", "سپر", "چراغ خودرو", "پژو", "پراید",
                     "سمند", "تیبا", "کوییک", "ساینا", "دنا", "رانا", "پارس", "شاهین",
                     "تارا", "آریسان", "یدکی"],
        "ptypes": ["لنت ترمز", "فیلتر روغن", "فیلتر هوا", "تسمه تایم", "دیسک و صفحه", "شمع و وایر",
                   "دینام و استارت", "رادیاتور و کولر", "گیربکس", "موتور و سرسیلندر",
                   "بدنه و چراغ", "کمک فنر و جلوبندی"],
        "b2b_queries": ["لنت ترمز عمده", "فیلتر روغن عمده", "لوازم یدکی پژو عمده",
                        "لوازم یدکی پراید عمده", "خرید لوازم یدکی", "قطعات موتور پژو"],
        "ticket_hint": 800_000,
    }},
{B}'''

BANDS_BLOCK = f'''{A}
 "autoparts": {{"لنت ترمز": (150_000, 4_500_000), "فیلتر روغن": (40_000, 500_000), "فیلتر هوا": (50_000, 600_000),
               "تسمه تایم": (150_000, 6_000_000), "دیسک و صفحه": (300_000, 12_000_000), "شمع و وایر": (30_000, 1_500_000),
               "دینام و استارت": (1_500_000, 25_000_000), "رادیاتور و کولر": (1_500_000, 30_000_000),
               "گیربکس": (5_000_000, 120_000_000), "موتور و سرسیلندر": (3_000_000, 200_000_000),
               "بدنه و چراغ": (200_000, 45_000_000), "کمک فنر و جلوبندی": (150_000, 8_000_000)}},
{B}'''

CORE_BLOCK = f'''{A}
 "autoparts": (30_000, 200_000_000),   # هر «عدد» قطعه یدکی
{B}'''

TARGETS = [
    ("config.py",        "VERTICALS = {",   CONFIG_BLOCK),
    ("real_pipeline.py", "PTYPE_BANDS = {", BANDS_BLOCK),
    ("core.py",          "PLAUSIBLE = {",   CORE_BLOCK),
]

def backup(path):
    b = path + ".bak-" + datetime.datetime.now().strftime("%m%d-%H%M")
    if not os.path.exists(b):
        shutil.copy2(path, b)

def add(path, anchor, block):
    s = open(path, encoding="utf-8").read()
    if A in s: return "قبلاً فعال بود"
    if anchor not in s: raise SystemExit(f"⛔ لنگر پیدا نشد در {path}")
    s = s.replace(anchor, anchor + "\n" + block + "\n", 1)   # خط جدید بعد از بلوک = بقیه‌ی دیکشنری سالم می‌ماند
    backup(path); open(path, "w", encoding="utf-8").write(s)
    return "✅ اضافه شد"

def remove(path):
    s = open(path, encoding="utf-8").read()
    if A not in s: return "—"
    out, skip = [], False
    for line in s.split("\n"):
        if A in line: skip = True; continue
        if B in line: skip = False; continue
        if not skip: out.append(line)
    backup(path); open(path, "w", encoding="utf-8").write("\n".join(out))
    return "↩️ حذف شد"

if __name__ == "__main__":
    for f, anchor, block in TARGETS:
        p = os.path.join(HERE, f)
        print(f"{f:18s} → {remove(p) if '--disable' in sys.argv else add(p, anchor, block)}")
    import ast, importlib
    for f, _, _ in TARGETS:
        ast.parse(open(os.path.join(HERE, f), encoding="utf-8").read())
    sys.path.insert(0, HERE)
    import config, core                      # توجه: real_pipeline را import نکن — در لحظه‌ی import کل کروال را اجرا می‌کند
    has_bands = "autoparts" in open(os.path.join(HERE, "real_pipeline.py"), encoding="utf-8").read()
    ok = "autoparts" in config.VERTICALS and "autoparts" in core.PLAUSIBLE and has_bands
    print("🧪 تست:", "✅ سالم" if ok else "⛔ ناقص", "| پورسانت:", config.VERTICALS.get("autoparts", {}).get("fee_rate"))
