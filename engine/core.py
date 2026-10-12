# -*- coding: utf-8 -*-
"""هسته‌ی موتور: نرمال‌سازی متن، دسته‌بندی، حذف تکراری، امتیازدهی تطبیق و محاسبه‌ی پورسانت."""
import re, unicodedata, hashlib
from config import VERTICALS, RED_FLAGS, DEMAND_MARKERS, COST_PER_TOUCH

# ---------- ۱) نرمال‌سازی متن فارسی ----------
_FA_MAP = {"ي": "ی", "ك": "ک", "ۀ": "ه", "ة": "ه", "أ": "ا", "إ": "ا", "آ": "ا", "ؤ": "و"}
_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

def norm(t: str) -> str:
    if not t: return ""
    t = unicodedata.normalize("NFKC", str(t))
    t = t.replace("\u200c", " ").replace("\u200f", " ").replace("\u200e", " ")
    for a, b in _FA_MAP.items(): t = t.replace(a, b)
    t = t.translate(_DIGITS)
    t = re.sub(r"[^\w\s\.]", " ", t)
    return re.sub(r"\s+", " ", t).strip().lower()

def tokens(t: str):
    return {w for w in norm(t).split() if len(w) > 1}

def fa_num(n) -> str:
    """۱٬۲۳۴٬۵۶۷"""
    return f"{int(n):,}".replace(",", "٬").translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))

def human(n) -> str:
    n = float(n)
    if n >= 1e9:  return f"{fa_num(n/1e9*10/10)} میلیارد"
    if n >= 1e6:  return f"{fa_num(round(n/1e6,1)*10/10)} میلیون"
    if n >= 1e3:  return f"{fa_num(round(n/1e3))} هزار"
    return fa_num(n)

# ---------- ۱.۵) تشخیص «نوع کالا» و مشخصات سخت (Hard Constraints) ----------
SIZE_RE = re.compile(r"(?:سایز|ضخامت|میل|اینچ|شعاع)\s*(\d+(?:\.\d+)?)")

def product_type(text: str, vertical: str):
    """اولین کلمه‌ی نوع‌کالا در متن. مثلاً در حوزه فولاد: ورق / میلگرد / لوله."""
    t = norm(text)
    keys = VERTICALS.get(vertical, {}).get("ptypes") or VERTICALS.get(vertical, {}).get("keywords", [])
    for k in keys:
        if norm(k) in t: return norm(k)
    return None

def hard_specs(text: str):
    return set(SIZE_RE.findall(norm(text)))

# ---------- ۲) استخراج قیمت و مقدار از متن آگهی ----------
def extract_price_toman(text: str, qty=None):
    """قیمت واحد را از متن آزاد استخراج می‌کند. پشتیبانی از «۴۵ تومان»، «۴۵ میلیون»، «۴۵٬۰۰۰»."""
    t = norm(text)
    m = re.search(r"(\d+(?:\.\d+)?)\s*(میلیارد|میلیون|هزار)?\s*(?:تومان|تومن)", t)
    if not m: return None
    v = float(m.group(1)); u = m.group(2)
    mult = {"میلیارد": 1e9, "میلیون": 1e6, "هزار": 1e3, None: 1}[u]
    return v * mult

def extract_qty(text: str, unit="kg"):
    """مقدار را از متن استخراج می‌کند: «۲۰ تن» → 20000 کیلو."""
    t = norm(text)
    m = re.search(r"(\d+(?:\.\d+)?)\s*(تن|کیلو|کیلوگرم|کلیو|kg|ton)", t)
    if not m: return None
    v = float(m.group(1)); u = m.group(2)
    return v * 1000 if u in ("تن", "ton") else v

# ---------- ۲.۵) نرمال‌سازی قیمت واحد + تشخیص خرده‌فروشی/خدمات ----------
# بازه‌ی معقول قیمت هر کیلو (تومان) به تفکیک حوزه — برای تشخیص اشتباه واحد (کیلو/تن/کل بار)
PLAUSIBLE = {
# === AUTO-PARTS BLOCK START ===
 "autoparts": (30_000, 200_000_000),   # هر «عدد» قطعه یدکی
# === AUTO-PARTS BLOCK END ===

"pistachio": (400_000, 6_000_000), "steel": (25_000, 120_000), "scrap": (3_000, 200_000)}

RETAIL_MARKERS = ["فروشگاه", "خرده فروشی", "خدمات", "دستگاه", "تعمیر", "آموزش", "نصب",
                  "مشاوره", "طراحی", "قسط", "بسته بندی", "ارسال به سراسر", "پیج", "اینستا",
                  "خاموت", "میکسر", "کمپرسور", "کارواش"]

