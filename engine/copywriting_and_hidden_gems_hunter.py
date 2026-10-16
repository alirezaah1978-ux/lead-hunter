#!/usr/bin/env python3
"""
Copywriting & Hidden Gems Hunter v1.0
1) شکار مستقیم مشتریان «کپی‌رایتینگ، تبلیغ‌نویسی و سناریونویسی ریلز/آگهی» در ایران (@didogram, @doorkaari) و خارج (۱۴ کانال دیاسپورا)
2) شکار ۷ معدن پنهان دست‌به‌نقد (تطبیق خودرو/ون اقساطی، فروش یکجای اثاثیه مهاجران، فرم‌های اداری/آوسبیلدونگ، کلون آواتار ویدیویی پزشکان/املاک)
"""
import os
import sys
import re
import json
import html
import urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

ALL_CHANNELS = [
    # کانال‌های استخدام سناریونویس/کپی‌رایتر/ادمین در ایران
    {"handle": "didogram", "region": "🇮🇷 ایران (دیدوگرام)", "pages": 2},
    {"handle": "doorkaari", "region": "🇮🇷 ایران (دورکاری)", "pages": 2},
    {"handle": "karlancer_projects", "region": "🇮🇷 ایران (کارلنسر)", "pages": 2},
    # کانال‌های ایرانیان خارج از کشور (آلمان، انگلیس، سوئد، هلند، کانادا، امارات، عمان، ترکیه)
    {"handle": "Akfon_DE", "region": "🇩🇪 آلمان (اکفون)", "pages": 4},
    {"handle": "iran_germany_1", "region": "🇩🇪 آلمان (مقیم آلمان)", "pages": 2},
    {"handle": "Niaz4uk", "region": "🇬🇧 انگلیس (لندن)", "pages": 2},
    {"handle": "Iranian_UK_Ads", "region": "🇬🇧 انگلیس (بازار UK)", "pages": 2},
    {"handle": "iranianswede", "region": "🇸🇪 سوئد (نیازمندی‌ها)", "pages": 2},
    {"handle": "IRANIANHOLAND", "region": "🇳🇱 هلند (ایرانیان)", "pages": 2},
    {"handle": "walcad", "region": "🇨🇦 کانادا (ونکوور)", "pages": 2},
    {"handle": "dubaiparsi", "region": "🇦🇪 امارات (دبی پارسی)", "pages": 2},
    {"handle": "omanex", "region": "🇴🇲 عمان (عمان اکس)", "pages": 2},
    {"handle": "divar_estanbul", "region": "🇹🇷 ترکیه (استانبول)", "pages": 2},
]


def fetch_posts(ch: dict) -> list[dict]:
    h = ch["handle"]
    before = None
    out = []
    for _ in range(ch.get("pages", 2)):
        u = f"https://t.me/s/{h}" + (f"?before={before}" if before else "")
        try:
            raw = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=14).read().decode("utf-8", "ignore")
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
            clean = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", tx.group(1)))).strip()
            if len(clean) < 25:
                continue
            contacts = re.findall(r'@[A-Za-z0-9_]{4,}|\+?\d[\d\s\-]{8,14}\d|[۰-۹]{10,12}', clean)
            contacts = [x.strip() for x in contacts if x.lower() != f"@{h.lower()}"]
            out.append({
                "channel": h,
                "region": ch["region"],
                "id": pid,
                "text": clean,
                "contacts": list(dict.fromkeys(contacts))[:3],
                "url": f"https://t.me/{h}/{pid}"
            })
        if not ids:
            break
        before = min(ids)
    return out


