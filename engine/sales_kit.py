# -*- coding: utf-8 -*-
"""🎁 کیت فروش «کارخانه محتوا»: پکیج‌شیت تصویری + نمونه‌کارت مشتری
خروجی: output/packages_sheet.png و output/sample_client_card.png
"""
import os
from PIL import Image, ImageDraw, ImageFont, features

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output"); os.makedirs(OUT, exist_ok=True)
FONT = os.path.join(HERE, "assets", "Vazirmatn-Bold.ttf")
BG, PANEL, PANEL2, ACCENT, TEXT, SUB, GOLD = (13, 17, 25), (22, 28, 40), (17, 23, 33), (126, 226, 168), (233, 238, 246), (139, 156, 181), (255, 212, 121)
HAS_RAQM = features.check("raqm")

def RTL(d, xy, text, font, fill, anchor="ra"):
    kw = {"direction": "rtl", "language": "fa"} if HAS_RAQM else {}
    d.text(xy, str(text), font=font, fill=fill, anchor=anchor, **kw)

def num(x):
    return f"{int(x):,}".replace(",", "٬").translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))

def F(size): return ImageFont.truetype(FONT, size)

# ═══════════════ ۱) پکیج‌شیت ═══════════════
def packages_sheet():
    W, H = 1080, 2170
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
    f_t, f_s = F(60), F(30); f_h, f_b, f_x = F(40), F(30), F(26)

    d.rectangle([0, 0, W, 240], fill=(15, 27, 43)); d.rectangle([0, 238, W, 243], fill=ACCENT)
    RTL(d, (W-56, 50), "کارخانه محتوای رهیاب", f_t, TEXT)
    RTL(d, (W-56, 135), "کانال و محتوای کسب‌وکارت را ما می‌سازیم و تغذیه می‌کنیم — ماهانه", f_s, ACCENT)

    y = 300
    RTL(d, (W-56, y), "▍دو پکیج، یک انتخاب", f_h, GOLD); y += 80

    pkg = [
        ("🟢 پکیج پایه", "۳ تا ۵ میلیون تومان / ماه", ACCENT, [
            "۲۰ پست گرافیکی اختصاصی",
            "۳۰ استوری آماده‌ی انتشار",
            "۴ کارت محصول / قیمت",
            "تقویم محتوایی ۳۰ روزه",
            "کپشن و هشتگ حرفه‌ای",
            "لوگو + بنر + کاور هایلایت (یک‌بار)",
            "چیدمان کامل کانال تلگرام",
            "انتشار خودکار با ربات",
        ]),
        ("🔵 پکیج حرفه‌ای", "۸ تا ۱۵ میلیون تومان / ماه", GOLD, [
            "همه‌ی اقلام پکیج پایه، به‌علاوه:",
            "۳۰ پست + ۶۰ استوری + ۸ کارت",
            "ربات کاتالوگ / سفارش / پاسخ خودکار",
            "۴ فایل صوتی گویندگی برای ویدیوها",
            "گزارش ماهانه‌ی عددی + پیشنهاد",
            "گزارش قیمت رقبا از موتور رهیاب",
            "بازطراحی فصلی هویت بصری",
        ]),
    ]
    for title, price, col, items in pkg:
        bh = 120 + len(items) * 62
        d.rounded_rectangle([48, y, W-48, y+bh], 22, fill=PANEL, outline=col, width=3)
        RTL(d, (W-84, y+34), title, f_h, col)
        RTL(d, (84, y+44), price, f_b, TEXT, anchor="la")
        yy = y + 118
        for it in items:
            RTL(d, (W-84, yy), "•  " + it, f_x, TEXT)
            yy += 62
        y += bh + 34

    RTL(d, (W-56, y), "▍خدمات افزودنی (قابل اضافه به هر پکیج)", f_h, GOLD); y += 76
    extras = [
        ("تبلیغ‌نویسی کمپین", "۱ تا ۳ میلیون"), ("ویدیوی فروش با گویندگی", "۱.۵ تا ۴ میلیون"),
        ("اسکریپت متقاعدسازی فروش", "۱ تا ۲ میلیون"), ("پلی‌بوک مشتری ناراضی + ربات", "۲ تا ۵ میلیون"),
        ("گزارش ماهانه‌ی قیمت رقبا", "۲ تا ۵ میلیون / ماه"), ("لیست سرنخ هدفمند صنف", "۱ تا ۴ میلیون"),
        ("ربات فروش اختصاصی", "۵ تا ۱۸ میلیون"), ("برندینگ بسته و برچسب", "۲ تا ۶ میلیون"),
    ]
    for name, price in extras:
        d.rounded_rectangle([48, y, W-48, y+86], 14, fill=PANEL2)
        RTL(d, (W-84, y+24), name, f_b, TEXT)
        RTL(d, (300, y+26), price, f_x, ACCENT, anchor="la")
        y += 98

    y += 10
    RTL(d, (W-56, y), "▍چرا ما؟", f_h, GOLD); y += 80
    for line in ["⚡ تحویل بسته‌ی اول زیر ۲۴ ساعت", "🎯 همه‌چیز خودکار — بدون کار روزانه برای تو",
                 "📊 گزارش عددی ماهانه (بازدید، محتوای برتر، فروش)", "🧪 نمونه‌کار زنده: کانال «نبض بازار عمده»"]:
        RTL(d, (W-84, y), line, f_b, TEXT); y += 64

    y += 20
    d.rounded_rectangle([48, y, W-48, y+170], 22, fill=(20, 40, 30), outline=ACCENT, width=3)
    RTL(d, (W-84, y+36), "شروع کار فقط با یک پیام:", f_h, ACCENT)
    RTL(d, (W-84, y+104), "یک کارت قیمت اختصاصی برای کسب‌وکارت، رایگان آماده می‌کنیم.", f_b, TEXT)

    img.save(os.path.join(OUT, "packages_sheet.png"))
    print("✅ packages_sheet.png", img.size)

