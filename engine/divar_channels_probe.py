# -*- coding: utf-8 -*-
"""اسکن کانال‌های فارسی «دیوار» در تلگرام (ایران + ایرانیان خارج).
خروجی: output/divar_channels.csv + خلاصه‌ی حوزه‌ها
"""
import sys, os, re, csv, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sources.telegram_public import crawl

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

# (handle, نام, منطقه)
CANDIDATES = [
    # --- ایران ---
    ("NiazmandihaDivareTehran", "دیوار تهران (نیازمندی‌ها)", "ایران"),
    ("agahy_mashhad", "دیوار مشهد و حومه", "ایران"),
    ("divar_man97", "دیوار (من)", "ایران"),
    ("divarmashhad_ir", "دیوار مشهد", "ایران"),
    ("divar_tehran", "دیوار تهران", "ایران"),
    ("divartehran", "دیوار تهران ۲", "ایران"),
    ("divar_isfahan", "دیوار اصفهان", "ایران"),
    ("divar_shiraz", "دیوار شیراز", "ایران"),
    ("divar_tabriz", "دیوار تبریز", "ایران"),
    ("divar_kerman", "دیوار کرمان", "ایران"),
    ("divar_karaj", "دیوار کرج", "ایران"),
    # --- آلمان ---
    ("divaralmani", "دیوار آلمان", "آلمان"),
    ("divarrhamburg", "دیوار هامبورگ", "آلمان"),
    ("divarberlina", "دیوار برلین", "آلمان"),
    ("divarfrankfurt", "دیوار فرانکفورت", "آلمان"),
    ("divar_koln_dusseldorf", "دیوار کلن/دوسلدورف", "آلمان"),
    ("divarfarsihamburg", "دیوار فارسی هامبورگ", "آلمان"),
    ("Iranian_In_Deutschland", "ایرانیان آلمان", "آلمان"),
    # --- هلند / اروپا ---
    ("hollandad", "نیازمندی‌های فارسی‌زبانان هلند", "هلند"),
    ("agahiHoland", "آگهی هلند", "هلند"),
    # --- ترکیه / خاورمیانه ---
    ("divar_estanbul", "دیوار و کاریابی استانبول", "ترکیه"),
    # --- کانادا / آمریکا ---
    ("walcad", "دیوار ایرانیان ونکوور", "کانادا"),
    ("America_Canada", "آمریکا کانادا", "کانادا/آمریکا"),
]

CATS = {
    "خوراکی/صادرات ایرانی": ["پسته", "زعفران", "نبات", "خرما", "تخمه", "آجیل", "ادویه", "لواشک", "ترشی", "حلوا", "زرشک", "دوغ", "ماست", "خامه"],
    "خودرو": ["خودرو", "ماشین", "پژو", "پراید", "سمند", "بی ام و", "بنز", "تویوتا", "خودرو دست دوم", "پلاک"],
    "املاک": ["آپارتمان", "خانه", "اجاره", "ملک", "سوئیت", "اتاق", "خرید خانه", "رهن"],
    "لوازم خانگی/مبلمان": ["یخچال", "لباسشویی", "مبل", "فرش", "تلویزیون", "ماشین ظرفشویی", "کاناپه", "تخت", "میز"],
    "موبایل/لپ‌تاپ": ["موبایل", "آیفون", "لپ تاپ", "لپ‌تاپ", "گوشی", "تبلت", "کامپیوتر"],
    "لوازم یدکی": ["لوازم یدکی", "قطعات", "لنت", "فیلتر", "گیربکس", "موتور خودرو", "تعمیرگاه"],
    "کارگو/ارسال بار": ["کارگو", "ارسال بار", "باربری", "حمل بار", "مرسوله", "پست", "ارسال به ایران", "ارسال به اروپا", "محموله"],
    "ارز/انتقال پول": ["یورو", "دلار", "انتقال پول", "صرافی", "تتر", "حواله", "ارز"],
    "کار/استخدام": ["استخدام", "کاریابی", "جویای کار", "نیرو"],
    "خدمات": ["تعمیر", "نظافت", "آرایش", "راننده", "نقاشی", "ساختمان", "لوله"],
    "ابزار/ماشین‌آلات": ["ابزار", "دستگاه", "ماشین آلات", "ماشین‌آلات", "صنعتی", "کمپرسور"],
}
BUY = ["خریدار", "میخرم", "می‌خرم", "متقاضی", "نیاز به خرید", "نیاز دارم", "جستجو می‌کنم", "دنبال"]

FA = "۰۱۲۳۴۵۶۷۸۹"
def to_en(t):
    for i, d in enumerate(FA): t = t.replace(d, str(i))
    return t

PHONE = re.compile(r"(?<!\d)(?:\+?49|0\d{2,4}|0?9\d{2})[\s\-\./]?\d{3,4}[\s\-\.]?\d{3,4}(?!\d)")

rows_out = []
for handle, label, region in CANDIDATES:
    try:
        posts = crawl(channels=[(handle, label)], pages=2)
    except Exception as e:
        print(f"  ⛔ {handle}: {type(e).__name__}")
        continue
    if not posts:
        print(f"  ⚪ {handle:26s} | بی‌پست/غیرعمومی")
        continue
    text = "\n".join((p.get("text") or "") + " " + (p.get("title") or "") for p in posts)
    cats = {c: sum(1 for k in ks if k in text) for c, ks in CATS.items()}
    cats = {c: n for c, n in cats.items() if n >= 2}
    phones = set()
    for p in posts:
        for ph in (p.get("phones") or []): phones.add(ph)
        for m in PHONE.finditer(to_en(p.get("text") or "")): phones.add(m.group(0).strip())
    buy = sum(1 for p in posts if any(b in (p.get("text") or "") for b in BUY))
    top = sorted(cats.items(), key=lambda x: -x[1])[:5]
    rows_out.append({
        "handle": handle, "نام": label, "منطقه": region, "پست": len(posts),
        "خریدار": buy, "شماره": len(phones),
        "حوزه‌ها": " · ".join(f"{c}({n})" for c, n in top),
        "نمونه": (posts[0].get("text") or "")[:110].replace("\n", " "),
        "لینک": f"https://t.me/s/{handle}",
    })
    print(f"  ✅ {handle:26s} | {len(posts):3d} پست | خریدار {buy:2d} | ☎ {len(phones):3d} | {rows_out[-1]['حوزه‌ها'][:70]}")

p = os.path.join(OUT, "divar_channels.csv")
with open(p, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["نام", "منطقه", "handle", "پست", "خریدار", "شماره", "حوزه‌ها", "نمونه", "لینک"])
    w.writeheader(); w.writerows(rows_out)
json.dump(rows_out, open(os.path.join(OUT, "divar_channels.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\n💾 {p}  ({len(rows_out)} کانال)")
tot = collections.Counter()
for r in rows_out:
    for part in r["حوزه‌ها"].split(" · "):
        c = part.split("(")[0]
        tot[c] += int(part.split("(")[1].rstrip(")")) if "(" in part else 1
print("\n🏆 جمع سیگنال حوزه‌ها در همه‌ی کانال‌ها:")
for c, n in tot.most_common():
    print(f"   {c:24s} {n}")
