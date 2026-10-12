# -*- coding: utf-8 -*-
"""
📣 کالکتور تلگرام (کانال‌های عمومی) — بدون لاگین، بدون API، بدون اکانت.
از «پیش‌نمایش عمومی کانال» (`t.me/s/<channel>`) می‌خواند؛ همان چیزی که هر مرورگر عادی می‌بیند.

ارزش ویژه‌ی این منبع: در کانال‌های عمده‌فروشی، فروشنده/خریدار معمولاً **شماره تماس مستقیم**
می‌گذارد → یعنی می‌توانی بدون واسطه‌ی چت دیوار با او حرف بزنی.

نصب: نیازی به چیز خاصی نیست (bs4 اختیاری است؛ پارسر داخلی کار می‌کند)
اجرا:
    python3 sources/telegram_public.py --channels ezayeat MadanBazar
    python3 sources/telegram_public.py --channels all --pages 3 --json out.json

⚠️ ادب و قانون: این فقط خواندن پست‌های عمومی است، با فاصله‌ی محترمانه و کش.
   کانال‌های «گروه» (که پیش‌نمایش ندارند) از این مسیر قابل خواندن نیستند و به اکانت نیاز دارند.
"""
import json, os, re, time, html, hashlib, urllib.request, argparse, unicodedata
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "_cache"); os.makedirs(CACHE, exist_ok=True)
MIN_INTERVAL = 3.0
_last = [0.0]

# ── کانال‌های پیشنهادی (قابل اضافه‌کردن با --channels) ──────────────────────────
CHANNELS = {
    # ضایعات و بازیافت
    "ezayeat":        "ضایعات و قراضه",
    "zayeatesf":      "ضایعات اصفهان",
    # فلزات و مواد معدنی
    "MadanBazar":     "بازار معدن و مواد معدنی",
    # فولاد و آهن
    "fouladban":      "فولادبان — اخبار فولاد",
    # --- کانال‌های «دیوار» فارسی (تست‌شده ۱۴۰۵/۰۷/۲۰) ---
    "divar_com":          "نیازمندی‌های دیوار (ملی)",
    "divarmarivanian":    "دیوار مریوان (فروشنده پرشماره)",
    "agahy_mashhad":      "دیوار مشهد و حومه",
    "NiazmandihaDivareTehran": "دیوار تهران (املاک/خدمات)",
    # --- ایرانیان خارج از کشور ---
    "hollandad":          "نیازمندی‌های فارسی‌زبانان هلند",
    "walcad":             "دیوار ایرانیان ونکوور",
    "America_Canada":     "آمریکا کانادا (تقاضا-محور)",
    "iranihaistanbul2":   "خانه ایرانیان استانبول",
    # --- عمده‌فروشی زنده (تست‌شده ۱۴۰۵/۰۷/۲۰ — همه همین هفته پست دارند) ---
    "salehabad":          "عمده‌فروشی بازار صالح‌آباد (۹۹K)",
    "maloosak96":         "باس عمده قشم/درگهان — ملوسک",
    "poshakmarofi":       "پخش عمده پوشاک معروفی — بانه",
    "hana_omde":          "واردات و پخش عمده بچگانه هانا — بانه",
    "arayeshi_rahimpoor": "پخش عمده آرایشی رحیم‌پور — بانه",
    "azizi1960":          "پخش عمده بچگانه کانیابانه — بانه",
    "lapland2":           "لپ‌تاپ استوک لپ‌لند — بانه (۷۱K)",
}
FA = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36"

def _throttle():
    dt = time.time() - _last[0]
    if dt < MIN_INTERVAL: time.sleep(MIN_INTERVAL - dt)
    _last[0] = time.time()

def _get(url, ttl=900):
    cp = os.path.join(CACHE, hashlib.md5(url.encode()).hexdigest() + ".html")
    if ttl > 0 and os.path.exists(cp) and time.time() - os.path.getmtime(cp) < ttl:
        return open(cp, encoding="utf-8").read()
    _throttle()
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "fa,en;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            body = r.read().decode("utf-8", "replace")
        if ttl >= 0: open(cp, "w", encoding="utf-8").write(body)
        return body
    except Exception as e:
        print(f"    ⛔ {url} → {type(e).__name__}: {e}")
        return ""

