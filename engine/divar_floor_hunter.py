#!/usr/bin/env python3
"""
Divar Brand-Aware & Freshness-Filtered Floor-Price Hunter v3.0 (نسخه نهایی و کامل)
فیلترهای ۵ لایه‌ای:
1) تفکیک شهر (۳۸ شهر ایران + حالت چندشهره)
2) تفکیک برند (۳۰+ برند با تمام املاهای رایج + تفکیک «برند در عنوان» از «برند در متن»)
3) تفکیک «🆕 نو/اصلی» از «♻️ استوک/در حد نو/کارکرده»
4) فیلتر زمانی هوشمند: فقط آگهی‌های نهایتاً تا ۲ هفته قبل (۱۴ روز اخیر) پذیرفته می‌شوند، مگر اینکه «نردبان / پله / فوری» خورده باشند!
5) حذف خودکار آگهی‌های دستمزد/تعمیرگاه و قیمت‌های صوری (۱۰۰ هزار تومانی)
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
    "تهران": "tehran", "مشهد": "mashhad", "اصفهان": "isfahan", "شیراز": "shiraz",
    "تبریز": "tabriz", "کرج": "karaj", "اهواز": "ahvaz", "قم": "qom",
    "کرمانشاه": "kermanshah", "رشت": "rasht", "یزد": "yazd", "ارومیه": "urmia",
    "کرمان": "kerman", "همدان": "hamedan", "اراک": "arak", "زاهدان": "zahedan",
    "بندرعباس": "bandar-abbas", "قزوین": "qazvin", "گرگان": "gorgan", "ساری": "sari",
    "بابل": "babol", "آمل": "amol", "اردبیل": "ardabil", "زنجان": "zanjan",
    "سنندج": "sanandaj", "خرم‌آباد": "khorramabad", "خرم آباد": "khorramabad",
    "بوشهر": "bushehr", "کاشان": "kashan", "نیشابور": "neyshabur", "سبزوار": "sabzevar",
    "دزفول": "dezful", "آبادان": "abadan", "بروجرد": "borujerd", "اسلامشهر": "eslamshahr",
    "شهریار": "shahriar", "قدس": "qods-city", "ملارد": "malard", "پاکدشت": "pakdasht",
    "ورامین": "varamin", "ری": "rey",
}

BRAND_ALIASES = {
    "سکو (SECO کره)": ["سکو", "سیکو", "seco"],
    "والئو آبی/سبز (Valeo/PHC)": ["والئو آبی", "والئو سبز", "والئو", "ولئو", "والو", "ولوابی", "والوابی", "valeo", "phc"],
    "عظام (Ezam)": ["عظام پلاس", "عظام", "ezam"],
    "دایکن (Daikin ژاپن)": ["دایکن", "دایکین", "اگزدی", "daikin", "exedy"],
    "لوک (LuK آلمان)": ["لوک", "luk"],
    "سایپا یدک / شرکتی": ["سایپا یدک", "سایپا", "شرکتی"],
    "ایساکو (ISACO)": ["ایساکو", "isaco"],
    "دیناپارت": ["دیناپارت", "dinapart"],
    "تکستار (Textar)": ["تکستار", "تکس تار", "textar"],
    "الیگ (Elig)": ["الیگ", "elig"],
    "پارس (لنت/کلاچ پارس)": ["لنت پارس", "پارس آبی", "پارس"],
    "ماندو (Mando کره)": ["ماندو", "mando"],
    "های‌کیو (Hi-Q کره)": ["های کیو", "هایکیو", "hi-q", "hiq"],
    "آفورتیس (Afortis)": ["آفورتیس", "افورتیس", "afortis"],
    "گلد (Gold)": ["گلد", "gold"],
    "کنتیننتال (Continental)": ["کنتیننتال", "کنتی تک", "کنتیتک", "continental", "contitech"],
    "دانگیل (Dongil کره)": ["دانگیل", "دونگیل", "dongil"],
    "پاورگریپ / گیتس (Gates)": ["پاورگریپ", "پاور گریپ", "گیتس", "gates", "powergrip"],
    "رافائل (Rafael)": ["رافائل", "رافایل", "rafael"],
    "هاچینسون (Hutchinson)": ["هاچینسون", "hutchinson"],
    "بوش (Bosch)": ["بوش", "bosch"],
    "ان‌جی‌کی (NGK ژاپن)": ["ان جی کی", "انجی کی", "ngk"],
    "دنسو (Denso)": ["دنسو", "denso"],
    "اکیوم (Eyquem)": ["اکیوم", "eyquem"],
    "کروز (Crouse)": ["کروز", "crouse"],
    "امکو (AMCO)": ["امکو", "amco"],
    "امیرنیا (Amirnia)": ["امیرنیا", "امیر نیا", "amirnia"],
    "ایندامین (Indamin)": ["ایندامین", "indamin"],
    "کایابا (KYB)": ["کایابا", "kyb"],
    # برندهای تجهیزات پزشکی، دندانپزشکی و ICU خانگی
    "پارس دنتال (Pars Dental)": ["پارس دنتال", "پارس دنت"],
    "زیگر (Siger)": ["زیگر", "siger"],
    "کارن (Karen)": ["کارن", "karen"],
    "یوول (Yuwell)": ["یوول", "yuwell"],
    "نایدک (Nidek آمریکا)": ["نایدک", "nidek"],
    "رسمد (ResMed)": ["رسمد", "resmed"],
    "فیلیپس (Philips)": ["فیلیپس", "philips"],
    "سوپرانو تیتانیوم (Soprano)": ["تیتانیوم", "سوپرانو", "soprano"],
}

CATEGORY_BRANDS = {
    "دیسک": ["سکو (SECO کره)", "والئو آبی/سبز (Valeo/PHC)", "عظام (Ezam)", "دایکن (Daikin ژاپن)", "سایپا یدک / شرکتی"],
    "صفحه": ["سکو (SECO کره)", "والئو آبی/سبز (Valeo/PHC)", "عظام (Ezam)", "دایکن (Daikin ژاپن)", "سایپا یدک / شرکتی"],
    "کلاچ": ["سکو (SECO کره)", "والئو آبی/سبز (Valeo/PHC)", "عظام (Ezam)", "دایکن (Daikin ژاپن)"],
    "لنت": ["تکستار (Textar)", "الیگ (Elig)", "پارس (لنت/کلاچ پارس)", "ماندو (Mando کره)", "های‌کیو (Hi-Q کره)", "عظام (Ezam)"],
    "تسمه": ["کنتیننتال (Continental)", "دانگیل (Dongil کره)", "پاورگریپ / گیتس (Gates)", "رافائل (Rafael)", "ایساکو (ISACO)"],
    "شمع": ["بوش (Bosch)", "ان‌جی‌کی (NGK ژاپن)", "دنسو (Denso)", "اکیوم (Eyquem)"],
    "وایر": ["بوش (Bosch)", "عظام (Ezam)", "کروز (Crouse)", "ایساکو (ISACO)"],
    "جلوبندی": ["امکو (AMCO)", "امیرنیا (Amirnia)", "عظام (Ezam)", "ایساکو (ISACO)"],
    "کمک": ["ایندامین (Indamin)", "کایابا (KYB)", "عظام (Ezam)", "ماندو (Mando کره)"],
    "سرسیلندر": ["ایساکو (ISACO)", "عظام (Ezam)", "دیناپارت"],
    "یونیت": ["پارس دنتال (Pars Dental)", "زیگر (Siger)", "کارن (Karen)"],
    "اکسیژن": ["یوول (Yuwell)", "نایدک (Nidek آمریکا)", "فیلیپس (Philips)"],
    "بای پپ": ["رسمد (ResMed)", "فیلیپس (Philips)", "یوول (Yuwell)"],
}

SERVICE_NOISE_WORDS = [
    "تعمیر", "تعمیرگاه", "لنت کوبی", "تراشکاری", "اجرت", "نصب در محل",
    "مکانیکی", "میکانیکی", "جلوبندی سازی", "صافکاری", "نقاشی", "کارواش", "تعویض تخصصی"
]

USED_STOCK_WORDS = [
    "استوک", "در حد نو", "درحدنو", "در حد", "کارکرده", "دست دوم", "تراش خورده", "کوبیده", "ریفر"
]

# فیلتر هوشمند فصل و تقاضای زمانی (۳۶۵ روزه در برابر فصلی پاییز/زمستان و تابستان)
SEASONAL_TAG_RULES = {
    "summer_only": {
        "keywords": ["کولر گازی", "کولر آبی", "موتور برق", "پنکه", "چیلر"],
        "badge": "⚠️ [فصلی تابستان — الان در پاییز/زمستان تقاضا پایین‌تر است؛ زمان خرید زیر قیمت از فروشنده‌های پول‌لازم!]"
    },
    "autumn_winter_peak": {
        "keywords": ["گرماتاب", "پکیج", "رادیاتور", "بخاری", "هیتر", "شوفاژ", "باتری", "باطری", "ضد یخ", "برف پاک کن", "لاستیک"],
        "badge": "🔥 [اوج تقاضای فصل الان (پاییز و زمستان) — نقدشوندگی و زنگ‌خور فوق‌العاده بالا!]"
    },
    "evergreen_top20": {
        "keywords": ["یونیت", "پزشکی", "سانتریفیوژ", "دندانپزشکی", "آهن", "میلگرد", "تیرآهن", "سنگ", "کابینت", "سیم کارت", "0912", "آیفون", "طلا", "دیسک", "صفحه", "لنت", "تسمه", "سرسیلندر", "یخچال صنعتی", "اسپرسوساز"],
        "badge": "💎 [تقاضای ۳۶۵ روزه چهارفصل و ضدبحران — بازار نقد و همیشگی]"
    }
}


def get_seasonality_badge(query: str) -> str:
    q_low = (query or "").lower()
    for grp in ("autumn_winter_peak", "summer_only", "evergreen_top20"):
        info = SEASONAL_TAG_RULES[grp]
        if any(k in q_low for k in info["keywords"]):
            return info["badge"]
    return "💎 [تقاضای چهارفصل ۳۶۵ روزه]"


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


def check_freshness_14d(meta: str) -> tuple[bool, str]:
    """
    قانون فیلتر زمانی کاربر:
    1) اگر آگهی «نردبان شده»، «پله شده» یا «فوری» باشد -> همیشه معتبر و به‌روز است (True).
    2) اگر تا نهایتاً ۲ هفته پیش (۱۴ روز اخیر) باشد -> معتبر است (True).
    3) اگر ۳ هفته پیش، ۴ هفته پیش، ماه پیش یا قدیمی‌تر باشد و نردبان/پله نخورده باشد -> فیلتر می‌شود (False).
    """
    m_norm = (meta or "").translate(PERSIAN_DIGITS).strip()
    is_boosted = any(k in m_norm for k in ("نردبان", "پله", "فوری"))
    if is_boosted:
        if "پله" in m_norm:
            return True, "🚀 پله شده"
        if "فوری" in m_norm:
            return True, "🔥 فوری"
        return True, "🚀 نردبان شده"

    # بررسی عبارات قدیمی‌تر از ۲ هفته (وقتی نردبان/پله نخورده‌اند)
    if any(k in m_norm for k in ("ماه پیش", "سال پیش", "چند هفته پیش")):
        return False, "⏳ قدیمی (بیش از ۲ هفته)"

    wk_m = re.search(r'(\d+)\s*هفته', m_norm)
    if wk_m:
        weeks = int(wk_m.group(1))
        if weeks > 2:
            return False, f"⏳ {weeks} هفته پیش (حذف شد)"
        return True, f"⏱️ {weeks} هفته پیش"

    if "هفتهٔ پیش" in m_norm or "هفته پیش" in m_norm:
        return True, "⏱️ ۱ هفته پیش"

    day_m = re.search(r'(\d+)\s*روز\s*پیش', m_norm)
    if day_m:
        days = int(day_m.group(1))
        if days > 14:
            return False, f"⏳ {days} روز پیش (حذف شد)"
        return True, f"⏱️ {days} روز پیش"

    if "پریروز" in m_norm:
        return True, "⏱️ پریروز"
    if "دیروز" in m_norm:
        return True, "⏱️ دیروز"
    if any(k in m_norm for k in ("ساعت پیش", "دقایقی پیش", "لحظاتی پیش", "ربع پیش", "امروز")):
        hr_m = re.search(r'(\d+\s*ساعت\s*پیش)', m_norm)
        return True, f"⏱️ {hr_m.group(1) if hr_m else 'امروز'}"

    return True, "⏱️ فعال (تا ۲ هفته)"


def detect_brand_in_query(query: str) -> tuple[str | None, list[str], str]:
    q_norm = query.strip().lower()
    for canonical, aliases in BRAND_ALIASES.items():
        for al in sorted(aliases, key=len, reverse=True):
            al_low = al.lower()
            if re.search(rf'(^|\s|‌){re.escape(al_low)}($|\s|‌)', q_norm) or (len(al_low) >= 4 and al_low in q_norm):
                base_q = re.sub(re.escape(al), "", query, flags=re.IGNORECASE).strip()
                base_q = re.sub(r"\s+", " ", base_q).strip()
                return canonical, aliases, (base_q or query)
    return None, [], query


def detect_brands_in_title(title: str) -> list[str]:
    t_low = title.lower()
    found = []
    for canonical, aliases in BRAND_ALIASES.items():
        for al in aliases:
            if al.lower() in t_low:
                found.append(canonical)
                break
    return found


def fetch_city_ads(query: str, city_fa: str = "تهران", brand_aliases: list[str] | None = None, timeout: int = 18) -> list[dict]:
    city_label, slug = resolve_city(city_fa)
    q_enc = urllib.parse.quote(query.strip())
    url = f"https://r.jina.ai/https://divar.ir/s/{slug}?q={q_enc}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        md = urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore")
    except Exception:
        return []

    ads = []
    seen_urls = set()
    for m in re.finditer(r'## \[(.*?)\]\((https://divar\.ir/v/[^\)]+)\)', md):
        raw = m.group(1)
        link = m.group(2)
        if link in seen_urls:
            continue
        seen_urls.add(link)
        clean = re.sub(r'!\[Image[^\]]*\]\([^\)]+\)', '', raw).strip()
        clean = re.sub(r'\s+', ' ', clean)
        pm = re.search(r'([\d۰-۹,٬]+)\s*تومان', clean)
        if not pm:
            continue
        price_val = int(re.sub(r'[^\d]', '', pm.group(1).translate(PERSIAN_DIGITS)) or 0)
        if price_val < 100000 or str(price_val) in ("111111", "1111111", "123456", "1234567"):
            continue
        title = clean[:pm.start()].strip()
        meta = clean[pm.end():].strip()
        is_service = any(w in title for w in SERVICE_NOISE_WORDS)
        is_stock = any(w in title for w in USED_STOCK_WORDS)
        is_shop = "فروشگاه" in meta
        is_promoted = any(k in meta for k in ("نردبان", "پله", "فوری"))
        is_fresh, freshness_label = check_freshness_14d(meta)
        title_brands = detect_brands_in_title(title)

        exact_brand_in_title = False
        if brand_aliases:
            t_low = title.lower()
            exact_brand_in_title = any(a.lower() in t_low for a in brand_aliases)

        ads.append({
            "city": city_label,
            "city_slug": slug,
            "title": title,
            "price": price_val,
            "meta": meta,
            "url": link,
            "is_service": is_service,
            "is_stock": is_stock,
            "is_shop": is_shop,
            "is_promoted": is_promoted,
            "is_fresh": is_fresh,
            "freshness_label": freshness_label,
            "title_brands": title_brands,
            "exact_brand_in_title": exact_brand_in_title,
        })

    ads.sort(key=lambda x: x["price"])
    return ads


def scan_single_brand_summary(base_query: str, brand_canonical: str, city_fa: str) -> dict | None:
    aliases = BRAND_ALIASES.get(brand_canonical, [])
    if not aliases:
        return None
    q_search = f"{base_query} {aliases[0]}"
    ads = fetch_city_ads(q_search, city_fa=city_fa, brand_aliases=aliases, timeout=18)
    if len(aliases) > 1 and sum(1 for a in ads if a["exact_brand_in_title"] and a["is_fresh"]) < 3:
        ads2 = fetch_city_ads(f"{base_query} {aliases[1]}", city_fa=city_fa, brand_aliases=aliases, timeout=16)
        seen = {a["url"] for a in ads}
        for a in ads2:
            if a["url"] not in seen:
                ads.append(a)
                seen.add(a["url"])

    # فقط آگهی‌های فروش قطعه که یا نهایتاً تا ۲ هفته پیش‌اند یا نردبان/پله شده‌اند
    valid = [a for a in ads if not a["is_service"] and a["is_fresh"]]
    stale_removed = sum(1 for a in ads if not a["is_service"] and not a["is_fresh"])
    if not valid:
        return None

    exact_new = [a for a in valid if a["exact_brand_in_title"] and not a["is_stock"]]
    exact_all = [a for a in valid if a["exact_brand_in_title"]]
    body_new = [a for a in valid if not a["exact_brand_in_title"] and not a["is_stock"]]

    primary_pool = exact_new if exact_new else (exact_all if exact_all else (body_new if body_new else valid))
    if len(primary_pool) >= 2:
        raw_m = statistics.median([x["price"] for x in primary_pool])
        cleaned = [x for x in primary_pool if x["price"] >= max(300000, raw_m * 0.28)]
        if cleaned:
            primary_pool = cleaned
    primary_pool.sort(key=lambda x: x["price"])
    prices = [x["price"] for x in primary_pool]

    floor_ad = primary_pool[0]
    floor_p = floor_ad["price"]
    med_p = int(statistics.median(prices))
    ceil_p = primary_pool[-1]["price"]
    trap_p = int(round((floor_p * 0.96) / 10000) * 10000)
    if trap_p >= floor_p:
        trap_p = max(100000, floor_p - 30000)

    return {
        "brand": brand_canonical,
        "total_found": len(valid),
        "stale_removed": stale_removed,
        "exact_title_count": len(exact_all),
        "exact_new_count": len(exact_new),
        "floor_price": floor_p,
        "median_price": med_p,
        "ceiling_price": ceil_p,
        "trap_price": trap_p,
        "floor_ad": floor_ad,
        "top_ads": (exact_new + [a for a in exact_all if a not in exact_new] + body_new)[:6],
    }


def analyze_floor_price(query: str, city_fa: str = "تهران", multi_city: bool = False) -> dict:
    brand_canonical, brand_aliases, base_query = detect_brand_in_query(query)
    city_label, _ = resolve_city(city_fa)

    if multi_city or city_fa.strip() in ("همه", "کل ایران", "ایران", "چند شهر"):
        target_cities = ["تهران", "مشهد", "اصفهان", "شیراز"]
    else:
        target_cities = [city_label]

    all_ads = []
    if brand_canonical:
        search_terms = [f"{base_query} {brand_aliases[0]}"]
        if len(brand_aliases) > 1:
            search_terms.append(f"{base_query} {brand_aliases[1]}")
        tasks = [(st, c) for c in target_cities for st in search_terms]
        with ThreadPoolExecutor(max_workers=min(6, len(tasks) or 1)) as ex:
            futs = [ex.submit(fetch_city_ads, st, c, brand_aliases, 18) for st, c in tasks]
            seen_u = set()
            for f in futs:
                try:
                    for ad in f.result():
                        if ad["url"] not in seen_u:
                            all_ads.append(ad)
                            seen_u.add(ad["url"])
                except Exception:
                    pass
    else:
        if len(target_cities) == 1:
            all_ads = fetch_city_ads(query, target_cities[0], None, timeout=20)
        else:
            with ThreadPoolExecutor(max_workers=4) as ex:
                for res_list in ex.map(lambda c: fetch_city_ads(query, c, None, 18), target_cities):
                    all_ads.extend(res_list)

    service_ads = [a for a in all_ads if a["is_service"]]
    stale_ads = [a for a in all_ads if not a["is_service"] and not a["is_fresh"]]
    # اعمال قانون طلایی: فقط آگهی‌های تا ۲ هفته اخیر یا آگهی‌های نردبان/پله/فوری
    product_ads = [a for a in all_ads if not a["is_service"] and a["is_fresh"]]

    exact_brand_new = [a for a in product_ads if a["exact_brand_in_title"] and not a["is_stock"]]
    exact_brand_all = [a for a in product_ads if a["exact_brand_in_title"]]
    new_product_ads = [a for a in product_ads if not a["is_stock"]]

    if brand_canonical and exact_brand_new:
        working_pool = exact_brand_new
    elif brand_canonical and exact_brand_all:
        working_pool = exact_brand_all
    elif new_product_ads:
        working_pool = new_product_ads
    else:
        working_pool = product_ads if product_ads else [a for a in all_ads if not a["is_service"]]

    if len(working_pool) >= 2:
        raw_med = statistics.median([x["price"] for x in working_pool])
        filt = [x for x in working_pool if x["price"] >= max(300000, raw_med * 0.28)]
        if filt:
            working_pool = filt

    working_pool.sort(key=lambda x: x["price"])

    brand_breakdown = []
    candidate_brands = []
    for kw, b_list in CATEGORY_BRANDS.items():
        if kw in base_query:
            candidate_brands = b_list
            break

    if candidate_brands and len(target_cities) == 1:
        with ThreadPoolExecutor(max_workers=5) as ex:
            futs = [ex.submit(scan_single_brand_summary, base_query, b_name, target_cities[0]) for b_name in candidate_brands]
            for f in futs:
                try:
                    r = f.result()
                    if r:
                        brand_breakdown.append(r)
                except Exception:
                    pass
        brand_breakdown.sort(key=lambda x: x["floor_price"])

    if not working_pool:
        return {
            "ok": False,
            "query": query,
            "base_query": base_query,
            "brand": brand_canonical,
            "cities": target_cities,
            "brand_breakdown": brand_breakdown,
            "error": "هیچ آگهی معتبر و به‌روزی (تا ۲ هفته اخیر یا نردبان/پله‌شده) در دیوار برای این عبارت پیدا نشد."
        }

    prices = [x["price"] for x in working_pool]
    floor_ad = working_pool[0]
    floor_price = floor_ad["price"]
    median_price = int(statistics.median(prices))
    avg_price = int(statistics.mean(prices))
    ceiling_price = working_pool[-1]["price"]

    trap_price = int(round((floor_price * 0.96) / 10000) * 10000)
    if trap_price >= floor_price:
        trap_price = max(100000, floor_price - 30000)

    min_valid_p = max(250000, int(median_price * 0.25)) if median_price >= 1000000 else 100000
    if brand_canonical:
        ordered_display = [
            a for a in (
                sorted(exact_brand_new, key=lambda x: x["price"])
                + sorted([a for a in exact_brand_all if a["is_stock"]], key=lambda x: x["price"])
                + sorted([a for a in product_ads if not a["exact_brand_in_title"]], key=lambda x: x["price"])
            )
            if a["price"] >= min_valid_p
        ]
    else:
        ordered_display = working_pool

    return {
        "ok": True,
        "query": query,
        "base_query": base_query,
        "brand": brand_canonical,
        "cities": target_cities,
        "total_scanned": len(all_ads),
        "valid_product_ads": len(product_ads),
        "stale_ads_filtered": len(stale_ads),
        "exact_brand_title_ads": len(exact_brand_all),
        "exact_brand_new_ads": len(exact_brand_new),
        "service_ads_filtered": len(service_ads),
        "floor_price": floor_price,
        "median_price": median_price,
        "avg_price": avg_price,
        "ceiling_price": ceiling_price,
        "amin_trap_price": trap_price,
        "floor_ad": floor_ad,
        "top_cheapest": ordered_display[:8],
        "brand_breakdown": brand_breakdown,
    }


def format_floor_report_tg(data: dict) -> str:
    if not data.get("ok"):
        return f"⚠️ <b>نتیجه‌ای برای «{data.get('query','')}» پیدا نشد:</b>\n{data.get('error','')}"

    q = data["query"]
    brand = data.get("brand")
    cities_str = "، ".join(data["cities"])
    brand_line = (
        f"🏷️ فیلتر برند: <b>{brand}</b> (تطابق قطعی در عنوان: {data['exact_brand_title_ads']} | نو آکبند: {data['exact_brand_new_ads']})"
        if brand else
        "🏷️ فیلتر برند: <b>همه برندها + جدول تفکیکی خودکار برندها</b>"
    )

    lines = [
        f"🐺 <b>رادار کف قیمت دیوار به تفکیک برند، تاریخ و فصل (v3.1)</b>",
        f"🔎 جست‌وجو: <b>{q}</b> | 📍 شهر: <b>{cities_str}</b>",
        brand_line,
        f"📅 وضعیت تقاضای فصلی: <b>{get_seasonality_badge(q)}</b>",
        f"⏱️ فیلتر زمان آگهی: <b>حداکثر تا ۲ هفته قبل (یا دارای نردبان/پله/فوری)</b>",
        f"📊 اسکن‌شده: <b>{data['total_scanned']}</b> (معتبر و به‌روز: {data['valid_product_ads']} | قدیمی‌تر از ۲ هفته حذف‌شده: {data.get('stale_ads_filtered',0)} | تعمیرات حذف‌شده: {data['service_ads_filtered']})",
        "",
        f"🟢 <b>کف قیمت واقعی (نو/به‌روز):</b> <code>{data['floor_price']:,}</code> تومان",
        f"🟡 <b>میانه قیمت این رده:</b> <code>{data['median_price']:,}</code> تومان",
        f"🔵 <b>میانگین قیمت:</b> <code>{data['avg_price']:,}</code> تومان",
        f"🔴 <b>سقف قیمت:</b> <code>{data['ceiling_price']:,}</code> تومان",
        "",
        f"🎯 <b>قیمت تله‌گذاری پیشنهادی امین حیدری:</b>",
        f"🔥 <b><code>{data['amin_trap_price']:,} تومان</code></b>",
    ]

    bb = data.get("brand_breakdown") or []
    if bb:
        lines.extend(["", f"📊 <b>جدول تفکیکی کف قیمت برندهای «{data['base_query']}» در {cities_str} (فقط تا ۲ هفته اخیر یا نردبان/پله):</b>"])
        for b_item in bb:
            ex_cnt = b_item["exact_title_count"]
            match_lbl = f"🎯 {ex_cnt} در عنوان" if ex_cnt > 0 else "📌 در متن"
            lines.append(
                f"• <b>{b_item['brand']}:</b> کف <code>{b_item['floor_price']:,}</code> | میانه <code>{b_item['median_price']:,}</code> | تله: <code>{b_item['trap_price']:,}</code> تومان ({match_lbl})"
            )

    lines.extend(["", f"🏆 <b>لیست دقیق آگهی‌های به‌روز دیوار (حداکثر ۲ هفته یا نردبان/پله):</b>"])
    for idx, ad in enumerate(data["top_cheapest"][:7], 1):
        badge = "🏪 فروشگاه" if ad["is_shop"] else "👤 شخصی"
        cond = "♻️ استوک/درحد" if ad["is_stock"] else "🆕 نو"
        fresh_tag = ad.get("freshness_label", "⏱️ به‌روز")
        b_tag = "🎯[برند در عنوان]" if ad.get("exact_brand_in_title") else ("📌[برند در متن]" if brand else "")
        b_detected = f" [{', '.join(ad['title_brands'])}]" if (not brand and ad.get("title_brands")) else ""
        lines.append(
            f"{idx}. <b>{ad['price']:,} تومان</b> ({cond} | {badge} | {fresh_tag}) {b_tag}{b_detected}\n"
            f"   📝 {ad['title']}\n"
            f"   🔗 <a href=\"{ad['url']}\">مشاهده آگهی در دیوار</a>"
        )

    title_brand_str = f" {brand.split('(')[0].strip()}" if brand else " اصلی"
    lines.extend([
        "",
        f"✍️ <b>عنوان تله‌گذاری‌شده آماده کپی (فرمول ویس #1537):</b>",
        f"<code>{data['base_query']}{title_brand_str} {data['cities'][0]} / ضمانت کتبی / بدون لرزش / قیمت عمده / ارسال فوری</code>",
    ])
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "دیسک و صفحه پراید سکو"
    c = sys.argv[2] if len(sys.argv) > 2 else "تهران"
    res = analyze_floor_price(q, c)
    print(format_floor_report_tg(res))
