# -*- coding: utf-8 -*-
"""
🖼️ ساخت «کارت قیمت روز» به صورت تصویر PNG (فارسی، راست‌به‌چپ).
از libraqm داخل Pillow استفاده می‌کند (شکل‌دهی و جهت‌دهی خودکار فارسی) — بدون نیاز به اینترنت.
اگر libraqm نبود، خودکار به حالت reshaper+bidi برمی‌گردد.
خروجی: engine/output/price_card.png
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont, features

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output"); os.makedirs(OUT, exist_ok=True)
FONT = os.path.join(HERE, "assets", "Vazirmatn-Bold.ttf")
W = 1080
BG, PANEL, PANEL2, ACCENT, TEXT, SUB, GOLD = (13, 17, 25), (22, 28, 40), (17, 23, 33), (126, 226, 168), (233, 238, 246), (139, 156, 181), (255, 212, 121)

HAS_RAQM = features.check("raqm")
if not HAS_RAQM:                       # فقط در صورت نبود raqm لازم است
    import arabic_reshaper
    from bidi.algorithm import get_display

def T(t):
    return str(t) if HAS_RAQM else get_display(arabic_reshaper.reshape(str(t)))

def RTL(d, xy, text, font, fill, anchor="ra", rtl=True):
    """رندر متن فارسی؛ اگر raqm هست، خودش شکل‌دهی و جهت را انجام می‌دهد."""
    kw = {"direction": "rtl", "language": "fa"} if (HAS_RAQM and rtl) else {}
    d.text(xy, T(text), font=font, fill=fill, anchor=anchor, **kw)

def LTR(d, xy, text, font, fill, anchor="la"):
    kw = {"direction": "ltr"} if HAS_RAQM else {}
    d.text(xy, T(text), font=font, fill=fill, anchor=anchor, **kw)

def num(x):
    if x is None: return "—"
    return f"{int(x):,}".replace(",", "٬").translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))

def money(x):
    x = float(x or 0)
    if x >= 1e9: return f"{num(round(x/1e9,1))} میلیارد"
    if x >= 1e6: return f"{num(round(x/1e6))} میلیون"
    if x >= 1e3: return f"{num(round(x/1e3))} هزار"
    return num(x)

def build(report_path=None, title="قیمت روز بازار", subtitle=None, n_intel=3, n_pairs=4,
          footer="منبع: رصد خودکار آگهی‌های عمومی • تحلیل: موتور تطبیق عرضه و تقاضا"):
    rp = report_path or os.path.join(OUT, "real_report.json")
    D = json.load(open(rp, encoding="utf-8"))
    intel, pairs, stats = D["intel"], D.get("pairs", []), D["stats"]

    # ارتفاع داینامیک — هیچ محتوایی بریده نمی‌شود
    H = 250 + 74 + n_intel*142 + 14 + 74 + n_pairs*178 + 150
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    f_title = ImageFont.truetype(FONT, 58)
    f_sub   = ImageFont.truetype(FONT, 28)
    f_h     = ImageFont.truetype(FONT, 38)
    f_name  = ImageFont.truetype(FONT, 36)
    f_price = ImageFont.truetype(FONT, 46)
    f_body  = ImageFont.truetype(FONT, 31)
    f_small = ImageFont.truetype(FONT, 25)
    f_tiny  = ImageFont.truetype(FONT, 22)

    # ---------- هدر ----------
    d.rectangle([0, 0, W, 210], fill=(15, 27, 43))
    d.rectangle([0, 208, W, 212], fill=ACCENT)
    RTL(d, (W-56, 44), title, f_title, TEXT)
    RTL(d, (W-56, 118), subtitle or f"به‌روزرسانی خودکار • {num(stats['unique'])} آگهی بررسی‌شده • {num(stats['pairs'])} فرصت شناسایی‌شده", f_sub, ACCENT)
    LTR(d, (56, 118), "● live", f_sub, ACCENT, anchor="la")

    y = 250
    # ---------- بخش ۱: تصویر بازار ----------
    RTL(d, (W-56, y), "۱) تصویر بازار", f_h, ACCENT); y += 74
    for v in list(intel.values())[:n_intel]:
        d.rounded_rectangle([56, y, W-56, y+120], radius=20, fill=PANEL)
        d.rectangle([W-64, y+16, W-58, y+104], fill=ACCENT)          # نوار سمت راست
        RTL(d, (W-86, y+18), v["fa"], f_name, TEXT)
        RTL(d, (W-86, y+68), f"{num(v['sellers'])} عرضه • {num(v['buyers'])} تقاضا", f_small, SUB)
        LTR(d, (100, y+22), num(v["median"]), f_price, ACCENT, anchor="la")
        RTL(d, (330, y+78), "تومان بر کیلو (میانه)", f_tiny, SUB, anchor="la")
        y += 142

    # ---------- بخش ۲: فرصت‌ها ----------
    y += 14
    RTL(d, (W-56, y), "۲) برترین فرصت‌های امروز", f_h, ACCENT); y += 74
    for p in pairs[:n_pairs]:
        d.rounded_rectangle([56, y, W-56, y+158], radius=20, fill=PANEL2, outline=(38, 52, 74), width=2)
        RTL(d, (W-86, y+16), p["need"][:46], f_body, TEXT)
        RTL(d, (W-86, y+62), f"خریدار: {num(p['buyer_price'])}   ←   فروشنده: {num(p['seller_price'])}", f_small, SUB)
        RTL(d, (W-86, y+104), p["vertical_fa"] + f"  •  {p['seller_city']}", f_tiny, SUB)
        # ستون فاصله قیمتی
        d.rounded_rectangle([70, y+22, 330, y+136], radius=16, fill=(24, 40, 32))
        RTL(d, (300, y+34), "فاصله قیمتی", f_tiny, SUB)
        LTR(d, (300, y+62), num(p["spread_per_kg"]), f_price, ACCENT, anchor="ra")
        RTL(d, (300, y+112), "تومان بر کیلو", f_tiny, SUB)
        y += 178

    # ---------- فوتر ----------
    d.rectangle([0, H-116, W, H], fill=(15, 27, 43))
    RTL(d, (W-56, H-86), footer, f_tiny, SUB)
    LTR(d, (56, H-86), "auto-generated", f_tiny, ACCENT, anchor="la")

    path = os.path.join(OUT, "price_card.png")
    img.save(path, "PNG", optimize=True)
    print("✔ کارت ساخته شد:", path, f"({os.path.getsize(path)//1024} KB)")
    return path

if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else None)
