#!/usr/bin/env python3
"""
Diaspora AI Matchmaker v2.0 (موتور ۳گانه شکار و تطبیق خودکار دیوارهای تلگرامی ایرانیان خارج از کشور)
مجهز به:
  1) تبدیل خودکار شماره‌های آلمان (0176...) به لینک مستقیم واتساپ (https://wa.me/49176...) و انگلیس (+44)
  2) استخراج هم‌زمان هر ۳ مدل بی‌حاشیه (مکلر مسکن، استودیو دیجیتال، کارخانه رزومه و کاریابی)
  3) تولید متن کامل ۳ مرحله‌ای مکالمه و جلب اعتماد برای هر آگهی
"""
import os
import sys
import re
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.diaspora_divar_hunter import DIASPORA_CHANNELS, fetch_channel_posts

PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

CITY_ALIASES = {
    "هامبورگ": ["هامبورگ", "hamburg", "wandsbek", "barmbek", "norderstedt", "altona", "horn", "winterhude", "elbgau", "kieler"],
    "کلن/دوسلدورف": ["کلن", "köln", "دوسلدورف", "düsseldorf", "pempelfort", "frechen", "بوخوم", "اسن", "دورتموند", "zollstock"],
    "برلین": ["برلین", "berlin"],
    "فرانکفورت": ["فرانکفورت", "frankfurt"],
    "لندن": ["لندن", "london", "northolt", "angel", "barking"],
    "ونکوور/تورنتو": ["ونکوور", "vancouver", "تورنتو", "toronto"],
    "استانبول": ["استانبول", "istanbul", "اسنیورت"],
}


def detect_city(text: str, default_country: str) -> str:
    low = text.lower()
    for city, kws in CITY_ALIASES.items():
        if any(k in low for k in kws):
            return city
    return default_country


def format_contact_links(contacts: list[str], country: str) -> list[str]:
    """Convert raw @usernames and local phone numbers (0176..., 07...) into clickable t.me and wa.me links."""
    links = []
    for c in contacts:
        c_norm = c.translate(PERSIAN_DIGITS).strip()
        if c_norm.startswith("@"):
            uname = c_norm[1:]
            links.append(f"تلگرام: {c_norm} (https://t.me/{uname})")
        else:
            digits = re.sub(r"\D", "", c_norm)
            if len(digits) < 9:
                continue
            if digits.startswith("00"):
                digits = digits[2:]
            elif digits.startswith("0"):
                if "آلمان" in country:
                    digits = "49" + digits[1:]
                elif "انگلیس" in country:
                    digits = "44" + digits[1:]
                elif "ترکیه" in country:
                    digits = "90" + digits[1:]
                elif "امارات" in country:
                    digits = "971" + digits[1:]
                elif "کانادا" in country:
                    digits = "1" + digits[1:]
                elif digits.startswith("09"):
                    digits = "98" + digits[1:]
            links.append(f"واتساپ: +{digits} (https://wa.me/{digits})")
    return links


def run_matchmaker() -> dict:
    raw_ads = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        for res in ex.map(fetch_channel_posts, DIASPORA_CHANNELS):
            raw_ads.extend(res)

    seen = set()
    ads = []
    for a in raw_ads:
        sig = re.sub(r"\W+", "", a["text"][:80]).lower()
        if sig not in seen:
            seen.add(sig)
            a["city"] = detect_city(a["text"], a["country"])
            a["contact_links"] = format_contact_links(a["contacts"], a["country"])
            ads.append(a)

    housing_supply = []
    housing_demand = []
    digital_leads = []
    resume_job_leads = []

    for a in ads:
        t = a["text"].lower()
        if not a["contact_links"]:
            continue

        # 1. Housing Demand vs Supply
        if any(k in t for k in ["دنبال خونه", "نیازمند خانه", "دنبال خانه", "دنبال wg", "دنبال یک خونه", "نیاز به (هم اتاقی)", "دنبال یک هم‌خانه"]):
            housing_demand.append(a)
        elif any(k in t for k in ["برای اجاره میباشد", "آماده اجاره", "کرایه داده میشود", "موجود است", "برای اجاره موجود", "جهت anmeldung", "ملد ادرس"]):
            housing_supply.append(a)

        # 2. Digital Studio Leads (Direct requests + businesses needing reels/website/admin)
        if any(k in t for k in ["موشن دیزاینر", "فروش بین‌الملل", "طراحی سایت", "ادیتور", "ادمین", "آرایشگر", "رستوران", "سالن", "کلینیک", "بازسازی", "مغازه"]):
            digital_leads.append(a)

        # 3. Resume (Bewerbung) & Job/Ausbildung Leads
        if any(k in t for k in ["نیازمندیم", "استخدام", "فرصت شغلی", "مسلط به زبان", "مینی جاب", "فول تایم", "پارت تایم", "راننده", "ویتر", "ناخن کار", "ausbildung", "bewerbung"]):
            resume_job_leads.append(a)

    # Match Housing Demand <-> Supply by City (with diverse tenants & landlords first)
    housing_matches_all = []
    for dem in housing_demand:
        for sup in housing_supply:
            if dem["city"] == sup["city"]:
                housing_matches_all.append({
                    "city": dem["city"],
                    "dem_id": dem["url"],
                    "sup_id": sup["url"],
                    "buyer_tenant": {
                        "url": dem["url"],
                        "contacts": dem["contact_links"],
                        "summary": dem["text"][:150]
                    },
                    "seller_landlord": {
                        "url": sup["url"],
                        "contacts": sup["contact_links"],
                        "summary": sup["text"][:150]
                    },
                    "step1_to_landlord": (
                        f"سلام وقت بخیر 🌹\n"
                        f"در مورد واحدی که در {sup['city']} آگهی کردید، هنوز موجوده؟\n"
                        f"ما دو متقاضی ایرانی موجه و شاغل (با قرارداد کاری و بدون حاشیه) دقیقا در {sup['city']} داریم که دنبال همچین واحدی هستن. "
                        f"هزینه معرفی رو هم خودمون از سمت مستأجر می‌گیریم و برای شما هیچ هزینه‌ای نداره. اجازه می‌دید شرایطشون رو بفرستم؟"
                    ),
                    "step2_to_tenant": (
                        f"سلام وقت بخیر 🌹\n"
                        f"دیدم در {dem['city']} دنبال واحد/اتاق هستید. ما یک فایل جدید در {dem['city']} از صاحب‌خانه ایرانی رصد کردیم که با شرایط شما می‌خونه.\n"
                        f"ما هیچ پیش‌پرداختی بابت معرفی نمی‌گیریم؛ اول تایم بازدید حضوری شما با صاحب‌خانه رو فیکس می‌کنیم، اگر واحد رو از نزدیک دیدید و پسندیدید، بابت حق معرفی فایل ۲۰۰ یورو (قابل تسویه ریالی در ایران) دریافت می‌شه. اگر هنوز خونه نگرفتید بگید تا مشخصات اولیه رو بفرستم."
                    )
                })

    housing_matches = []
    used_dem = set()
    used_sup = set()
    for m in housing_matches_all:
        if m["dem_id"] not in used_dem and m["sup_id"] not in used_sup:
            housing_matches.append(m)
            used_dem.add(m["dem_id"])
            used_sup.add(m["sup_id"])
    for m in housing_matches_all:
        if m not in housing_matches:
            housing_matches.append(m)

    return {
        "total_unique_ads": len(ads),
        "counts": {
            "housing_supply": len(housing_supply),
            "housing_demand": len(housing_demand),
            "housing_matched_pairs": len(housing_matches),
            "digital_studio_leads": len(digital_leads),
            "resume_and_job_leads": len(resume_job_leads),
        },
        "top_housing_matches": housing_matches[:8],
        "digital_leads": digital_leads[:8],
        "resume_job_leads": resume_job_leads[:8]
    }