def analyze_all() -> dict:
    raw = []
    with ThreadPoolExecutor(max_workers=7) as ex:
        for res in ex.map(fetch_posts, ALL_CHANNELS):
            raw.extend(res)

    seen = set()
    ads = []
    for a in raw:
        sig = re.sub(r"\W+", "", a["text"][:80]).lower()
        if sig not in seen:
            seen.add(sig)
            ads.append(a)

    buckets = {
        "direct_copy_scenario_iran": [],
        "diaspora_weak_ads_to_rewrite": [],
        "hidden_gem_auto_furniture": [],
        "hidden_gem_avatar_doctors_realtors": [],
        "hidden_gem_forms_ausbildung_ip": []
    }

    for a in ads:
        t = a["text"].lower()
        if "ایران" in a["region"]:
            if any(k in t for k in ["سناریو", "کپی", "تولید محتوا", "ادمین", "ریلز", "استوری", "بلاگر", "تبلیغ"]):
                buckets["direct_copy_scenario_iran"].append(a)
        else:
            # آگهی‌های تجاری ضعیف در کانال‌های خارج که پول تبلیغ داده‌اند اما متنشان خشک است
            if a["contacts"] and any(k in t for k in ["وام", "اجاره", "استخدام", "نیازمندیم", "سالن", "رستوران", "مغازه", "شراکت", "فروش"]):
                buckets["diaspora_weak_ads_to_rewrite"].append(a)
            # معدن پنهان خودرو/ون و فروش یکجای اثاثیه
            if any(k in t for k in ["ون ", "کامیونت", "ماشین", "خودرو", "وسایل منزل", "یخچال", "لباسشویی", "مبله"]):
                buckets["hidden_gem_auto_furniture"].append(a)
            # معدن پنهان پزشکان، روانشناسان، مشاوران املاک و کلینیک‌ها (مناسب آواتار هوش مصنوعی + سناریو)
            if any(k in t for k in ["روانشناس", "کلینیک", "پزشک", "ملک در دبی", "املاک", "مشاور", "وکیل", "اقامت"]):
                buckets["hidden_gem_avatar_doctors_realtors"].append(a)
            # معدن پنهان فرم‌های اداری، کمک‌هزینه، آوسبیلدونگ و آی‌پی ایران
            if any(k in t for k in ["آوسبیلدونگ", "ausbildung", "کمک‌هزینه", "بورسیه", "آی‌پی ایران", "قرارداد کاری", "anmeldung"]):
                buckets["hidden_gem_forms_ausbildung_ip"].append(a)

    return {
        "total_scanned": len(ads),
        "counts": {k: len(v) for k, v in buckets.items()},
        "samples": {k: v[:5] for k, v in buckets.items()}
    }


def format_telegram_copywriting_report() -> str:
    res = analyze_all()
    c = res["counts"]
    lines = [
        "✍️ <b>رادار زنده «کپی‌رایتینگ، سناریونویسی مستقیم و ۷ معدن پنهان دست‌به‌نقد»</b>",
        f"📊 اسکن زنده ۱۳ کانال ایران و خارج: <code>{res['total_scanned']}</code> آگهی یکتا",
        f"• تقاضای مستقیم سناریو/محتوا (ایران): <code>{c['direct_copy_scenario_iran']}</code>",
        f"• آگهی‌های تجاری ضعیف خارج (آماده بازنویسی یورویی): <code>{c['diaspora_weak_ads_to_rewrite']}</code>",
        f"• پزشکان/املاک خارج (مناسب آواتار AI + سناریو): <code>{c['hidden_gem_avatar_doctors_realtors']}</code>",
        f"• اثاثیه یکجا و خودرو اقساطی: <code>{c['hidden_gem_auto_furniture']}</code>\n",
        "🔥 <b>۱. شکارهای آماده سناریونویسی و کپی‌رایتینگ در ایران (@didogram / @doorkaari):</b>"
    ]
    for it in res["samples"]["direct_copy_scenario_iran"][:3]:
        lines.append(f"• [{it['region']}] {it['text'][:125]}... | <a href=\"{it['url']}\">لینک</a> | {it['contacts']}")

    lines.append("\n💶 <b>۲. شکارهای آماده بازنویسی آگهی و سناریوی ریلز در خارج (۱۰۰ تا ۲۵۰ یورو):</b>")
    for it in res["samples"]["diaspora_weak_ads_to_rewrite"][:3]:
        lines.append(f"• [{it['region']}] {it['text'][:125]}... | <a href=\"{it['url']}\">لینک</a> | {it['contacts']}")

    lines.append("\n💎 <b>۳. شکارهای معدن‌های پنهان (خودرو اقساطی، اثاثیه یکجا، آواتار پزشکان و فرم/IP):</b>")
    for it in (res["samples"]["hidden_gem_auto_furniture"][:2] + res["samples"]["hidden_gem_forms_ausbildung_ip"][:2]):
        lines.append(f"• [{it['region']}] {it['text'][:125]}... | <a href=\"{it['url']}\">لینک</a> | {it['contacts']}")

    return "\n".join(lines)


if __name__ == "__main__":
    print(format_telegram_copywriting_report())
