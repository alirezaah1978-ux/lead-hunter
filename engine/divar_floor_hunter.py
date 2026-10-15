#!/usr/bin/env python3
"""
Divar Floor-Price Hunter (شکارچی کف قیمت زنده دیوار در هر شهر — مدل محمد امین حیدری پست #543 و #1620)
- دریافت زنده آگهی‌های دیوار در هر شهر ایران (از طریق پروکسی خوانای r.jina.ai روی divar.ir/s/{city})
- جداسازی هوشمند آگهی‌های واقعی فروش کالا از آگهی‌های خدمات/تعمیر/قیمت فیک
- محاسبه: کف قیمت واقعی، میانه بازار، سقف قیمت، و «قیمت تله‌گذاری پیشنهادی امین حیدری»
- پشتیبانی از تک‌شهر (۳۸ شهر ایران) و حالت «چندشهره / مقایسه شهرها»
"""
import re
import json
import statistics
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

CITY_SLUGS = {
    "تهران": "tehran",
    "مشهد": "mashhad",
    "اصفهان": "isfahan",
    "شیراز": "shiraz",
    "تبریز": "tabriz",
    "کرج": "karaj",
    "اهواز": "ahvaz",
    "قم": "qom",
    "کرمانشاه": "kermanshah",
    "رشت": "rasht",
    "یزد": "yazd",
    "ارومیه": "urmia",
    "کرمان": "kerman",
    "همدان": "hamedan",
    "اراک": "arak",
    "زاهدان": "zahedan",
    "بندرعباس": "bandar-abbas",
    "قزوین": "qazvin",
    "گرگان": "gorgan",
    "ساری": "sari",
    "بابل": "babol",
    "آمل": "amol",
    "اردبیل": "ardabil",
    "زنجان": "zanjan",
    "سنندج": "sanandaj",
    "خرم‌آباد": "khorramabad",
    "خرم آباد": "khorramabad",
    "بوشهر": "bushehr",
    "کاشان": "kashan",
    "نیشابور": "neyshabur",
    "سبزوار": "sabzevar",
    "دزفول": "dezful",
    "آبادان": "abadan",
    "بروجرد": "borujerd",
    "اسلامشهر": "eslamshahr",
    "شهریار": "shahriar",
    "قدس": "qods-city",
    "ملارد": "malard",
    "پاکدشت": "pakdasht",
    "ورامین": "varamin",
    "ری": "rey",
}

SERVICE_NOISE_WORDS = [
    "تعمیر", "تعمیرگاه", "لنت کوبی", "تراشکاری", "اجرت", "نصب رایگان در محل",
    "مکانیکی", "میکانیکی", "جلوبندی سازی", "صافکاری", "نقاشی", "کارواش"
]


def resolve_city(city_name: str) -> tuple[str, str]:
    c = (city_name or "").strip()
    if not c:
        return "تهران", "tehran"
    if c in CITY_SLUGS:
        return c, CITY_SLUGS[c]
    for k, v in CITY_SLUGS.items():
        if k in c or c in k or c.lower() == v:
            return k, v
    return "تهران", "tehran"


def fetch_city_ads(query: str, city_fa: str = "تهران", timeout: int = 18) -> list[dict]:
    city_label, slug = resolve_city(city_fa)
    q_enc = urllib.parse.quote(query.strip())
    url = f"https://r.jina.ai/https://divar.ir/s/{slug}?q={q_enc}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        md = urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore")
    except Exception:
        return []

    ads = []
    for m in re.finditer(r'## \[(.*?)\]\((https://divar\.ir/v/[^\)]+)\)', md):
        raw = m.group(1)
        link = m.group(2)
        clean = re.sub(r'!\[Image[^\]]*\]\([^\)]+\)', '', raw).strip()
        clean = re.sub(r'\s+', ' ', clean)
        pm = re.search(r'([\d۰-۹,٬]+)\s*تومان', clean)
        if not pm:
            continue
        price_val = int(re.sub(r'[^\d]', '', pm.group(1).translate(PERSIAN_DIGITS)) or 0)
        # حذف قیمت‌های فیک مثل ۱۰۰۰، ۱۱۱۱۱ یا زیر ۵۰ هزار تومان
        if price_val < 50000 or str(price_val) in ("111111", "1111111", "123456", "1234567"):
            continue
        title = clean[:pm.start()].strip()
        meta = clean[pm.end():].strip()
        is_service = any(w in title for w in SERVICE_NOISE_WORDS)
        is_shop = "فروشگاه" in meta
        is_promoted = ("نردبان" in meta) or ("پله" in meta)
        ads.append({
            "city": city_label,
            "city_slug": slug,
            "title": title,
            "price": price_val,
            "meta": meta,
            "url": link,
            "is_service": is_service,
            "is_shop": is_shop,
            "is_promoted": is_promoted,
        })

    ads.sort(key=lambda x: x["price"])
    return ads