def normalize_price(price, text, vertical):
    """قیمت را به «تومان بر کیلو» تبدیل می‌کند یا نامعتبر اعلام می‌کند.
    برمی‌گرداند: (قیمت نرمال‌شده یا None، وضعیت)"""
    if not price: return None, "بی‌قیمت"
    lo, hi = PLAUSIBLE.get(vertical, (1_000, 10**8))
    t = norm(text)
    if lo <= price <= hi:
        return price, "معتبر (کیلویی)"
    # احتمالاً قیمت هر تن است
    if lo <= price / 1000 <= hi and ("تن" in t or "کامیون" in t or "بار" in t):
        return price / 1000, "نرمال‌شده از تن"
    if price < lo:
        return None, "مشکوک (خیلی کم — احتمالاً خرده/واحدی)"
    return None, "مشکوک (خیلی زیاد — احتمالاً کل بار یا تجهیزات)"

# ---------- ۳) دسته‌بندی حوزه کالایی ----------
def classify_vertical(text: str):
    best, score = None, 0
    for key, cfg in VERTICALS.items():
        s = sum(1 for k in cfg["keywords"] if norm(k) in norm(text))
        if s > score: best, score = key, s
    return best

# ---------- ۴) پاک‌سازی و حذف تکراری ----------
def fingerprint(l: dict) -> str:
    """اثر انگشت برای تشخیص آگهی تکراری (یک فروشنده، چند آگهی یکسان)."""
    base = f"{norm(l.get('title',''))[:40]}|{l.get('price')}|{norm(l.get('seller',''))}"
    return hashlib.md5(base.encode()).hexdigest()[:10]

def similar(a: dict, b: dict) -> bool:
    """تشابه معنایی: عنوان‌های بازنویسی‌شده با قیمت/مقدار یکسان = همان کالا."""
    if a.get("vertical") != b.get("vertical"): return False
    if a.get("price") and b.get("price"):
        if abs(a["price"] - b["price"]) / max(a["price"], b["price"]) > 0.02: return False
    else:
        return False
    if a.get("qty") and b.get("qty") and abs(a["qty"]-b["qty"])/max(a["qty"],b["qty"]) > 0.05: return False
    ta, tb = tokens(a.get("title","")), tokens(b.get("title",""))
    containment = len(ta & tb) / max(1, min(len(ta), len(tb)))
    return containment >= 0.7 or a["fingerprint"] == b["fingerprint"]

def clean_listing(l: dict) -> dict:
    l = dict(l)
    l["_text"] = f"{l.get('title','')} {l.get('desc','')}"
    l["vertical"] = l.get("vertical") or classify_vertical(l["_text"])
    if not l.get("price"):
        l["price"] = extract_price_toman(l["_text"])
    if not l.get("qty"):
        l["qty"] = extract_qty(l["_text"], VERTICALS.get(l["vertical"], {}).get("unit", "kg"))
    l["is_demand_post"] = any(k in norm(l.get("title","")) for k in DEMAND_MARKERS)
    l["red_flags"] = [f for f in RED_FLAGS if norm(f) in norm(l["_text"])]
    l["is_retail"] = any(m in norm(l["_text"]) for m in RETAIL_MARKERS)
    l["unit_price"], l["price_status"] = normalize_price(l.get("price"), l["_text"], l["vertical"])
    l["ptype"] = product_type(l["_text"], l["vertical"])
    l["specs"] = hard_specs(l["_text"])
    l["fingerprint"] = fingerprint(l)
    return l

def dedupe(listings):
    seen, out, dupes = [], [], 0
    for l in listings:
        twin = next((s for s in seen if similar(s, l)), None)
        if twin is not None:
            dupes += 1
            twin["duplicate_of"].append(l.get("id"))
            continue
        l["duplicate_of"] = []
        seen.append(l); out.append(l)
    return out, dupes

# ---------- ۵) موتور امتیازدهی تطبیق ----------
W = {"spec": 0.34, "price": 0.26, "qty": 0.16, "geo": 0.12, "fresh": 0.12}