# ═══════════════ ۲) نمونه‌کارت مشتری ═══════════════
def sample_client_card():
    W, H = 1080, 1350
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
    f_t, f_s, f_r, f_p, f_x = F(56), F(30), F(34), F(42), F(26)

    d.rectangle([0, 0, W, 250], fill=(30, 22, 12)); d.rectangle([0, 248, W, 253], fill=GOLD)
    RTL(d, (W-56, 52), "نمونه‌ی کارت مشتری", f_s, GOLD)
    RTL(d, (W-56, 110), "پخش یدکی آرین‌پارت", f_t, TEXT)
    RTL(d, (W-56, 190), "قیمت روز • به‌روزرسانی خودکار", f_x, SUB)

    rows = [("سرسیلندر پژو ۲۰۶", "۴٬۸۵۰٬۰۰۰"), ("دیسک ترمز جلو سمند", "۱٬۲۹۰٬۰۰۰"),
            ("رینگ موتور ۴۰۵ اورجینال", "۲٬۶۵۰٬۰۰۰"), ("چراغ جلو پارس", "۳٬۴۰۰٬۰۰۰"),
            ("واترپمپ ۲۰۶ تیپ ۲", "۹۸۰٬۰۰۰")]
    y = 320
    for name, price in rows:
        d.rounded_rectangle([48, y, W-48, y+130], 18, fill=PANEL)
        RTL(d, (W-84, y+34), name, f_r, TEXT)
        RTL(d, (84, y+40), price, f_p, ACCENT, anchor="la")
        RTL(d, (84, y+88), "تومان", f_x, SUB, anchor="la")
        y += 148

    d.rounded_rectangle([48, y+10, W-48, y+150], 18, fill=(20, 40, 30), outline=ACCENT, width=2)
    RTL(d, (W-84, y+44), "🎁 پیشنهاد این هفته: ۱۰٪ تخفیف روی خرید عمده", f_r, ACCENT)
    RTL(d, (W-84, y+100), "تماس: ۰۹۱۲-۰۰۰-۰۰۰۰  •  ارسال به سراسر کشور", f_x, TEXT)

    RTL(d, (W-56, H-92), "کارت واقعی مشتری، در همین سبک و با اقلام و قیمت‌های خودت ساخته می‌شود.", F(24), SUB)
    RTL(d, (W-56, H-54), "هر پست کنار همین کارت منتشر می‌شود — تولید و انتشار: کارخانه محتوای رهیاب", F(24), SUB)

    img.save(os.path.join(OUT, "sample_client_card.png"))
    print("✅ sample_client_card.png", img.size)

if __name__ == "__main__":
    packages_sheet()
    sample_client_card()