def analyze_floor_price(query: str, city_fa: str = "تهران", multi_city: bool = False) -> dict:
    if multi_city or city_fa.strip() in ("همه", "کل ایران", "ایران", "چند شهر"):
        target_cities = ["تهران", "مشهد", "اصفهان", "شیراز"]
    else:
        target_cities = [resolve_city(city_fa)[0]]

    all_ads = []
    if len(target_cities) == 1:
        all_ads = fetch_city_ads(query, target_cities[0], timeout=20)
    else:
        with ThreadPoolExecutor(max_workers=4) as ex:
            futures = [ex.submit(fetch_city_ads, query, c, 18) for c in target_cities]
            for f in futures:
                try:
                    all_ads.extend(f.result())
                except Exception:
                    pass

    # جداسازی آگهی‌های فروش قطعه/کالا از آگهی‌های دستمزد/تعمیرگاه
    product_ads = [a for a in all_ads if not a["is_service"]]
    service_ads = [a for a in all_ads if a["is_service"]]
    working_pool = product_ads if len(product_ads) >= 2 else all_ads

    # حذف پرت‌های آماری خیلی پایین (مثلاً قیمت یک پیچ یا واشر وقتی دنبال کل قطعه هستیم)
    if len(working_pool) >= 5:
        raw_median = statistics.median([x["price"] for x in working_pool])
        filtered_pool = [x for x in working_pool if x["price"] >= raw_median * 0.28]
        if len(filtered_pool) >= 2:
            working_pool = filtered_pool

    working_pool.sort(key=lambda x: x["price"])

    if not working_pool:
        return {
            "ok": False,
            "query": query,
            "cities": target_cities,
            "error": "هیچ آگهی قیمت‌داری در دیوار برای این عبارت پیدا نشد."
        }

    prices = [x["price"] for x in working_pool]
    floor_ad = working_pool[0]
    floor_price = floor_ad["price"]
    median_price = int(statistics.median(prices))
    avg_price = int(statistics.mean(prices))
    ceiling_price = working_pool[-1]["price"]

    # فرمول تله‌گذاری امین حیدری (پست #1537 و #1620):
    # قیمت تله = حدود ۵٪ تا ۸٪ زیر کفِ نرمال بازار (یا ۲۰ تا ۵۰ هزار تومان زیر کف قیمت رقیب اصلی)
    trap_price = int(round((floor_price * 0.95) / 10000) * 10000)
    if trap_price >= floor_price:
        trap_price = max(50000, floor_price - 20000)

    return {
        "ok": True,
        "query": query,
        "cities": target_cities,
        "total_scanned": len(all_ads),
        "valid_product_ads": len(working_pool),
        "service_ads_filtered": len(service_ads),
        "floor_price": floor_price,
        "median_price": median_price,
        "avg_price": avg_price,
        "ceiling_price": ceiling_price,
        "amin_trap_price": trap_price,
        "floor_ad": floor_ad,
        "top_cheapest": working_pool[:8],
        "top_expensive": working_pool[-3:] if len(working_pool) > 3 else [],
    }


def format_floor_report_tg(data: dict) -> str:
    if not data.get("ok"):
        return f"⚠️ <b>نتیجه‌ای برای «{data.get('query','')}» پیدا نشد:</b>\n{data.get('error','')}"

    q = data["query"]
    cities_str = "، ".join(data["cities"])
    fl = data["floor_ad"]
    lines = [
        f"🐺 <b>رادار کف قیمت دیوار (فرمول امین حیدری #1620)</b>",
        f"🔎 محصول: <b>{q}</b> | 📍 شهر: <b>{cities_str}</b>",
        f"📊 آگهی‌های اسکن‌شده: <b>{data['total_scanned']}</b> (فروش کالا: {data['valid_product_ads']} | خدمات/تعمیر حذف‌شده: {data['service_ads_filtered']})",
        "",
        f"🟢 <b>کف قیمت واقعی رقبا:</b> <code>{data['floor_price']:,}</code> تومان",
        f"🟡 <b>میانه قیمت بازار:</b> <code>{data['median_price']:,}</code> تومان",
        f"🔵 <b>میانگین قیمت بازار:</b> <code>{data['avg_price']:,}</code> تومان",
        f"🔴 <b>سقف قیمت بازار:</b> <code>{data['ceiling_price']:,}</code> تومان",
        "",
        f"🎯 <b>قیمت تله‌گذاری پیشنهادی امین حیدری (برای انفجار زنگ‌خور):</b>",
        f"🔥 <b><code>{data['amin_trap_price']:,} تومان</code></b> (همراه با فرمول بمباران مزیت در عنوان!)",
        "",
        f"🏆 <b>ارزان‌ترین آگهی‌های واقعی الان در دیوار:</b>",
    ]
    for idx, ad in enumerate(data["top_cheapest"][:6], 1):
        badge = "🏪 فروشگاه" if ad["is_shop"] else "👤 شخصی"
        promo = " | 🚀 نردبان/پله" if ad["is_promoted"] else ""
        lines.append(
            f"{idx}. <b>{ad['price']:,} تومان</b> — {ad['title']} ({ad['city']} | {badge}{promo})\n"
            f"   🔗 <a href=\"{ad['url']}\">مشاهده آگهی در دیوار</a>"
        )

    lines.extend([
        "",
        f"✍️ <b>عنوان تله‌گذاری‌شده آماده کپی برای تو (فرمول ویس #1537):</b>",
        f"<code>{q} {data['cities'][0]} / ضمانت کتبی / ارسال فوری / به قیمت عمده / اصلی</code>",
    ])
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "دیسک و صفحه پراید"
    c = sys.argv[2] if len(sys.argv) > 2 else "تهران"
    res = analyze_floor_price(q, c)
    print(json.dumps(res, ensure_ascii=False, indent=2))