def _text(frag):
    frag = re.sub(r"<br\s*/?>", "\n", frag)
    frag = re.sub(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', r"\2 (\1)", frag, flags=re.S)
    frag = re.sub(r"<[^>]+>", "", frag)
    return html.unescape(frag).strip()

def clean(t):
    t = unicodedata.normalize("NFKC", t or "").replace("\u200c", " ").replace("\u200f", " ").replace("\u200e", " ")
    return re.sub(r"[ \t]+", " ", t).strip()

# ── استخراج فیلدها ───────────────────────────────────────────────────────────
PHONE = re.compile(r"(?:\+98|0)?9\d{2}[\s\-\.]?\d{3}[\s\-\.]?\d{4}")
LANDLINE = re.compile(r"0\d{2,3}[\s\-]?\d{7,8}")
# قیمت با واحد صریح: «۱۲ میلیون تومان»
PRICE_PAT = re.compile(r"(\d[\d,٬\.]{2,})\s*(میلیارد|میلیون|هزار|تومان|تومن)")
# قیمت خام جداکننده‌دار: «2,000,000» یا «44,000» (فرمت رایج لیست‌های قیمت تلگرام)
BARE_PRICE = re.compile(r"(?<![\d])(\d{1,3}(?:[,٬]\d{3})+)(?![\d])")
# سطر لیست قیمت: «#مس_کابلی_قرمز 2,000,000🔶» یا «آهن سنگین 43,500»
PRICE_LINE = re.compile(r"^\s*(?P<name>[^\d\n]{2,45}?)\s*[:：]?\s*(?P<val>\d{1,3}(?:[,٬]\d{3})+)(?P<mark>[🔶➕➖↑↓]*)\s*$", re.M)

def phones(t):
    out = []
    for m in PHONE.finditer(t or ""):
        p = re.sub(r"\D", "", m.group())
        p = "0" + p[2:] if p.startswith("98") else p
        if len(p) == 11 and p not in out: out.append(p)
    return out

def prices(t):
    """همه‌ی اعداد قیمتی متن را برمی‌گرداند: [(مقدار تومان, متن اصلی)]"""
    out = []
    for m in PRICE_PAT.finditer((t or "").translate(FA)):
        raw = m.group(1).replace(",", "").replace("٬", "")
        try: v = float(raw)
        except ValueError: continue
        unit = m.group(2)
        if "تومان" in unit or "تومن" in unit: out.append(int(v))
        elif unit == "میلیارد": out.append(int(v * 1e9))
        elif unit == "میلیون":  out.append(int(v * 1e6))
        elif unit == "هزار":    out.append(int(v * 1e3))
    return out

def bare_prices(t):
    """همه‌ی اعداد قیمتی (با جداکننده هزارگان) — برای لیست‌های قیمت بدون واحد."""
    out = []
    for m in BARE_PRICE.finditer((t or "").translate(FA)):
        try:
            v = int(m.group(1).replace(",", "").replace("٬", ""))
            if 100 <= v <= 10**10: out.append(v)
        except ValueError: pass
    return out

GREET = {"با سلام", "سلام", "درود", "بسم الله", "قیمت", "قیمت خرید", "قیمت فروش", "قیمت روز"}
def smart_title(text):
    """اولین سطر معنادار (نه سلام و نه فقط ایموجی/هشتگ خالی)."""
    for ln in (text or "").split("\n"):
        ln = clean(ln).strip(" -•|")
        if len(ln) < 6: continue
        if ln in GREET: continue
        if re.fullmatch(r"[\W_]+", ln): continue
        if re.match(r"^https?://", ln): continue
        if "t.me/" in ln and len(ln) < 40: continue
        words = [w for w in re.split(r"\s+", ln) if len(w) > 1]
        if len(words) >= 2 or "#" in ln:
            return re.sub(r"\s*\(\?q=[^)]+\)", "", ln)[:120]
    return clean(text)[:100]

def is_pricelist(text):
    """لیست قیمت روز: چند سطر «نام + عدد» و اشاره به کیلو/قیمت"""
    items = PRICE_LINE.findall(text or "")
    marks = ("قیمت" in (text or "")) or ("کیلو" in (text or "")) or ("به ازای" in (text or ""))
    return len(items) >= 4 and marks

def price_items(text):
    """استخراج جدول قیمت: [{name, price, mark}]"""
    out, seen = [], set()
    for m in PRICE_LINE.finditer(text or ""):
        name = clean(m.group("name")).strip(" #-•:").replace("_", " ")
        try: val = int(m.group("val").replace(",", "").replace("٬", ""))
        except ValueError: continue
        if not name or name in GREET or len(name) < 3 or name in seen: continue
        if val < 500: continue
        seen.add(name)
        out.append({"name": name[:45], "price": val, "mark": m.group("mark")})
    return out[:40]

def bulk_signals(t):
    t = clean(t)
    keys = ["تن", "تناژ", "عمده", "بارگیری", "کامیون", "خریدار", "فروشنده", "موجود",
            "قرارداد", "صادرات", "کیلو", "خرید", "فروش", "مزایده", "درجه"]
    return [k for k in keys if k in t][:6]

def direction(t):
    t = clean(t)
    buy = sum(t.count(k) for k in ["خریدار", "خرید", "نیاز به", "متقاضی", "می‌خرم", "میخرم"])
    sell = sum(t.count(k) for k in ["فروش", "موجود", "عرضه", "بارگیری", "آماده تحویل"])
    return "تقاضا" if buy > sell else "عرضه"

# ── پارسر صفحه ───────────────────────────────────────────────────────────────
MSG_RE = re.compile(
    r'data-post="(?P<chan>[^/"]+)/(?P<mid>\d+)"(?P<body>.*?)(?=data-post="|\Z)', re.S)
TEXT_RE = re.compile(r'class="tgme_widget_message_text[^"]*"[^>]*>(?P<txt>.*?)</div>', re.S)
TIME_RE = re.compile(r'<time datetime="([^"]+)"')
VIEW_RE = re.compile(r'tgme_widget_message_views">([^<]+)<')

def parse_page(html_text, channel_fa=""):
    out = []
    for m in MSG_RE.finditer(html_text):
        body = m.group("body")
        tm = TEXT_RE.search(body)
        if not tm: continue
        text = clean(_text(tm.group("txt")))
        if len(text) < 25: continue                      # پیام تبلیغاتی خیلی کوتاه = بی‌ارزش
        tmatch = TIME_RE.search(body)
        when = tmatch.group(1) if tmatch else ""
        try:
            dt = datetime.fromisoformat(when)
            age_h = max(0, int((datetime.now(timezone.utc) - dt).total_seconds() // 3600))
        except Exception:
            dt, age_h = None, None
        out.append({
            "id": f"tg-{m.group('chan')}-{m.group('mid')}",
            "source": "تلگرام",
            "channel": m.group("chan"),
            "channel_fa": channel_fa,
            "title": smart_title(text),
            "desc": text,
            "text": text,
            "price": (prices(text) or bare_prices(text) or [None])[0],
            "price_list": price_items(text) if is_pricelist(text) else [],
            "kind": ("pricelist" if is_pricelist(text) else
                     "listing" if (phones(text) or len(text) > 60) else "short"),
            "age_hours": age_h if age_h is not None else 24,
            "posted_at": dt.isoformat() if dt else "",
            "phones": phones(text),
            "direction": direction(text),
            "signals": bulk_signals(text),
            "views": (VIEW_RE.search(body).group(1) if VIEW_RE.search(body) else ""),
            "url": f"https://t.me/{m.group('chan')}/{m.group('mid')}",
            "city": "",
        })
    return out

def fetch_channel(channel, channel_fa="", pages=2, ttl=900):
    rows = []
    url = f"https://t.me/s/{channel}"
    for i in range(pages):
        body = _get(url, ttl=ttl)
        if not body: break
        got = parse_page(body, channel_fa)
        rows += got
        # صفحه‌بندی: قبل از قدیمی‌ترین پست موجود
        ids = [int(x["id"].split("-")[-1]) for x in got] if got else []
        if not ids: break
        url = f"https://t.me/s/{channel}?before={min(ids)}"
        print(f"    ↳ {channel} صفحه {i+1}: {len(got)} پست")
    return rows

def crawl(channels=None, pages=2):
    chans = channels or list(CHANNELS.items())
    rows = []
    for ch in chans:
        if isinstance(ch, tuple): name, fa = ch
        else: name, fa = ch, ""
        print(f"  📣 تلگرام | {name} ({fa})")
        rows += fetch_channel(name, fa, pages=pages)
    return rows

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--channels", nargs="+", default=None)
    ap.add_argument("--pages", type=int, default=2)
    ap.add_argument("--json", default="")
    ap.add_argument("--ttl", type=int, default=900)
    a = ap.parse_args()
    chans = [(c, CHANNELS.get(c, "")) for c in a.channels] if a.channels else None
    rows = crawl(chans, a.pages)
    print(f"\n✔ مجموع {len(rows)} پست")
    for r in rows[:6]:
        print(f"   • [{r['direction']}] {r['title'][:52]}")
        print(f"     قیمت: {r['price']} | 📞 {r['phones'][:2] or '—'} | {r['age_hours']}h | {r['url']}")
    if a.json:
        json.dump(rows, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("✔ ذخیره شد:", a.json)
