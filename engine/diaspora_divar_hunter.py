#!/usr/bin/env python3
"""
Diaspora Divar Hunter v1.2 (رادار شکار فرصت‌های دلاری/یورویی در «دیوارهای تلگرامی ایرانیان خارج از کشور»)
اسکن زنده ۱۰ کانال و دیوار تلگرامی ایرانیان در آلمان، انگلیس، کانادا، ترکیه، عمان و امارات
با ۵ فیلتر تخصصی + حذف خودکار پست‌های خبری و اولویت‌بندی تنوع کشوری
"""
import re
import json
import html
import urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

DIASPORA_CHANNELS = [
    {"handle": "Akfon_DE", "country": "🇩🇪 آلمان (سراسری)", "currency": "EUR (€)", "pages": 5},
    {"handle": "Hamburgdd", "country": "🇩🇪 آلمان (هامبورگ)", "currency": "EUR (€)", "pages": 2},
    {"handle": "DivarFarsiHamburg", "country": "🇩🇪 آلمان (هامبورگ ۲)", "currency": "EUR (€)", "pages": 2},
    {"handle": "DIWAR_ALMAN", "country": "🇩🇪 آلمان (دیوار)", "currency": "EUR (€)", "pages": 2},
    {"handle": "Berlinetelat2", "country": "🇩🇪 آلمان (برلین)", "currency": "EUR (€)", "pages": 2},
    {"handle": "Niaz4uk", "country": "🇬🇧 انگلیس (لندن)", "currency": "GBP (£)", "pages": 3},
    {"handle": "divar_estanbul", "country": "🇹🇷 ترکیه (استانبول)", "currency": "TRY / USD", "pages": 3},
    {"handle": "walcad", "country": "🇨🇦 کانادا (ونکوور)", "currency": "CAD ($)", "pages": 2},
    {"handle": "omanex", "country": "🇴🇲 عمان (مسقط)", "currency": "OMR (ریال عمان)", "pages": 2},
    {"handle": "iranian_uae", "country": "🇦🇪 امارات (دبی)", "currency": "AED (درهم)", "pages": 2},
]

NEWS_BLACKLIST = [
    "پلیس آلمان", "مظنون به برنامه", "ترامپ", "یورونیوز", "euronews",
    "دویچه‌وله", "خبرنگار", "حمله در غرب", "سقوط هواپیما", "dw_farsi", "🔶"
]

FILTERS = {
    "remote_digital_services": {
        "title": "💻 ۱. خدمات دیجیتال، طراحی، ادمینی، رزومه (Bewerbung) و آموزش آنلاین (۱۰۰٪ از ایران)",
        "keywords": [
            "موشن دیزاینر", "طراحی سایت", "گرافیک", "ادمین", "فروش بین‌الملل",
            "تدریس", "آموزش زبان", "آیلتس", "bewerbung", "ausbildung", "رزومه",
            "روانشناس", "مشاوره", "تراپی", "سئو", "تولید محتوا", "برنامه نویس",
            "gcse", "a-level", "فال قهوه", "تاروت"
        ]
    },
    "housing_makler_match": {
        "title": "🏠 ۲. مکلری (Makler) و تطبیق هوشمند مسکن/هم‌خانه با کمیسیون ۵۰۰ تا ۴,۰۰۰ یورو",
        "keywords": [
            "مکلر", "makler", "دنبال خونه", "نیازمند خانه", "اجاره گرم", "وارم میته", "کالت میته",
            "قابلیت ملد", "anmeldung", "هم اتاقی", "همخانه", "هم‌خانه", "اجاره داده میشود", "کاتسیون"
        ]
    },
    "luggage_trade_cargo": {
        "title": "✈️ ۳. تجارت چمدانی، خرید/فروش کیلو بار مسافر و ارسال کالا/مدارک (کیلویی ۱۰ تا ۱۵ یورو)",
        "keywords": [
            "بار مجاز", "قبول مدارک", "کیلو", "مسافر", "قبول دارو", "پرواز تهران", "مبدا :اصفهان",
            "سیگار وینستون", "زعفران", "فرش دستباف", "خشکبار", "صنایع دستی", "فریت بار"
        ]
    },
    "legal_admin_iran_assets": {
        "title": "⚖️ ۴. امور حقوقی، وکالت، ثبت شرکت، صرافی/حواله و کارهای اداری/ملکی داخل ایران",
        "keywords": [
            "وکیل", "وکالت", "ثبت شرکت", "اقامت", "وام شخصی", "سرمایه گذار",
            "شراکت", "مالیات", "حسابداری", "حواله", "صرافی", "نرخ تتر", "ریال عمان", "خرید و فروش پوند"
        ]
    },
    "b2b_diaspora_business": {
        "title": "🏪 ۵. کسب‌وکارهای ایرانی خارج (رستوران، کلینیک زیبایی، ساختمانی، کنسرت) نیازمند لید و تبلیغات",
        "keywords": [
            "رستوران", "آرایشگر", "کلینیک", "بوتاکس", "فیلر", "ساختمانی", "بازسازی",
            "مغازه", "فرصت شغلی", "نیازمندیم", "استخدام", "کنسرت", "بلیط کنسرت"
        ]
    }
}