def format_telegram_diaspora_report() -> str:
    rep = run_matchmaker()
    c = rep["counts"]
    lines = [
        "🌍 <b>رادار زنده ۳گانه «دیوارهای تلگرامی خارج از کشور» (مکلر مسکن + استودیو دیجیتال + کارخانه رزومه)</b>",
        f"📊 اسکن زنده: <code>{rep['total_unique_ads']}</code> آگهی یکتا | جفت‌های مسکن: <code>{c['housing_matched_pairs']}</code> | لید دیجیتال: <code>{c['digital_studio_leads']}</code> | کاریابی/رزومه: <code>{c['resume_and_job_leads']}</code>\n",
        "🏠 <b>مدل ۱: جفت‌های آماده «مکلر مسکن» (۹۰٪ هوش مصنوعی | شیرینی ۲۰۰ تا ۱۰۰۰ یورو):</b>"
    ]
    for idx, m in enumerate(rep["top_housing_matches"][:3], 1):
        t_links = " | ".join(m["buyer_tenant"]["contacts"])
        l_links = " | ".join(m["seller_landlord"]["contacts"])
        lines.append(
            f"\n🔹 <b>جفت #{idx} در شهر {m['city']}:</b>\n"
            f"👤 <b>متقاضی (خریدار):</b> {m['buyer_tenant']['summary']}...\n"
            f"🔗 <a href=\"{m['buyer_tenant']['url']}\">لینک آگهی</a> | {t_links}\n"
            f"🔑 <b>صاحب‌خانه (فروشنده):</b> {m['seller_landlord']['summary']}...\n"
            f"🔗 <a href=\"{m['seller_landlord']['url']}\">لینک آگهی</a> | {l_links}"
        )

    lines.append("\n💻 <b>مدل ۲: مشتریان آماده «استودیو دیجیتال و ادمین/موشن» (۸۵٪ هوش مصنوعی | ۲۰۰ تا ۶۰۰ یورو):</b>")
    for idx, d in enumerate(rep["digital_leads"][:4], 1):
        d_links = " | ".join(d["contact_links"])
        lines.append(
            f"\n🔸 <b>لید دیجیتال #{idx} [{d['city']}]:</b> {d['text'][:135]}...\n"
            f"🔗 <a href=\"{d['url']}\">لینک آگهی</a> | {d_links}"
        )

    lines.append("\n📄 <b>مدل ۳: کارفرمایان و سوژه‌های «رزومه آلمانی/انگلیسی و کاریابی» (۹۵٪ هوش مصنوعی | ۵۰ تا ۱۵۰ یورو):</b>")
    for idx, r in enumerate(rep["resume_job_leads"][:3], 1):
        r_links = " | ".join(r["contact_links"])
        lines.append(
            f"\n▪️ <b>فرصت شغلی #{idx} [{r['city']}]:</b> {r['text'][:135]}...\n"
            f"🔗 <a href=\"{r['url']}\">لینک آگهی</a> | {r_links}"
        )

    return "\n".join(lines)


if __name__ == "__main__":
    print(format_telegram_diaspora_report())