def score_match(demand: dict, listing: dict) -> dict:
    """امتیاز ۰ تا ۱ با تفکیک اجزا — تا بتوانی به فروشنده توضیح بدهی چرا این لید ارزشمند است."""
    d_tok = tokens(demand["need"]) | {norm(k) for k in demand.get("keywords", [])}
    l_tok = tokens(listing["_text"])
    spec = len(d_tok & l_tok) / max(1, len(d_tok))

    price, notes = 0.0, []
    sp, bp = listing.get("price"), demand.get("max_price")
    if sp and bp:
        if sp <= bp:
            spread = (bp - sp) / bp
            price = 0.6 + 0.4 * min(1.0, spread / 0.10)   # زیر سقف خریدار = حداقل ۰.۶
            notes.append(f"{spread*100:.1f}٪ زیر سقف خریدار")
        else:
            price = max(0.0, 1 - (sp - bp) / bp * 6)  # هر ۱۶٪ گران‌تر → صفر
            notes.append(f"{((sp-bp)/bp)*100:.0f}٪ گران‌تر از سقف خریدار")
    elif sp is None:
        notes.append("قیمت نامشخص")

    qty = 0.0
    if listing.get("qty") and demand.get("qty"):
        ratio = listing["qty"] / demand["qty"]
        qty = 1.0 if ratio >= 1 else max(0.15, ratio)
        if ratio < 1: notes.append(f"فقط {ratio*100:.0f}٪ حجم لازم")

    geo = 1.0 if norm(listing.get("city","")) == norm(demand.get("city","")) else \
          0.6 if norm(listing.get("province","")) == norm(demand.get("province","")) else 0.3

    h = listing.get("age_hours", 24)
    fresh = max(0.0, 1 - h / 120)

    base = W["spec"]*spec + W["price"]*price + W["qty"]*qty + W["geo"]*geo + W["fresh"]*fresh

    penalty = 0.0
    if listing["is_demand_post"]: penalty += 0.45; notes.append("این آگهی خودش خریدار است")
    if listing.get("is_retail"):  penalty += 0.30; notes.append("خرده‌فروشی/خدمات — عمده نیست")
    if listing.get("price_status","").startswith("مشکوک"): penalty += 0.12; notes.append("قیمت مشکوک به اشتباه واحد")
    if listing["red_flags"]:       penalty += 0.22; notes.append("فروشنده «واسطه نمی‌خواهد»")
    if listing.get("price") is None: penalty += 0.05
    if not demand.get("verified"):   penalty += 0.06; notes.append("خریدار هنوز اعتبارسنجی نشده")

    # --- محدودیت‌های سخت: نوع کالا و سایز ---
    d_v = demand.get("vertical") or listing["vertical"]
    d_ptype = product_type(demand["need"], d_v)
    if d_ptype and listing.get("ptype") and d_ptype != listing["ptype"]:
        penalty += 0.20; notes.append(f"⛔ نوع کالا فرق دارد: خریدار «{d_ptype}» می‌خواهد، آگهی «{listing['ptype']}»")
    d_specs = hard_specs(demand["need"])
    if d_specs and listing.get("specs") and not (d_specs & listing["specs"]):
        penalty += 0.15; notes.append(f"⛔ سایز مطابق نیست: {sorted(d_specs)} در برابر {sorted(listing['specs'])}")

    total = max(0.0, min(1.0, base - penalty))
    return {"score": round(total, 3),
            "parts": {"spec": round(spec,2), "price": round(price,2), "qty": round(qty,2),
                      "geo": round(geo,2), "fresh": round(fresh,2), "penalty": round(penalty,2)},
            "notes": notes}

# ---------- ۶) اقتصاد فرصت ----------
def economics(demand, listing, m, close_prob_boost=0.0):
    cfg = VERTICALS.get(listing.get("vertical") or demand.get("vertical"), {})
    price = listing.get("price") or cfg.get("ticket_hint", 0)
    qty = min(listing.get("qty") or 0, demand.get("qty") or 0) or demand.get("qty") or 1
    deal_value = price * qty
    fee = max(deal_value * cfg.get("fee_rate", 0.01), cfg.get("min_fee", 0))
    # احتمال بستن معامله: تابعی از امتیاز تطبیق + اعتبار خریدار + سابقه فروشنده
    prob = min(0.55, 0.10 + 0.45 * m["score"] + (0.10 if demand.get("verified") else 0) + close_prob_boost)
    touches = 3 if m["score"] > 0.8 else 5
    cost = touches * COST_PER_TOUCH
    return {"deal_value": deal_value, "fee": fee, "fee_rate": cfg.get("fee_rate", 0.01),
            "lead_fee": cfg.get("lead_fee", 0), "close_prob": round(prob, 2),
            "cost": cost, "ev": fee * prob - cost}