def fetch_channel_posts(ch_info: dict) -> list[dict]:
    h = ch_info["handle"]
    before = None
    out = []
    for _ in range(ch_info.get("pages", 2)):
        url = f"https://t.me/s/{h}" + (f"?before={before}" if before else "")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            raw = urllib.request.urlopen(req, timeout=16).read().decode("utf-8", "ignore")
        except Exception:
            break
        chunks = re.split(r'<div class="tgme_widget_message_wrap[^>]*>', raw)[1:]
        ids = []
        for c in chunks:
            m = re.search(rf'data-post="{re.escape(h)}/(\d+)"', c, re.I)
            if not m:
                continue
            pid = int(m.group(1))
            ids.append(pid)
            tx = re.search(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>', c, re.S)
            if not tx:
                continue
            clean = html.unescape(re.sub(r"<[^>]+>", " ", tx.group(1))).strip()
            clean = re.sub(r"\s+", " ", clean)
            if len(clean) < 25:
                continue
            if any(nb in clean.lower() for nb in NEWS_BLACKLIST):
                continue
            contacts = re.findall(r'@[A-Za-z0-9_]{4,}|\+?\d[\d\s\-]{8,14}\d|[۰-۹]{10,12}', clean)
            contacts = [c.strip() for c in contacts if c.lower() != f"@{h.lower()}"]
            out.append({
                "channel": h,
                "country": ch_info["country"],
                "currency": ch_info["currency"],
                "id": pid,
                "text": clean,
                "contacts": list(dict.fromkeys(contacts))[:3],
                "url": f"https://t.me/{h}/{pid}"
            })
        if not ids:
            break
        before = min(ids)
    return out


def diversify_by_channel(ads: list[dict], limit: int = 8) -> list[dict]:
    """Ensure top samples show variety across different countries/channels first."""
    picked = []
    seen_ch = set()
    for ad in ads:
        if ad["channel"] not in seen_ch:
            picked.append(ad)
            seen_ch.add(ad["channel"])
            if len(picked) >= limit:
                return picked
    for ad in ads:
        if ad not in picked:
            picked.append(ad)
            if len(picked) >= limit:
                break
    return picked


def scan_diaspora_opportunities() -> dict:
    all_ads_raw = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        for res in ex.map(fetch_channel_posts, DIASPORA_CHANNELS):
            all_ads_raw.extend(res)

    seen = set()
    all_ads = []
    for ad in all_ads_raw:
        sig = re.sub(r"\W+", "", ad["text"][:80]).lower()
        if sig in seen:
            continue
        seen.add(sig)
        all_ads.append(ad)

    categorized = {k: [] for k in FILTERS}
    for ad in all_ads:
        t_low = ad["text"].lower()
        for f_key, f_info in FILTERS.items():
            if any(kw.lower() in t_low for kw in f_info["keywords"]):
                categorized[f_key].append(ad)

    return {
        "total_ads_scanned": len(all_ads),
        "channels_scanned": len(DIASPORA_CHANNELS),
        "categories": {
            k: {
                "title": FILTERS[k]["title"],
                "count": len(v),
                "samples": diversify_by_channel(v, 8)
            }
            for k, v in categorized.items()
        }
    }


if __name__ == "__main__":
    rep = scan_diaspora_opportunities()
    print(f"Total Unique Diaspora Ads Scanned: {rep['total_ads_scanned']} across {rep['channels_scanned']} channels\n")
    for k, info in rep["categories"].items():
        print(f"=== {info['title']} ({info['count']} آگهی یکتا) ===")
        for s in info["samples"][:6]:
            print(f"  • [{s['country']} | @{s['channel']}/{s['id']}] {s['text'][:155]}... | تماس: {s['contacts']}")
        print()
