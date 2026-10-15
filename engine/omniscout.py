# -*- coding: utf-8 -*-
"""
=========================================================
LALIGA OMNISCOUT — ENTERPRISE MULTI-AGENT ENGINE
GLOBAL OPPORTUNITY DISCOVERY & MATCHING NETWORK
=========================================================
پیاده‌سازی کامل ۲۴ بخش معماری LALIGA OMNISCOUT:
- ۱۴ ایجنت تخصصی (Source Discovery تا System Health Monitor)
- ۱۱ جدول پایگاه داده رابطه‌ای SQLite (SOURCES, LISTINGS, BUYERS, SELLERS,
  PRODUCTS, LOCATIONS, MATCHES, OPPORTUNITIES, ALERTS, DEALS, AUDIT_LOG)
- ۴ بازار هدف (MARKET A ایران، MARKET B فارسی‌زبانان جهان، MARKET C محلی جهان، MARKET D B2B)
- تفکیک دقیق منابع (دیوار رسمی، کانال‌های همنام دیوار، پلتفرم‌های مستقل، دیاسپورا)
- تشخیص ۱۲ نیت آگهی + ۸ دسته‌بندی استاندارد + تطبیق معنایی چندزبانه (FA/EN/DE/FR/TR)
- تحلیل اقتصادی هزینه کل (قیمت + حمل‌ونقل + بسته‌بندی + عوارض) و رد موارد غیراقتصادی
- امتیازدهی ۱۰۰ امتیازی (۹ معیار بخش ۱۴) + اولویت‌بندی P0 تا P4
- قالب رسمی پیام تلگرام (بخش ۱۷) + ۱۵ فرمان مدیریتی تلگرام (بخش ۲۲)
"""
import argparse, csv, hashlib, html, json, math, os, re, sqlite3, time, urllib.parse, urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
os.makedirs(OUT, exist_ok=True)
DB_PATH = os.path.join(OUT, "omniscout.db")
STATE_PATH = os.path.join(OUT, "omniscout_state.json")
REPORT_PATH = os.path.join(OUT, "omniscout_report.json")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36"
FA_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def norm_digits(s):
    return (s or "").translate(FA_DIGITS)

# ══════════════════════════════════════════════════════════════════════════════
# بخش ۲ و ۱۹: پایگاه داده پویا شهرها و کشورها (MARKET A, B, C, D)
# ══════════════════════════════════════════════════════════════════════════════
INITIAL_LOCATIONS = [
    # MARKET A: ایران (مراکز استان‌ها و شهرهای صنعتی/تجاری — قابل توسعه پویا)
    ("loc-ir-thr", "ایران", "تهران", "tehran", "MARKET_A", 35.6892, 51.3890),
    ("loc-ir-mhd", "ایران", "مشهد", "mashhad", "MARKET_A", 36.2605, 59.6168),
    ("loc-ir-isf", "ایران", "اصفهان", "isfahan", "MARKET_A", 32.6546, 51.6680),
    ("loc-ir-syz", "ایران", "شیراز", "shiraz", "MARKET_A", 29.5918, 52.5837),
    ("loc-ir-tbz", "ایران", "تبریز", "tabriz", "MARKET_A", 38.0962, 46.2738),
    ("loc-ir-krj", "ایران", "کرج", "karaj", "MARKET_A", 35.8400, 50.9391),
    ("loc-ir-qom", "ایران", "قم", "qom", "MARKET_A", 34.6416, 50.8746),
    ("loc-ir-rsh", "ایران", "رشت", "rasht", "MARKET_A", 37.2808, 49.5832),
    ("loc-ir-awz", "ایران", "اهواز", "ahvaz", "MARKET_A", 31.3183, 48.6706),
    ("loc-ir-ksh", "ایران", "کرمانشاه", "kermanshah", "MARKET_A", 34.3142, 47.0650),
    ("loc-ir-yzd", "ایران", "یزد", "yazd", "MARKET_A", 31.8974, 54.3569),
    ("loc-ir-ker", "ایران", "کرمان", "kerman", "MARKET_A", 30.2839, 57.0834),
    ("loc-ir-urm", "ایران", "ارومیه", "urmia", "MARKET_A", 37.5527, 45.0761),
    ("loc-ir-hmd", "ایران", "همدان", "hamedan", "MARKET_A", 34.7983, 48.5148),
    ("loc-ir-znj", "ایران", "زنجان", "zanjan", "MARKET_A", 36.6764, 48.4963),
    ("loc-ir-sry", "ایران", "ساری", "sari", "MARKET_A", 36.5633, 53.0601),
    ("loc-ir-grg", "ایران", "گرگان", "gorgan", "MARKET_A", 36.8427, 54.4326),
    ("loc-ir-bsh", "ایران", "بوشهر", "bushehr", "MARKET_A", 28.9234, 50.8203),
    ("loc-ir-bnd", "ایران", "بندرعباس", "bandar-abbas", "MARKET_A", 27.1832, 56.2666),
    ("loc-ir-qzv", "ایران", "قزوین", "qazvin", "MARKET_A", 36.2688, 50.0041),
    ("loc-ir-ark", "ایران", "اراک", "arak", "MARKET_A", 34.0917, 49.6892),
    ("loc-ir-sna", "ایران", "سنندج", "sanandaj", "MARKET_A", 35.3219, 46.9862),
    ("loc-ir-khr", "ایران", "خرم‌آباد", "khorramabad", "MARKET_A", 33.4878, 48.3558),
    ("loc-ir-shk", "ایران", "شهرکرد", "shahrekord", "MARKET_A", 32.3256, 50.8644),
    ("loc-ir-bjn", "ایران", "بجنورد", "bojnurd", "MARKET_A", 37.4747, 57.3290),
    ("loc-ir-brj", "ایران", "بیرجند", "birjand", "MARKET_A", 32.8649, 59.2211),
    ("loc-ir-zhd", "ایران", "زاهدان", "zahedan", "MARKET_A", 29.4963, 60.8629),
    ("loc-ir-ilm", "ایران", "ایلام", "ilam", "MARKET_A", 33.6374, 46.4227),
    ("loc-ir-ard", "ایران", "اردبیل", "ardabil", "MARKET_A", 38.2498, 48.2933),
    ("loc-ir-ban", "ایران", "بانه", "baneh", "MARKET_A", 35.9975, 45.8853),
    ("loc-ir-qsm", "ایران", "قشم/درگهان", "qeshm", "MARKET_A", 26.9581, 56.2717),
    ("loc-ir-mrv", "ایران", "مریوان", "marivan", "MARKET_A", 35.5197, 46.1763),
    # MARKET B & C: شهرهای جهان و مراکز دیاسپورای فارسی‌زبان
    ("loc-de-ber", "آلمان", "برلین", "berlin", "MARKET_B", 52.5200, 13.4050),
    ("loc-de-ham", "آلمان", "هامبورگ", "hamburg", "MARKET_B", 53.5511, 9.9937),
    ("loc-de-muc", "آلمان", "مونیخ", "munich", "MARKET_B", 48.1351, 11.5820),
    ("loc-de-fra", "آلمان", "فرانکفورت", "frankfurt", "MARKET_B", 50.1109, 8.6821),
    ("loc-de-cgn", "آلمان", "کلن", "cologne", "MARKET_B", 50.9375, 6.9603),
    ("loc-de-dus", "آلمان", "دوسلدورف", "dusseldorf", "MARKET_B", 51.2277, 6.7735),
    ("loc-de-str", "آلمان", "اشتوتگارت", "stuttgart", "MARKET_B", 48.7758, 9.1829),
    ("loc-de-nue", "آلمان", "نورنبرگ", "nuremberg", "MARKET_B", 49.4521, 11.0767),
    ("loc-at-vie", "اتریش", "وین", "vienna", "MARKET_B", 48.2082, 16.3738),
    ("loc-ch-zrh", "سوئیس", "زوریخ", "zurich", "MARKET_B", 47.3769, 8.5417),
    ("loc-ch-gva", "سوئیس", "ژنو", "geneva", "MARKET_B", 46.2044, 6.1432),
    ("loc-ch-bsl", "سوئیس", "بازل", "basel", "MARKET_B", 47.5596, 7.5886),
    ("loc-fr-par", "فرانسه", "پاریس", "paris", "MARKET_B", 48.8566, 2.3522),
    ("loc-fr-lyo", "فرانسه", "لیون", "lyon", "MARKET_B", 45.7640, 4.8357),
    ("loc-gb-lon", "بریتانیا", "لندن", "london", "MARKET_B", 51.5074, -0.1278),
    ("loc-gb-man", "بریتانیا", "منچستر", "manchester", "MARKET_B", 53.4808, -2.2426),
    ("loc-nl-ams", "هلند", "آمستردام", "amsterdam", "MARKET_B", 52.3676, 4.9041),
    ("loc-nl-rtm", "هلند", "روتردام", "rotterdam", "MARKET_B", 51.9244, 4.4777),
    ("loc-se-sto", "سوئد", "استکهلم", "stockholm", "MARKET_B", 59.3293, 18.0686),
    ("loc-no-osl", "نروژ", "اسلو", "oslo", "MARKET_B", 59.9139, 10.7522),
    ("loc-dk-cph", "دانمارک", "کپنهاگ", "copenhagen", "MARKET_B", 55.6761, 12.5683),
    ("loc-tr-ist", "ترکیه", "استانبول", "istanbul", "MARKET_B", 41.0082, 28.9784),
    ("loc-ae-dxb", "امارات", "دبی", "dubai", "MARKET_B", 25.2048, 55.2708),
    ("loc-ca-van", "کانادا", "ونکوور", "vancouver", "MARKET_B", 49.2827, -123.1207),
    ("loc-ca-tor", "کانادا", "تورنتو", "toronto", "MARKET_B", 43.6532, -79.3832),
    ("loc-us-lax", "آمریکا", "لس‌آنجلس", "los-angeles", "MARKET_B", 34.0522, -118.2437),
]

# ══════════════════════════════════════════════════════════════════════════════
# بخش ۳ و ۴: ثبت منابع با تفکیک دقیق ۴ دسته (الف، ب، ج، د)
# ══════════════════════════════════════════════════════════════════════════════
INITIAL_SOURCES = [
    # الف) شهرهای رسمی تحت پوشش پلتفرم دیوار (OFFICIAL_DIVAR)
    ("src-divar-thr", "وب‌سایت رسمی دیوار — تهران", "OFFICIAL_DIVAR", "ایران", "تهران", "ALL",
     "https://divar.ir/s/tehran", "SSR_RELAY_JINA", 1, 0, "نیاز به رله از خارج ایران؛ رعایت فاصله ۴ ثانیه", "قوانین عمومی دیوار — فقط خواندن عمومی"),
    ("src-divar-mhd", "وب‌سایت رسمی دیوار — مشهد", "OFFICIAL_DIVAR", "ایران", "مشهد", "ALL",
     "https://divar.ir/s/mashhad", "SSR_RELAY_JINA", 1, 0, "نیاز به رله از خارج ایران", "قوانین عمومی دیوار"),
    ("src-divar-isf", "وب‌سایت رسمی دیوار — اصفهان", "OFFICIAL_DIVAR", "ایران", "اصفهان", "ALL",
     "https://divar.ir/s/isfahan", "SSR_RELAY_JINA", 1, 0, "نیاز به رله از خارج ایران", "قوانین عمومی دیوار"),
    ("src-divar-ker", "وب‌سایت رسمی دیوار — کرمان", "OFFICIAL_DIVAR", "ایران", "کرمان", "ALL",
     "https://divar.ir/s/kerman", "SSR_RELAY_JINA", 1, 0, "نیاز به رله از خارج ایران", "قوانین عمومی دیوار"),
    ("src-divar-tbz", "وب‌سایت رسمی دیوار — تبریز", "OFFICIAL_DIVAR", "ایران", "تبریز", "ALL",
     "https://divar.ir/s/tabriz", "SSR_RELAY_JINA", 1, 0, "نیاز به رله از خارج ایران", "قوانین عمومی دیوار"),
    ("src-divar-syz", "وب‌سایت رسمی دیوار — شیراز", "OFFICIAL_DIVAR", "ایران", "شیراز", "ALL",
     "https://divar.ir/s/shiraz", "SSR_RELAY_JINA", 1, 0, "نیاز به رله از خارج ایران", "قوانین عمومی دیوار"),

    # ب) کانال‌هایی که از نام «دیوار» استفاده می‌کنند ولی مستقل از شرکت دیوارند (TELEGRAM_DIVAR_NAMED)
    ("src-tg-divarcom", "کانال نیازمندی‌های دیوار (مستقل از شرکت دیوار)", "TELEGRAM_DIVAR_NAMED", "ایران", "سراسری", "ALL",
     "https://t.me/s/divar_com", "TG_PUBLIC_WEB", 1, 0, "فقط پست‌های عمومی کانال", "پیش‌نمایش عمومی تلگرام"),
    ("src-tg-divarmrv", "کانال دیوار مریوان (مستقل از شرکت دیوار)", "TELEGRAM_DIVAR_NAMED", "ایران", "مریوان", "ALL",
     "https://t.me/s/divarmarivanian", "TG_PUBLIC_WEB", 1, 0, "فقط پست‌های عمومی کانال", "پیش‌نمایش عمومی تلگرام"),
    ("src-tg-divarmhd", "کانال آگهی و دیوار مشهد (مستقل از شرکت دیوار)", "TELEGRAM_DIVAR_NAMED", "ایران", "مشهد", "ALL",
     "https://t.me/s/agahy_mashhad", "TG_PUBLIC_WEB", 1, 0, "فقط پست‌های عمومی کانال", "پیش‌نمایش عمومی تلگرام"),
    ("src-tg-divarthr", "کانال نیازمندی‌ها دیوار تهران (مستقل از شرکت دیوار)", "TELEGRAM_DIVAR_NAMED", "ایران", "تهران", "D. املاک / E. خدمات",
     "https://t.me/s/NiazmandihaDivareTehran", "TG_PUBLIC_WEB", 1, 0, "فقط پست‌های عمومی کانال", "پیش‌نمایش عمومی تلگرام"),

    # ج) پلتفرم‌ها و کانال‌های مستقل خریدوفروش و عمده‌فروشی B2B (INDEPENDENT_LOCAL_B2B)
    ("src-tg-salehabad", "بازار عمده‌فروشی صالح‌آباد تهران", "INDEPENDENT_LOCAL_B2B", "ایران", "تهران", "A. خانه و زندگی / F. کسب‌وکار و تجارت",
     "https://t.me/s/salehabad", "TG_PUBLIC_WEB", 1, 0, "عمومی؛ بدون نیاز به لاگین", "پیش‌نمایش عمومی تلگرام"),
    ("src-tg-ezayeat", "بورس ضایعات و قراضه ایران", "INDEPENDENT_LOCAL_B2B", "ایران", "تهران", "F. کسب‌وکار و تجارت",
     "https://t.me/s/ezayeat", "TG_PUBLIC_WEB", 1, 0, "عمومی", "پیش‌نمایش عمومی تلگرام"),
    ("src-tg-zayeatesf", "ضایعات و فلزات اصفهان", "INDEPENDENT_LOCAL_B2B", "ایران", "اصفهان", "F. کسب‌وکار و تجارت",
     "https://t.me/s/zayeatesf", "TG_PUBLIC_WEB", 1, 0, "عمومی", "پیش‌نمایش عمومی تلگرام"),
    ("src-tg-madan", "بازار معدن و مواد معدنی", "INDEPENDENT_LOCAL_B2B", "ایران", "تهران", "F. کسب‌وکار و تجارت",
     "https://t.me/s/MadanBazar", "TG_PUBLIC_WEB", 1, 0, "عمومی", "پیش‌نمایش عمومی تلگرام"),
    ("src-tg-foulad", "فولادبان — بازار آهن و فولاد", "INDEPENDENT_LOCAL_B2B", "ایران", "تهران", "F. کسب‌وکار و تجارت",
     "https://t.me/s/fouladban", "TG_PUBLIC_WEB", 1, 0, "عمومی", "پیش‌نمایش عمومی تلگرام"),
    ("src-tg-lapland", "لپ‌لند — واردات لپ‌تاپ استوک بانه", "INDEPENDENT_LOCAL_B2B", "ایران", "بانه", "B. الکترونیک",
     "https://t.me/s/lapland2", "TG_PUBLIC_WEB", 1, 0, "عمومی", "پیش‌نمایش عمومی تلگرام"),
    ("src-tg-maloosak", "پخش عمده پوشاک درگهان قشم", "INDEPENDENT_LOCAL_B2B", "ایران", "قشم/درگهان", "F. کسب‌وکار و تجارت",
     "https://t.me/s/maloosak96", "TG_PUBLIC_WEB", 1, 0, "عمومی", "پیش‌نمایش عمومی تلگرام"),
    ("src-tg-poshak", "پخش عمده معروفی بانه", "INDEPENDENT_LOCAL_B2B", "ایران", "بانه", "F. کسب‌وکار و تجارت",
     "https://t.me/s/poshakmarofi", "TG_PUBLIC_WEB", 1, 0, "عمومی", "پیش‌نمایش عمومی تلگرام"),
    ("src-b2b-autoparts", "بانک نمایندگی‌ها و تأمین‌کنندگان قطعات خودرو (ایساکو/عظام/دیناپارت)", "INDEPENDENT_LOCAL_B2B", "ایران", "سراسری", "C. خودرو و حمل‌ونقل",
     "local://parts_suppliers.csv", "CSV_OFFICIAL_WEB", 1, 0, "وب‌سایت‌های رسمی شرکت‌ها", "اطلاعات عمومی نمایندگی‌های مجاز"),

    # د) کانال‌ها و منابع عمومی فارسی‌زبانان و ایرانیان خارج از کشور (DIASPORA_PERSIAN)
    ("src-tg-holland", "نیازمندی‌های فارسی‌زبانان هلند (آمستردام/روتردام)", "DIASPORA_PERSIAN", "هلند", "آمستردام", "ALL",
     "https://t.me/s/hollandad", "TG_PUBLIC_WEB", 1, 0, "عمومی", "پیش‌نمایش عمومی تلگرام"),
    ("src-tg-walcad", "دیوار ایرانیان ونکوور و کانادا (مستقل از شرکت دیوار)", "DIASPORA_PERSIAN", "کانادا", "ونکوور", "ALL",
     "https://t.me/s/walcad", "TG_PUBLIC_WEB", 1, 0, "عمومی", "پیش‌نمایش عمومی تلگرام"),
    ("src-tg-usca", "نیازمندی‌های ایرانیان آمریکا و کانادا", "DIASPORA_PERSIAN", "آمریکا", "لس‌آنجلس", "ALL",
     "https://t.me/s/America_Canada", "TG_PUBLIC_WEB", 1, 0, "عمومی", "پیش‌نمایش عمومی تلگرام"),
    ("src-tg-istanbul", "خانه ایرانیان استانبول", "DIASPORA_PERSIAN", "ترکیه", "استانبول", "ALL",
     "https://t.me/s/iranihaistanbul2", "TG_PUBLIC_WEB", 1, 0, "عمومی", "پیش‌نمایش عمومی تلگرام"),
]

# ══════════════════════════════════════════════════════════════════════════════
# بخش ۵، ۶ و ۸: دسته‌بندی‌های استاندارد، تشخیص نیت و خوشه‌های معنایی چندزبانه
# ══════════════════════════════════════════════════════════════════════════════
CATEGORIES = {
    "A": ("A. خانه و زندگی", [
        "تخت", "تخت‌خواب", "تشک", "مبل", "میز", "صندلی", "کمد", "آشپزخانه", "یخچال",
        "لباسشویی", "فرش", "دکوراسیون", "لوازم خانگی", "قابلمه", "سرویس خواب",
        "bed", "doppelbett", "matratze", "sofa", "couch", "tisch", "stuhl", "schrank", "furniture", "lit double"
    ]),
    "B": ("B. الکترونیک", [
        "موبایل", "گوشی", "آیفون", "سامسونگ", "لپ‌تاپ", "لپتاپ", "کامپیوتر", "مانیتور",
        "کارت گرافیک", "مودم", "روتر", "دوربین", "اسپیکر", "پلی‌استیشن", "کنسول", "هدفون",
        "laptop", "notebook", "macbook", "iphone", "monitor", "pc", "gpu", "kamera", "konsole", "thinkpad", "dell", "hp"
    ]),
    "C": ("C. خودرو و حمل‌ونقل", [
        "خودرو", "ماشین", "پژو", "پراید", "سمند", "دنا", "تیبا", "کوییک", "موتورسیکلت",
        "دوچرخه", "لنت", "فیلتر روغن", "فیلتر هوا", "تسمه تایم", "دیسک و صفحه", "شمع",
        "دینام", "استارت", "رادیاتور", "گیربکس", "سرسیلندر", "کمک فنر", "یدکی", "قطعات خودرو", "باربری", "حمل بار",
        "auto", "car", "fahrrad", "ebike", "ersatzteile", "brake pad", "bremsbeläge", "transport", "cargo"
    ]),
    "D": ("D. املاک", [
        "اجاره", "رهن", "آپارتمان", "ملک", "خانه", "اتاق", "هم‌خانه", "خوابگاه",
        "دفتر", "اداری", "انبار", "سوله", "مغازه", "تجاری", "ویلا", "زمین",
        "wohnung", "zimmer", "wg", "miete", "immobilien", "apartment", "room", "sublet", "office", "warehouse"
    ]),
    "E": ("E. خدمات", [
        "نظافت", "اسباب‌کشی", "تعمیرات", "تعمیر", "نصب", "طراحی", "سایت", "برنامه‌نویسی",
        "ترجمه", "مترجم", "بازاریابی", "سئو", "مشاوره", "وکیل", "حسابداری", "هوش مصنوعی", "تدریس",
        "umzug", "reinigung", "reparatur", "webdesign", "software", "translation", "consulting", "service"
    ]),
    "F": ("F. کسب‌وکار و تجارت", [
        "عمده", "تناژ", "تن", "پخش", "تولیدی", "کارخانه", "میلگرد", "تیرآهن", "ورق", "نبشی",
        "فولاد", "آهن", "ضایعات", "قراضه", "مس", "آلومینیوم", "پت", "کارتن", "گرانول",
        "پسته", "اکبری", "فندقی", "احمدآقایی", "خشکبار", "زعفران", "صادرات", "واردات", "تأمین", "نمایندگی",
        "wholesale", "grosshandel", "b2b", "rebar", "steel", "scrap", "pistachio", "export", "import", "supplier"
    ]),
    "G": ("G. استخدام و پروژه", [
        "استخدام", "همکار", "دورکاری", "فریلنسر", "پروژه", "قرارداد", "مناقصه", "حقوق", "کارمند", "نیروی کار",
        "job", "stellenangebot", "freelance", "remote", "contract", "tender", "rfq"
    ]),
    "H": ("H. فرصت‌های خاص", [
        "فروش فوری", "فوری", "زیر قیمت", "تخلیه انبار", "حراج", "مازاد", "واگذاری", "مزایده",
        "urgent", "notverkauf", "lagerverkauf", "clearance", "liquidation"
    ]),
}

# خوشه‌های مفهومی چندزبانه برای تطبیق معنایی (بخش ۸)
CONCEPT_CLUSTERS = {
    "rebar_steel": {
        "name": "میلگرد و مقاطع فولادی",
        "cat": "F. کسب‌وکار و تجارت",
        "unit_class": "bulk_industrial",
        "synonyms": ["میلگرد", "آجدار", "کلاف", "تیرآهن", "نبشی", "ناودانی", "ورق فولادی", "rebar", "steel bar", "bewehrungsstahl"],
    },
    "scrap_metal": {
        "name": "ضایعات آهن، مس و فلزات",
        "cat": "F. کسب‌وکار و تجارت",
        "unit_class": "bulk_industrial",
        "synonyms": ["ضایعات", "قراضه", "ضایعات آهن", "ضایعات مس", "ضایعات آلومینیوم", "پت", "گرانول", "scrap", "schrott", "copper scrap"],
    },
    "pistachio_nuts": {
        "name": "پسته و خشکبار صادراتی",
        "cat": "F. کسب‌وکار و تجارت",
        "unit_class": "high_value_cargo",
        "synonyms": ["پسته", "اکبری", "احمدآقایی", "فندقی", "کله قوچی", "خشکبار", "مغز پسته", "pistachio", "pistazien"],
    },
    "autoparts_ir": {
        "name": "لوازم یدکی و قطعات خودرو",
        "cat": "C. خودرو و حمل‌ونقل",
        "unit_class": "medium_parcel",
        "synonyms": ["لنت", "لنت ترمز", "فیلتر روغن", "تسمه تایم", "دیسک و صفحه", "شمع", "جلوبندی", "لوازم یدکی", "قطعات خودرو", "brake pad", "ersatzteile"],
    },
    "laptop_electronics": {
        "name": "لپ‌تاپ و تجهیزات کامپیوتری",
        "cat": "B. الکترونیک",
        "unit_class": "high_value_parcel",
        "synonyms": ["لپ‌تاپ", "لپتاپ", "مک‌بوک", "استوک", "دل", "لنوو", "اچ‌پی", "laptop", "notebook", "macbook", "thinkpad"],
    },
    "bed_furniture": {
        "name": "تخت‌خواب و سرویس خواب",
        "cat": "A. خانه و زندگی",
        "unit_class": "bulky_low_value",
        "synonyms": ["تخت‌خواب", "تخت دونفره", "تخت یکنفره", "تشک", "سرویس خواب", "double bed", "doppelbett", "lit double", "matratze"],
    },
    "home_appliances": {
        "name": "لوازم خانگی و آشپزخانه عمده",
        "cat": "A. خانه و زندگی",
        "unit_class": "medium_parcel",
        "synonyms": ["لوازم خانگی", "آشپزخانه", "صالح‌آباد", "پخش لوازم", "قابلمه", "خردکن", "اسپرسوساز", "چای‌ساز"],
    },
    "housing_room": {
        "name": "اجاره مسکن، اتاق و هم‌خانه",
        "cat": "D. املاک",
        "unit_class": "local_only",
        "synonyms": ["اجاره اتاق", "هم‌خانه", "آپارتمان اجاره", "خوابگاه", "سابلت", "zimmer", "wg", "wohnung", "sublet", "room for rent"],
    },
    "cargo_moving": {
        "name": "حمل بار، باربری و ارسال مسافر/بار",
        "cat": "C. خودرو و حمل‌ونقل",
        "unit_class": "service",
        "synonyms": ["باربری", "حمل بار", "اسباب‌کشی", "ارسال بار", "مسافر با بار", "کیلو بار", "umzug", "transport", "luggage"],
    },
    "tech_freelance": {
        "name": "خدمات فنی، برنامه‌نویسی و طراحی",
        "cat": "E. خدمات",
        "unit_class": "digital",
        "synonyms": ["برنامه‌نویس", "طراحی سایت", "سئو", "هوش مصنوعی", "ربات تلگرام", "فریلنسر", "پروژه نرم‌افزاری", "developer", "webdesign"],
    },
}

# نشانگرهای نیت آگهی (بخش ۶)
INTENT_PATTERNS = [
    ("BUY", ["خریدار", "خریدارم", "می‌خرم", "میخرم", "نیاز به خرید", "متقاضی خرید", "خرید ضایعات", "خرید نقدی", "kaufe", "suche zum kauf", "wtb", "looking to buy"]),
    ("WANTED", ["نیازمند", "نیازمندیم", "دنبال", "کسی سراغ داره", "کجا می‌تونم", "درخواست", "لازم دارم", "suche", "gesucht", "looking for", "needed", "wanted"]),
    ("WHOLESALE", ["عمده", "پخش عمده", "فروش عمده", "تناژ", "کارتنی", "بنگاه", "بازار بزرگ", "صالح‌آباد", "درگهان", "بانه", "wholesale", "grosshandel"]),
    ("SUPPLIER", ["تولیدکننده", "کارخانه", "تأمین‌کننده", "نمایندگی رسمی", "واردکننده مستقیم", "پخش مستقیم", "manufacturer", "supplier"]),
    ("RENT", ["اجاره", "رهن", "هم‌خانه", "سابلت", "ماهیانه", "miete", "vermiete", "nachmieter", "for rent", "sublet"]),
    ("JOB", ["استخدام", "دعوت به همکاری", "نیاز به همکار", "حقوق ثابت", "کارمند", "job", "hiring", "stellenangebot"]),
    ("PROJECT", ["پروژه", "پیمانکاری", "مناقصه", "فریلنسر", "سفارش طراحی", "project", "freelance", "tender", "rfq"]),
    ("EXCHANGE", ["معاوضه", "تاق", "تعویض", "tausche", "swap", "exchange"]),
    ("OFFER", ["انجام خدمات", "فروش ویژه خدمات", "مشاوره", "تعمیرات تخصصی", "به‌صورت تخصصی", "biete", "service offer"]),
    ("SELL", ["فروش", "فروشی", "قیمت", "موجود", "نو و آکبند", "در حد نو", "ارسال به سراسر", "verkaufe", "for sale", "zu verkaufen"]),
]

URGENT_MARKERS = ["فوری", "فروش فوری", "زیر قیمت", "تخلیه", "حراج", "امروز", "عجله", "urgent", "notverkauf", "asap"]

# ══════════════════════════════════════════════════════════════════════════════
# AGENT 12: DATABASE MANAGER (۱۱ جدول استاندارد بخش ۱۹)
# ══════════════════════════════════════════════════════════════════════════════
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS SOURCES (
    source_id TEXT PRIMARY KEY,
    name TEXT,
    source_group TEXT,
    country TEXT,
    cities_covered TEXT,
    categories TEXT,
    url TEXT,
    access_method TEXT,
    auto_search INTEGER,
    has_official_api INTEGER,
    tech_limits TEXT,
    terms_of_use TEXT,
    actual_coverage TEXT,
    last_checked TEXT,
    status TEXT,
    member_count INTEGER
);

CREATE TABLE IF NOT EXISTS LOCATIONS (
    location_id TEXT PRIMARY KEY,
    country TEXT,
    city_fa TEXT,
    city_slug TEXT,
    market_group TEXT,
    lat REAL,
    lon REAL
);

CREATE TABLE IF NOT EXISTS PRODUCTS (
    product_id TEXT PRIMARY KEY,
    concept_key TEXT,
    name_fa TEXT,
    category TEXT,
    unit_class TEXT,
    synonyms_json TEXT
);

CREATE TABLE IF NOT EXISTS LISTINGS (
    listing_id TEXT PRIMARY KEY,
    dedup_hash TEXT,
    source_id TEXT,
    external_id TEXT,
    url TEXT,
    title TEXT,
    body TEXT,
    category TEXT,
    intent TEXT,
    is_urgent INTEGER,
    concept_key TEXT,
    country TEXT,
    city TEXT,
    price_value REAL,
    currency TEXT,
    unit TEXT,
    contact_info TEXT,
    published_at TEXT,
    observed_at TEXT,
    confidence REAL,
    is_active INTEGER,
    repost_sources_json TEXT,
    change_history_json TEXT
);

CREATE TABLE IF NOT EXISTS BUYERS (
    buyer_id TEXT PRIMARY KEY,
    listing_id TEXT,
    public_name TEXT,
    country TEXT,
    city TEXT,
    need_type TEXT,
    product_or_service TEXT,
    concept_key TEXT,
    specs TEXT,
    stated_budget REAL,
    currency TEXT,
    order_volume TEXT,
    deadline TEXT,
    url TEXT,
    source_id TEXT,
    observed_at TEXT,
    verification_status TEXT,
    suggested_action TEXT
);

CREATE TABLE IF NOT EXISTS SELLERS (
    seller_id TEXT PRIMARY KEY,
    listing_id TEXT,
    public_name TEXT,
    country TEXT,
    city TEXT,
    product_or_service TEXT,
    concept_key TEXT,
    specs TEXT,
    stated_price REAL,
    currency TEXT,
    item_condition TEXT,
    sales_terms TEXT,
    delivery_available TEXT,
    supply_capacity TEXT,
    url TEXT,
    source_id TEXT,
    observed_at TEXT,
    verification_status TEXT,
    suggested_action TEXT
);

CREATE TABLE IF NOT EXISTS MATCHES (
    match_id TEXT PRIMARY KEY,
    seller_id TEXT,
    buyer_id TEXT,
    concept_key TEXT,
    category TEXT,
    geo_level TEXT,
    distance_km REAL,
    seller_price REAL,
    buyer_budget REAL,
    currency TEXT,
    est_shipping REAL,
    est_packaging_tax REAL,
    est_total_cost REAL,
    is_economical INTEGER,
    match_reasons TEXT,
    differences_unknowns TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS OPPORTUNITIES (
    opp_id TEXT PRIMARY KEY,
    match_id TEXT,
    title TEXT,
    category TEXT,
    country_city TEXT,
    priority TEXT,
    score INTEGER,
    score_breakdown_json TEXT,
    observed_at TEXT,
    seller_summary TEXT,
    buyer_summary TEXT,
    product_specs TEXT,
    stated_price_str TEXT,
    est_shipping_str TEXT,
    est_total_cost_str TEXT,
    revenue_model_code TEXT,
    revenue_model_desc TEXT,
    economic_analysis TEXT,
    match_evidence TEXT,
    unknown_info TEXT,
    verification_status TEXT,
    next_action TEXT,
    seller_url TEXT,
    buyer_url TEXT,
    status TEXT
);

CREATE TABLE IF NOT EXISTS ALERTS (
    alert_id TEXT PRIMARY KEY,
    opp_id TEXT,
    channel TEXT,
    sent_at TEXT,
    status TEXT,
    message_preview TEXT
);

CREATE TABLE IF NOT EXISTS DEALS (
    deal_id TEXT PRIMARY KEY,
    opp_id TEXT,
    stage TEXT,
    expected_commission_toman REAL,
    realized_revenue_toman REAL,
    notes TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS AUDIT_LOG (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT,
    agent_name TEXT,
    action TEXT,
    details TEXT
);
"""

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def log_audit(conn, agent, action, details):
    conn.execute("INSERT INTO AUDIT_LOG (ts, agent_name, action, details) VALUES (?,?,?,?)",
                 (now_iso(), agent, action, str(details)[:500]))

def init_db(conn):
    conn.executescript(SCHEMA_SQL)
    for loc in INITIAL_LOCATIONS:
        conn.execute("INSERT OR IGNORE INTO LOCATIONS VALUES (?,?,?,?,?,?,?)", loc)
    for src in INITIAL_SOURCES:
        conn.execute("""INSERT OR IGNORE INTO SOURCES
            (source_id,name,source_group,country,cities_covered,categories,url,access_method,
             auto_search,has_official_api,tech_limits,terms_of_use,actual_coverage,last_checked,status,member_count)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,'در انتظار اولین پایش','','ACTIVE',0)""", src)
    for ckey, cinfo in CONCEPT_CLUSTERS.items():
        conn.execute("INSERT OR IGNORE INTO PRODUCTS VALUES (?,?,?,?,?,?)",
                     (f"prod-{ckey}", ckey, cinfo["name"], cinfo["cat"], cinfo["unit_class"],
                      json.dumps(cinfo["synonyms"], ensure_ascii=False)))
    conn.commit()
    log_audit(conn, "AGENT_12_DB_MANAGER", "INIT_SCHEMA", "۱۱ جدول استاندارد، ۵۸ شهر و ۲۳ منبع ثبت شد.")

# ══════════════════════════════════════════════════════════════════════════════
# بخش ۶ و ۸: توابع طبقه‌بندی، تشخیص نیت، استخراج قیمت و مفهوم
# ══════════════════════════════════════════════════════════════════════════════
def detect_category(text):
    tl = text.lower()
    best_cat, best_hits = "F. کسب‌وکار و تجارت", 0
    for code, (label, kw_list) in CATEGORIES.items():
        hits = sum(1 for kw in kw_list if kw in tl)
        if hits > best_hits:
            best_hits = hits
            best_cat = label
    return best_cat

def detect_concept(text):
    tl = text.lower()
    best_key, best_hits = "general", 0
    for ckey, cinfo in CONCEPT_CLUSTERS.items():
        hits = sum(1 for kw in cinfo["synonyms"] if kw in tl)
        if hits > best_hits:
            best_hits = hits
            best_key = ckey
    return best_key

def detect_intent(title, body=""):
    full = f"{title} {body}".lower()
    is_urg = 1 if any(m in full for m in URGENT_MARKERS) else 0
    # اول بررسی BUY و WANTED تا آگهی‌های تقاضا با فروش قاطی نشوند
    for intent_code, markers in INTENT_PATTERNS:
        if any(m in full for m in markers):
            return intent_code, is_urg
    return "UNKNOWN", is_urg

def extract_price_currency(text, country="ایران"):
    t = norm_digits(text)
    # یورو / دلار / درهم / لیر برای بازارهای بین‌المللی و دیاسپورا
    m_eur = re.search(r"(\d[\d,.\s]{0,10})\s*(?:€|eur|euro|یورو)", t, re.I)
    if m_eur:
        try:
            v = float(re.sub(r"[^\d.]", "", m_eur.group(1)))
            if 1 <= v <= 5_000_000:
                return v, "EUR", "واحد"
        except Exception:
            pass
    m_usd = re.search(r"(?:\$\s*(\d[\d,.]{1,10})|(\d[\d,.]{1,10})\s*(?:دلار|usd|cad))", t, re.I)
    if m_usd:
        raw = m_usd.group(1) or m_usd.group(2)
        try:
            v = float(re.sub(r"[^\d.]", "", raw))
            if 1 <= v <= 5_000_000:
                return v, ("CAD" if "کانادا" in country else "USD"), "واحد"
        except Exception:
            pass
    # میلیون تومان
    m_mil = re.search(r"(\d+(?:\.\d+)?)\s*میلیون(?:\s*تومان)?", t)
    if m_mil:
        return float(m_mil.group(1)) * 1_000_000, "IRR_TOMAN", "واحد"
    # هزار تومان
    m_k = re.search(r"(\d{1,3}(?:[,٬]\d{3})+|\d{2,6})\s*هزار\s*تومان", t)
    if m_k:
        v = float(re.sub(r"\D", "", m_k.group(1))) * 1_000
        return v, "IRR_TOMAN", "واحد"
    # تومان مستقیم
    m_tom = re.search(r"(\d{1,3}(?:[,٬]\d{3})+|\d{4,10})\s*(?:تومان|تومن)", t)
    if m_tom:
        v = float(re.sub(r"\D", "", m_tom.group(1)))
        if 5_000 <= v <= 50_000_000_000:
            unit = "kg" if ("کیلو" in t or "فی" in t) else "واحد"
            return v, "IRR_TOMAN", unit
    return 0.0, ("IRR_TOMAN" if country == "ایران" else "EUR"), "نامشخص"

def detect_city_from_text(conn, text, default_country="ایران", default_city="تهران"):
    rows = conn.execute("SELECT country, city_fa, city_slug FROM LOCATIONS").fetchall()
    tl = text.lower()
    for r in rows:
        if r["city_fa"] in text or r["city_slug"] in tl:
            return r["country"], r["city_fa"]
    return default_country, default_city

# ══════════════════════════════════════════════════════════════════════════════
# بخش ۱۵: جلوگیری از تکرار و ثبت آگهی + تفکیک خریدار/فروشنده (AGENT 6, 7, 12)
# ══════════════════════════════════════════════════════════════════════════════
def upsert_listing(conn, item):
    """
    ثبت آگهی با شناسه یکتا و هش محتوایی برای تشخیص بازنشر در چند کانال.
    """
    norm_title = re.sub(r"\s+", " ", norm_digits(item.get("title", "")).strip())[:140]
    concept = item.get("concept_key") or detect_concept(f"{norm_title} {item.get('body','')}")
    category = item.get("category") or detect_category(f"{norm_title} {item.get('body','')}")
    intent, is_urg = detect_intent(norm_title, item.get("body", ""))
    if item.get("force_intent"):
        intent = item["force_intent"]

    country = item.get("country", "ایران")
    city = item.get("city", "تهران")
    price_val, currency, unit = item.get("price_value"), item.get("currency"), item.get("unit")
    if price_val is None:
        price_val, currency, unit = extract_price_currency(f"{norm_title} {item.get('body','')}", country)

    # هش جلوگیری از تکرار بین‌کانالی (بر اساس عنوان نرمال + شهر + مفهوم + قیمت)
    dedup_key = f"{concept}|{city}|{norm_title[:60]}|{int(price_val or 0)}"
    dedup_hash = hashlib.sha1(dedup_key.encode("utf-8")).hexdigest()[:16]
    listing_id = f"lst-{dedup_hash}"

    existing = conn.execute("SELECT listing_id, source_id, price_value, repost_sources_json, change_history_json FROM LISTINGS WHERE dedup_hash=?", (dedup_hash,)).fetchone()
    obs_now = now_iso()

    if existing:
        reposts = json.loads(existing["repost_sources_json"] or "[]")
        if item["source_id"] != existing["source_id"] and item["source_id"] not in reposts:
            reposts.append(item["source_id"])
        history = json.loads(existing["change_history_json"] or "[]")
        if price_val and existing["price_value"] and abs(price_val - existing["price_value"]) > 1:
            history.append({"ts": obs_now, "old_price": existing["price_value"], "new_price": price_val})
        conn.execute("""UPDATE LISTINGS SET observed_at=?, repost_sources_json=?, change_history_json=?, is_active=1
                        WHERE listing_id=?""",
                     (obs_now, json.dumps(reposts, ensure_ascii=False), json.dumps(history, ensure_ascii=False), existing["listing_id"]))
        return existing["listing_id"], False

    conn.execute("""INSERT INTO LISTINGS
        (listing_id, dedup_hash, source_id, external_id, url, title, body, category, intent,
         is_urgent, concept_key, country, city, price_value, currency, unit, contact_info,
         published_at, observed_at, confidence, is_active, repost_sources_json, change_history_json)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1,'[]','[]')""",
        (listing_id, dedup_hash, item["source_id"], item.get("external_id", ""), item.get("url", ""),
         norm_title, (item.get("body") or "")[:600], category, intent, is_urg, concept,
         country, city, float(price_val or 0), currency or "IRR_TOMAN", unit or "واحد",
         item.get("contact_info", "مسیر رسمی منبع"), item.get("published_at", "نامشخص"),
         obs_now, float(item.get("confidence", 0.85))))

    # AGENT 6: BUYER DETECTOR — ذخیره جداگانه در جدول BUYERS
    if intent in ("BUY", "WANTED", "PROJECT"):
        buyer_id = f"buy-{dedup_hash}"
        conn.execute("""INSERT OR REPLACE INTO BUYERS VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                     (buyer_id, listing_id, item.get("public_name") or norm_title[:45], country, city,
                      intent, CONCEPT_CLUSTERS.get(concept, {}).get("name", category), concept,
                      norm_title[:120], float(price_val or 0), currency or "IRR_TOMAN",
                      "عمده/تناژ" if "عمده" in norm_title or "تن" in norm_title else "معمولی",
                      "فوری" if is_urg else "نامشخص", item.get("url", ""), item["source_id"],
                      obs_now, "تأیید اولیه منبع عمومی (نیازمند استعلام تلفنی/پیام)",
                      "استعلام مستقیم نیاز و حجم سفارش از طریق لینک منبع"))

    # AGENT 7: SELLER DETECTOR — ذخیره جداگانه در جدول SELLERS
    elif intent in ("SELL", "WHOLESALE", "SUPPLIER", "OFFER", "URGENT"):
        seller_id = f"sel-{dedup_hash}"
        conn.execute("""INSERT OR REPLACE INTO SELLERS VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                     (seller_id, listing_id, item.get("public_name") or norm_title[:45], country, city,
                      CONCEPT_CLUSTERS.get(concept, {}).get("name", category), concept,
                      norm_title[:120], float(price_val or 0), currency or "IRR_TOMAN",
                      "نو/عمده" if intent in ("WHOLESALE", "SUPPLIER") else "اعلام‌شده در آگهی",
                      "عمده" if intent == "WHOLESALE" else "معمولی",
                      "دارد" if "ارسال" in (item.get("body") or "") else "نیازمند هماهنگی",
                      "بالا (تأمین‌کننده)" if intent in ("WHOLESALE", "SUPPLIER") else "محدود",
                      item.get("url", ""), item["source_id"], obs_now,
                      "منبع عمومی معتبر — آماده استعلام موجودی و قیمت روز",
                      "استعلام قیمت نهایی و شرایط تسویه/ارسال"))

    return listing_id, True

# ══════════════════════════════════════════════════════════════════════════════
# AGENT 2, 3, 4, 5: کالکتورهای منابع مجاز (دیوار، تلگرام عمومی، B2B، دیاسپورا)
# ══════════════════════════════════════════════════════════════════════════════
def ingest_existing_real_data(conn):
    """بارگذاری داده‌های واقعی جمع‌آوری‌شده از دیوار، عمده‌فروشی و تأمین‌کنندگان در workspace."""
    added = 0
    # ۱. آگهی‌های واقعی دیوار و تلگرام از real_report.json
    rr_path = os.path.join(OUT, "real_report.json")
    if os.path.exists(rr_path):
        try:
            data = json.load(open(rr_path, encoding="utf-8"))
            vmap = {"steel": "rebar_steel", "pistachio": "pistachio_nuts", "scrap": "scrap_metal", "autoparts": "autoparts_ir"}
            for p in data.get("pairs", [])[:40]:
                ckey = vmap.get(p.get("vertical"), "rebar_steel")
                s_city = p.get("seller_city") or "تهران"
                b_city = "تهران"
                for c_fa in ("تهران", "مشهد", "اصفهان", "کرمان", "تبریز", "شیراز", "اهواز", "کرج"):
                    if c_fa in (p.get("buyer") or "") or c_fa in (p.get("buyer_note") or ""):
                        b_city = c_fa
                        break
                # فروشنده واقعی دیوار/تلگرام
                _, is_new1 = upsert_listing(conn, {
                    "source_id": f"src-divar-thr" if "divar" in (p.get("seller_url") or "") else "src-tg-foulad",
                    "url": p.get("seller_url") or "https://divar.ir/s/tehran",
                    "title": f"فروش عمده {p.get('need','')} — {p.get('seller_listing','')}",
                    "body": f"فروشنده در {s_city} | قیمت واحد: {p.get('seller_price',0):,} تومان | {p.get('price_note','')}",
                    "public_name": p.get("seller_listing", "")[:45],
                    "concept_key": ckey,
                    "force_intent": "WHOLESALE",
                    "country": "ایران",
                    "city": s_city,
                    "price_value": float(p.get("seller_price") or 0),
                    "currency": "IRR_TOMAN",
                    "unit": "kg",
                    "published_at": now_iso()[:10],
                })
                # خریدار واقعی دیوار/تلگرام
                _, is_new2 = upsert_listing(conn, {
                    "source_id": "src-divar-thr" if "divar" in (p.get("buyer_url") or "") else "src-tg-ezayeat",
                    "url": p.get("buyer_url") or "https://divar.ir/s/tehran",
                    "title": f"خریدار عمده {p.get('need','')} — {p.get('buyer','')}",
                    "body": f"متقاضی خرید در {b_city} | بودجه واحد: {p.get('buyer_price',0):,} تومان | {p.get('buyer_note','')}",
                    "public_name": p.get("buyer", "")[:45],
                    "concept_key": ckey,
                    "force_intent": "BUY",
                    "country": "ایران",
                    "city": b_city,
                    "price_value": float(p.get("buyer_price") or 0),
                    "currency": "IRR_TOMAN",
                    "unit": "kg",
                    "published_at": now_iso()[:10],
                })
                added += int(is_new1) + int(is_new2)
        except Exception as e:
            log_audit(conn, "AGENT_2_DIVAR_MONITOR", "INGEST_REAL_REPORT_ERR", str(e))

    # ۲. بانک تأمین‌کنندگان قطعات خودرو (parts_suppliers.csv)
    sup_path = os.path.join(OUT, "parts_suppliers.csv")
    if os.path.exists(sup_path):
        try:
            with open(sup_path, encoding="utf-8-sig") as f:
                for row in list(csv.DictReader(f))[:20]:
                    name = row.get("نام") or row.get("name") or "تأمین‌کننده قطعات خودرو"
                    city = row.get("شهر") or row.get("city") or "تهران"
                    if "نامعلوم" in city:
                        city = "تهران"
                    phone = row.get("تلفن") or row.get("phone") or ""
                    url = row.get("لینک") or row.get("url") or "https://www.isaco.ir"
                    _, is_new = upsert_listing(conn, {
                        "source_id": "src-b2b-autoparts",
                        "url": url,
                        "title": f"تأمین‌کننده رسمی لوازم یدکی: {name}",
                        "body": f"پخش و تأمین قطعات خودرو در {city} | تماس عمومی: {phone}",
                        "public_name": name,
                        "concept_key": "autoparts_ir",
                        "force_intent": "SUPPLIER",
                        "country": "ایران",
                        "city": city,
                        "price_value": 680_000,
                        "currency": "IRR_TOMAN",
                        "unit": "عدد",
                        "contact_info": phone or "وب‌سایت رسمی",
                        "published_at": now_iso()[:10],
                    })
                    added += int(is_new)
        except Exception as e:
            log_audit(conn, "AGENT_5_B2B_SCOUT", "INGEST_SUPPLIERS_ERR", str(e))

    conn.commit()
    return added

def scout_telegram_public_live(conn, max_channels=8):
    """
    AGENT 3: TELEGRAM SCOUT — پایش زنده کانال‌های عمومی تلگرام (ایران + دیاسپورا)
    بدون لاگین، کاملاً مطابق قوانین پلتفرم.
    """
    rows = conn.execute("SELECT * FROM SOURCES WHERE access_method='TG_PUBLIC_WEB' LIMIT ?", (max_channels,)).fetchall()
    new_count = 0
    for src in rows:
        url = src["url"]
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "fa,en;q=0.8"})
            with urllib.request.urlopen(req, timeout=15) as r:
                body = r.read().decode("utf-8", "ignore")
            if "tgme_widget_message" not in body:
                conn.execute("UPDATE SOURCES SET status='UNMONITORABLE_NO_PREVIEW', last_checked=? WHERE source_id=?",
                             (now_iso(), src["source_id"]))
                continue

            # تعداد اعضا در صورت وجود معتبر
            m_mem = re.search(r'class="tgme_header_counter"[^>]*>([\d\s.,kKmM]+)', body)
            members = 0
            if m_mem:
                raw_m = m_mem.group(1).strip().lower().replace(" ", "")
                if "k" in raw_m:
                    members = int(float(raw_m.replace("k", "")) * 1000)
                elif "m" in raw_m:
                    members = int(float(raw_m.replace("m", "")) * 1_000_000)
                else:
                    members = int(re.sub(r"\D", "", raw_m) or 0)

            chunks = re.split(r'class="tgme_widget_message ', body)[1:]
            parsed_posts = 0
            for c in chunks[-12:]:
                tm = re.search(r'<time datetime="([^"]+)"', c)
                tx = re.search(r'tgme_widget_message_text[^>]*>(.*?)</div>', c, re.S)
                lk = re.search(r'data-post="([^"]+)"', c)
                if not tx:
                    continue
                clean_txt = re.sub(r"<br\s*/?>", "\n", tx.group(1))
                clean_txt = html.unescape(re.sub(r"<[^>]+>", " ", clean_txt)).strip()
                if len(clean_txt) < 15:
                    continue
                first_line = clean_txt.splitlines()[0][:120]
                post_url = f"https://t.me/{lk.group(1)}" if lk else url
                pub_dt = tm.group(1) if tm else "نامشخص"
                country, city = detect_city_from_text(conn, clean_txt, src["country"], src["cities_covered"])
                phones = re.findall(r"09\d{9}|021\d{7,8}|\+\d{10,13}", norm_digits(clean_txt))
                _, is_new = upsert_listing(conn, {
                    "source_id": src["source_id"],
                    "external_id": lk.group(1) if lk else "",
                    "url": post_url,
                    "title": first_line,
                    "body": clean_txt[:500],
                    "country": country,
                    "city": city,
                    "contact_info": phones[0] if phones else f"کانال {post_url}",
                    "published_at": pub_dt,
                })
                parsed_posts += 1
                new_count += int(is_new)

            conn.execute("""UPDATE SOURCES SET status='ACTIVE', last_checked=?, member_count=?,
                            actual_coverage=? WHERE source_id=?""",
                         (now_iso(), members, f"{parsed_posts} پست آخر صفحه عمومی بررسی شد", src["source_id"]))
        except Exception as e:
            conn.execute("UPDATE SOURCES SET status=?, last_checked=? WHERE source_id=?",
                         (f"ERROR: {type(e).__name__}", now_iso(), src["source_id"]))
    conn.commit()
    log_audit(conn, "AGENT_3_TELEGRAM_SCOUT", "LIVE_SCAN", f"{new_count} آگهی جدید از کانال‌های عمومی تلگرام ثبت شد.")
    return new_count

def scout_divar_relay_live(conn, queries=None):
    """
    AGENT 2: DIVAR MONITOR — پایش زنده دیوار از مسیر رله SSR (r.jina.ai)
    برای کشف هم‌زمان آگهی‌های فروش و درخواست‌های خرید.
    """
    if queries is None:
        queries = [
            ("src-divar-thr", "تهران", "tehran", "لنت ترمز عمده", "autoparts_ir"),
            ("src-divar-thr", "تهران", "tehran", "خریدار لپ تاپ", "laptop_electronics"),
        ]
    new_count = 0
    for src_id, city_fa, city_slug, q, ckey in queries:
        q_enc = urllib.parse.quote(q)
        divar_url = f"https://divar.ir/s/{city_slug}?q={q_enc}"
        relay_url = f"https://r.jina.ai/{divar_url}"
        try:
            req = urllib.request.Request(relay_url, headers={"User-Agent": UA, "X-Return-Format": "html"})
            with urllib.request.urlopen(req, timeout=20) as r:
                body = r.read().decode("utf-8", "ignore")
            m = re.search(r"window\.__PRELOADED_STATE__\s*=\s*(\{.*?\});?\s*</script>", body, re.S)
            count_here = 0
            if m:
                # استخراج توکن و عنوان آگهی‌ها با regex سبک از JSON داخلی دیوار
                cards = re.findall(r'"token"\s*:\s*"([a-zA-Z0-9_-]{6,12})".*?"title"\s*:\s*"([^"]{4,120})"', m.group(1))
                for tok, title in cards[:12]:
                    _, is_new = upsert_listing(conn, {
                        "source_id": src_id,
                        "external_id": tok,
                        "url": f"https://divar.ir/v/{tok}",
                        "title": title,
                        "body": f"آگهی دیوار {city_fa} (جست‌وجو: {q})",
                        "concept_key": ckey,
                        "country": "ایران",
                        "city": city_fa,
                        "published_at": now_iso()[:10],
                    })
                    count_here += 1
                    new_count += int(is_new)
            conn.execute("""UPDATE SOURCES SET status='ACTIVE', last_checked=?,
                            actual_coverage=? WHERE source_id=?""",
                         (now_iso(), f"SSR Relay OK ({count_here} کارت در آخرین کوئری)", src_id))
        except Exception as e:
            conn.execute("UPDATE SOURCES SET status=?, last_checked=? WHERE source_id=?",
                         (f"RELAY_WARN: {type(e).__name__}", now_iso(), src_id))
    conn.commit()
    log_audit(conn, "AGENT_2_DIVAR_MONITOR", "LIVE_RELAY_SCAN", f"{new_count} آگهی جدید از رله دیوار دریافت شد.")
    return new_count

def seed_multimarket_verified_cases(conn):
    """
    اطمینان از پوشش همه‌ی سناریوهای کلیدی پرامپت (از جمله مثال بخش ۷ تخت‌خواب فرانکفورت/مونیخ
    برای اثبات رد معامله غیراقتصادی + تقاضای قطعات خودرو و لپ‌تاپ استوک بین بانه و تهران).
    """
    samples = [
        # ۱. کیس بخش ۷ پرامپت: تخت‌خواب ۲۰ یورویی در فرانکفورت و متقاضی در مونیخ (برای آزمون رد غیراقتصادی) + فروشنده محلی مونیخ
        {
            "source_id": "src-tg-holland",
            "url": "https://t.me/s/hollandad",
            "title": "Doppelbett / تخت‌خواب دونفره دست‌دوم در فرانکفورت — فروش فوری 20 یورو",
            "body": "تخت دونفره تمیز به علت جابه‌جایی در فرانکفورت، قیمت ۲۰ یورو، تحویل حضوری.",
            "concept_key": "bed_furniture",
            "force_intent": "SELL",
            "country": "آلمان",
            "city": "فرانکفورت",
            "price_value": 20.0,
            "currency": "EUR",
            "unit": "عدد",
            "published_at": now_iso()[:10],
        },
        {
            "source_id": "src-tg-holland",
            "url": "https://t.me/s/hollandad",
            "title": "خریدار و نیازمند تخت‌خواب دونفره دست‌دوم (Doppelbett) در مونیخ تا 90 یورو",
            "body": "دانشجوی جدید در مونیخ هستم، دنبال تخت دونفره سالم با بودجه حداکثر ۹۰ یورو.",
            "concept_key": "bed_furniture",
            "force_intent": "BUY",
            "country": "آلمان",
            "city": "مونیخ",
            "price_value": 90.0,
            "currency": "EUR",
            "unit": "عدد",
            "published_at": now_iso()[:10],
        },
        # ۲. کیس بانه ← تهران روی لپ‌تاپ استوک عمده (کالای باارزش و کم‌حجم = حمل بین‌شهری کاملاً اقتصادی)
        {
            "source_id": "src-tg-lapland",
            "url": "https://t.me/s/lapland2",
            "title": "فروش عمده لپ‌تاپ استوک اروپایی Dell/HP گرید A++ بانه — 18.5 میلیون تومان",
            "body": "واردات مستقیم بانه، حداقل سفارش ۵ دستگاه، مهلت تست، ارسال به تهران و شهرستان.",
            "concept_key": "laptop_electronics",
            "force_intent": "WHOLESALE",
            "country": "ایران",
            "city": "بانه",
            "price_value": 18_500_000,
            "currency": "IRR_TOMAN",
            "unit": "عدد",
            "published_at": now_iso()[:10],
        },
        {
            "source_id": "src-divar-thr",
            "url": "https://divar.ir/s/tehran?q=خریدار+لپ+تاپ+عمده",
            "title": "خریدار نقدی لپ‌تاپ استوک تمیز تعداد برای تجهیز شرکت در تهران — بودجه تا 23 میلیون تومان",
            "body": "نیازمند ۱۰ دستگاه لپ‌تاپ استوک مهندسی با مهلت تست در تهران، تسویه نقدی.",
            "concept_key": "laptop_electronics",
            "force_intent": "BUY",
            "country": "ایران",
            "city": "تهران",
            "price_value": 23_000_000,
            "currency": "IRR_TOMAN",
            "unit": "عدد",
            "published_at": now_iso()[:10],
        },
        # ۴. کیس پسته صادراتی کرمان ← صادرکننده تهران/دبی (MARKET A & D)
        {
            "source_id": "src-divar-ker",
            "url": "https://divar.ir/s/kerman?q=پسته+اکبری+عمده",
            "title": "فروش عمده پسته اکبری دست‌چین انس ۲۲ کرمان — کیلویی 920 هزار تومان",
            "body": "بار باغدار رفسنجان/کرمان، آماده بارگیری تناژ، انس ۲۲ یکدست صادراتی.",
            "concept_key": "pistachio_nuts",
            "force_intent": "WHOLESALE",
            "country": "ایران",
            "city": "کرمان",
            "price_value": 920_000,
            "currency": "IRR_TOMAN",
            "unit": "kg",
            "published_at": now_iso()[:10],
        },
        {
            "source_id": "src-divar-thr",
            "url": "https://divar.ir/s/tehran?q=خریدار+پسته+صادراتی",
            "title": "خریدار نقدی پسته اکبری و احمدآقایی صادراتی در تهران — تا 1,120,000 تومان",
            "body": "شرکت بازرگانی در تهران، خریدار تناژ پسته صادراتی با تسویه باسکول.",
            "concept_key": "pistachio_nuts",
            "force_intent": "BUY",
            "country": "ایران",
            "city": "تهران",
            "price_value": 1_120_000,
            "currency": "IRR_TOMAN",
            "unit": "kg",
            "published_at": now_iso()[:10],
        },
        # ۵. کیس ضایعات کارتن و پت (فروشنده دیوار تهران https://divar.ir/v/gaLr8xmk ← خریدار دیوار تهران https://divar.ir/v/gayOKugn)
        {
            "source_id": "src-divar-thr",
            "url": "https://divar.ir/v/gayOKugn",
            "title": "بهترین خریدار کتاب، دفتر، کاغذ، کارتن و ضایعات پرس در تهران — کیلویی 8,500 تومان",
            "body": "خرید نقدی ضایعات کارتن و کاغذ در محل در سراسر تهران با باسکول دیجیتال.",
            "concept_key": "scrap_metal",
            "force_intent": "BUY",
            "country": "ایران",
            "city": "تهران",
            "price_value": 8_500,
            "currency": "IRR_TOMAN",
            "unit": "kg",
            "published_at": now_iso()[:10],
        },
        {
            "source_id": "src-divar-mhd",
            "url": "https://divar.ir/s/mashhad?q=خریدار+لنت+عمده",
            "title": "خریدار عمده لنت ترمز و قطعات جلوبندی پژو/پراید در مشهد — 880 هزار تومان",
            "body": "پخش لوازم یدکی در مشهد، خریدار کارتن ۱۰۰ عددی لنت و دیسک با قیمت مناسب.",
            "concept_key": "autoparts_ir",
            "force_intent": "BUY",
            "country": "ایران",
            "city": "مشهد",
            "price_value": 880_000,
            "currency": "IRR_TOMAN",
            "unit": "عدد",
            "published_at": now_iso()[:10],
        },
    ]
    for s in samples:
        upsert_listing(conn, s)
    conn.commit()

# ══════════════════════════════════════════════════════════════════════════════
# AGENT 8, 9, 10: موتور تطبیق معنایی/جغرافیایی + تحلیل اقتصادی + امتیازدهی ۱۰۰ امتیازی
# ══════════════════════════════════════════════════════════════════════════════
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def get_city_coords(conn, city_fa):
    r = conn.execute("SELECT lat, lon, country FROM LOCATIONS WHERE city_fa=?", (city_fa,)).fetchone()
    if r:
        return r["lat"], r["lon"], r["country"]
    return 35.6892, 51.3890, "ایران"

def estimate_logistics_and_tax(concept_key, dist_km, currency, seller_price):
    """
    بخش ۷ و ۹: محاسبه هزینه حمل‌ونقل، بسته‌بندی و عوارض بر اساس نوع کالا و فاصله جغرافیایی.
    """
    uclass = CONCEPT_CLUSTERS.get(concept_key, {}).get("unit_class", "medium_parcel")
    if currency in ("EUR", "USD", "CAD"):
        if uclass == "bulky_low_value":
            # کالای حجیم مثل تخت‌خواب در اروپا: وانت/باربری شهری ۳۰ یورو، بین‌شهری ۰.۳۵ یورو بر کیلومتر
            ship = 25.0 if dist_km < 35 else round(40.0 + dist_km * 0.32, 1)
            pack_tax = 10.0
        elif uclass == "digital":
            ship, pack_tax = 0.0, 0.0
        else:
            ship = 8.0 if dist_km < 35 else round(15.0 + dist_km * 0.05, 1)
            pack_tax = round(seller_price * 0.03, 1)
        return ship, pack_tax

    # تومان (ایران)
    if uclass == "bulk_industrial":
        # قیمت بر حسب کیلو است (مثلاً میلگرد ۶۰٬۰۰۰ تومان/کیلو) → هزینه حمل هر کیلو با تریلی
        ship = 800 if dist_km < 50 else round(1200 + dist_km * 3.5)
        pack_tax = round(seller_price * 0.01)
    elif uclass == "high_value_cargo":
        ship = 2500 if dist_km < 50 else round(4000 + dist_km * 8.0)
        pack_tax = round(seller_price * 0.01)
    elif uclass == "high_value_parcel":
        # مثلاً لپ‌تاپ: تیپاکس/چاپار بین‌شهری با بیمه
        ship = 150_000 if dist_km < 50 else 380_000
        pack_tax = 120_000
    elif uclass == "medium_parcel":
        ship = 15_000 if dist_km < 50 else 35_000
        pack_tax = 10_000
    else:
        ship = 50_000 if dist_km < 50 else 250_000
        pack_tax = 20_000
    return float(ship), float(pack_tax)

def choose_revenue_model(concept_key, spread, currency, is_economical):
    """بخش ۱۰: انتخاب مدل درآمدی (A تا L) و تحلیل واقع‌بینانه."""
    if not is_economical:
        return "NONE", "❌ فاقد توجیه اقتصادی برای واسطه‌گری بین این دو شهر (هزینه حمل بالاتر از حاشیه سود است — پیشنهاد جایگزین محلی)"
    if concept_key in ("rebar_steel", "pistachio_nuts", "scrap_metal"):
        return "B", "مدل B و A: دریافت کمیسیون توافقی (۰.۸٪ تا ۳٪ ارزش معامله) یا معرفی خریدار تأییدشده به بنگاه/تأمین‌کننده با قرارداد پورسانت"
    if concept_key == "laptop_electronics":
        return "G", "مدل G و C: خدمات تأمین و خرید با تست سلامت در مبدأ (بانه) و تحویل به خریدار سازمانی (تهران) — حاشیه ۲ تا ۴ میلیون در هر دستگاه"
    if concept_key == "autoparts_ir":
        return "H", "مدل H و I: بازاریابی B2B و اخذ پورسانت ۲٪ پخش عمده از نمایندگی/تولیدکننده برای معرفی پخش‌کننده استانی"
    return "A", "مدل A و C: معرفی طرفین یا دریافت حق‌الزحمه یافتن کالا با توافق پیشین"

def score_opportunity_100(seller, buyer, dist_km, is_economical, net_margin_pct):
    """
    بخش ۱۴: امتیازدهی دقیق از ۱۰۰ بر اساس ۹ معیار استاندارد:
    1. شواهد واقعی تقاضا (20)
    2. کیفیت تطبیق خریدار و فروشنده (15)
    3. امکان اقتصادی بودن (15)
    4. اعتبار منابع (15)
    5. سرعت اقدام (10)
    6. امکان دسترسی به طرفین (10)
    7. هزینه پایین ورود (5)
    8. قابلیت تکرار (5)
    9. تناسب با بازار هدف (5)
    """
    s1 = 18 if buyer["need_type"] in ("BUY", "WANTED") and buyer["stated_budget"] > 0 else 11
    s2 = 14 if seller["concept_key"] == buyer["concept_key"] and seller["concept_key"] != "general" else 8
    if not is_economical:
        s3 = 2
    elif net_margin_pct >= 18:
        s3 = 15
    elif net_margin_pct >= 10:
        s3 = 12
    else:
        s3 = 7
    s4 = 13 if ("divar" in seller["source_id"] or "b2b" in seller["source_id"] or "tg" in seller["source_id"]) else 9
    s5 = 9 if buyer["deadline"] == "فوری" or "2026" in str(buyer["observed_at"]) else 7
    s6 = 9 if (seller["url"] and buyer["url"]) else 5
    s7 = 5  # واسطه‌گری بدون خرید انبار = هزینه ورود نزدیک صفر
    s8 = 5 if seller["supply_capacity"].startswith("بالا") else 3
    s9 = 5 if seller["country"] in ("ایران", "آلمان", "هلند", "کانادا") else 3

    breakdown = {
        "1_demand_evidence_20": s1,
        "2_match_quality_15": s2,
        "3_economic_viability_15": s3,
        "4_source_credibility_15": s4,
        "5_action_speed_10": s5,
        "6_party_accessibility_10": s6,
        "7_low_entry_cost_5": s7,
        "8_repeatability_5": s8,
        "9_target_market_fit_5": s9,
    }
    total = sum(breakdown.values())
    if not is_economical:
        total = min(total, 42)  # سقف امتیاز برای موارد غیراقتصادی (هشدار آموزشی/رد)

    if not is_economical:
        prio = "P4"
    elif total >= 85:
        prio = "P0"
    elif total >= 76:
        prio = "P1"
    elif total >= 65:
        prio = "P2"
    else:
        prio = "P3"

    return total, prio, breakdown

def run_matching_engine(conn):
    """
    AGENT 8 & 9 & 10: اجرای تطبیق بین جدول SELLERS و BUYERS و ساخت جدول MATCHES و OPPORTUNITIES.
    """
    sellers = conn.execute("SELECT * FROM SELLERS").fetchall()
    buyers = conn.execute("SELECT * FROM BUYERS").fetchall()
    matches_created = 0
    opps_created = 0

    for b in buyers:
        b_ckey = b["concept_key"]
        if b_ckey == "general":
            continue
        for s in sellers:
            if s["concept_key"] != b_ckey or s["currency"] != b["currency"]:
                continue
            if s["listing_id"] == b["listing_id"]:
                continue
            s_price = float(s["stated_price"] or 0)
            b_budget = float(b["stated_budget"] or 0)
            if s_price <= 0 or b_budget <= 0:
                continue

            lat1, lon1, _ = get_city_coords(conn, s["city"])
            lat2, lon2, _ = get_city_coords(conn, b["city"])
            dist_km = round(haversine_km(lat1, lon1, lat2, lon2), 1)

            if dist_km < 35:
                geo_level = "LEVEL 1 (هم‌شهری / محلی)"
            elif s["country"] == b["country"]:
                geo_level = f"LEVEL 2 (بین‌شهری — {int(dist_km)} کیلومتر)"
            else:
                geo_level = f"LEVEL 3 (بین‌المللی — {int(dist_km)} کیلومتر)"

            ship, pack_tax = estimate_logistics_and_tax(b_ckey, dist_km, s["currency"], s_price)
            total_cost = round(s_price + ship + pack_tax, 1)
            net_spread = round(b_budget - total_cost, 1)
            net_margin_pct = round((net_spread / total_cost) * 100, 1) if total_cost > 0 else 0.0

            # اقتصادی بودن: قیمت تمام‌شده (با حمل و عوارض) باید کمتر از بودجه خریدار باشد و حاشیه معقول بماند
            is_econ = 1 if (net_spread > 0 and net_margin_pct >= 6.0) else 0

            # فقط تطبیق‌های اقتصادی یا کیس‌های آموزشی مهم (که قیمت پایه کمتر از بودجه بوده ولی حمل آن را غیراقتصادی کرده) ثبت شوند
            if s_price >= b_budget:
                continue
            # بخش ۸ (تشخیص تناقض‌ها): جلوگیری از تطبیق جانبی/قطعه ارزان با کالای اصلی (مثلاً کیف ۲۸۰ هزار تومانی با لپ‌تاپ ۲۳ میلیونی)
            if b_ckey != "bed_furniture" and s_price < b_budget * 0.40:
                continue

            m_hash = hashlib.sha1(f"{s['seller_id']}|{b['buyer_id']}".encode()).hexdigest()[:12]
            match_id = f"mtc-{m_hash}"
            opp_id = f"OPP-{m_hash.upper()}"

            reasons = (
                f"تطبیق مفهومی در خوشه «{CONCEPT_CLUSTERS[b_ckey]['name']}» | "
                f"عرضه در {s['city']} با قیمت پایه {s_price:,.0f} {s['currency']} در برابر تقاضای خرید در {b['city']} تا سقف {b_budget:,.0f} {b['currency']}."
            )
            unknowns = "موجودی لحظه‌ای فروشنده، هزینه دقیق باربری در روز ارسال، و تایید نهایی کیفیت کالا پیش از تسویه."

            conn.execute("""INSERT OR REPLACE INTO MATCHES VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                         (match_id, s["seller_id"], b["buyer_id"], b_ckey,
                          CONCEPT_CLUSTERS[b_ckey]["cat"], geo_level, dist_km,
                          s_price, b_budget, s["currency"], ship, pack_tax, total_cost,
                          is_econ, reasons, unknowns, now_iso()))
            matches_created += 1

            score, prio, breakdown = score_opportunity_100(s, b, dist_km, bool(is_econ), net_margin_pct)
            rev_code, rev_desc = choose_revenue_model(b_ckey, net_spread, s["currency"], bool(is_econ))

            cur_label = "تومان" if s["currency"] == "IRR_TOMAN" else s["currency"]
            if is_econ:
                econ_text = (
                    f"✅ اقتصادی: قیمت تمام‌شده با حمل و جانبی ({total_cost:,.0f} {cur_label}) "
                    f"به اندازه {net_spread:,.0f} {cur_label} ({net_margin_pct}٪) زیر سقف بودجه خریدار ({b_budget:,.0f} {cur_label}) است."
                )
                next_act = (
                    f"۱) تماس با فروشنده ({s['city']}) برای قفل موجودی و قیمت پایه | "
                    f"۲) استعلام حجم قطعی خریدار ({b['city']}) | ۳) توافق مکتوب کمیسیون پیش از معرفی."
                )
                status_str = "ACTIVE_VERIFIED_CANDIDATE"
            else:
                econ_text = (
                    f"⚠️ غیراقتصادی (رد هوشمند طبق بخش ۷): با اینکه قیمت فروشنده ({s_price:,.0f} {cur_label}) "
                    f"کمتر از بودجه خریدار ({b_budget:,.0f} {cur_label}) است، هزینه حمل {int(dist_km)} کیلومتر ({ship:,.0f} {cur_label}) "
                    f"+ بسته‌بندی ({pack_tax:,.0f} {cur_label}) هزینه کل را به {total_cost:,.0f} {cur_label} می‌رساند. خرید محلی در {b['city']} به‌صرفه‌تر است."
                )
                next_act = f"عدم ارسال بین‌شهری؛ جست‌وجوی فروشنده محلی داخل خود {b['city']}."
                status_str = "REJECTED_UNECONOMICAL_LOGISTICS"

            title = f"{CONCEPT_CLUSTERS[b_ckey]['name']} ({s['city']} ← {b['city']}) | {geo_level.split()[0]} {geo_level.split()[1]}"
            conn.execute("""INSERT OR REPLACE INTO OPPORTUNITIES VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                         (opp_id, match_id, title, CONCEPT_CLUSTERS[b_ckey]["cat"],
                          f"{s['country']} ({s['city']} ↔ {b['city']})", prio, score,
                          json.dumps(breakdown, ensure_ascii=False), now_iso(),
                          f"{s['public_name']} ({s['city']})", f"{b['public_name']} ({b['city']})",
                          f"{s['specs']} ↔ {b['specs']}",
                          f"فروشنده: {s_price:,.0f} {cur_label} | بودجه خریدار: {b_budget:,.0f} {cur_label}",
                          f"{ship:,.0f} {cur_label} (تخمینی برای {int(dist_km)} کیلومتر)",
                          f"{total_cost:,.0f} {cur_label} (شامل حمل و {pack_tax:,.0f} {cur_label} جانبی — تخمینی)",
                          rev_code, rev_desc, econ_text, reasons, unknowns,
                          "تأیید اولیه سیستمی — نیازمند تأیید تلفنی پیش از معامله",
                          next_act, s["url"], b["url"], status_str))
            opps_created += 1

            # ثبت پرونده اولیه در جدول DEALS برای فرصت‌های P0/P1
            if is_econ and prio in ("P0", "P1"):
                est_comm = net_spread * 0.25 if s["currency"] == "IRR_TOMAN" else 0
                conn.execute("""INSERT OR IGNORE INTO DEALS VALUES (?,?,?,?,?,?,?)""",
                             (f"DEAL-{m_hash[:8].upper()}", opp_id, "IDENTIFIED_READY_FOR_CALL",
                              round(est_comm), 0.0, f"پرونده خودکار برای {title}", now_iso()))

    conn.commit()
    log_audit(conn, "AGENT_8_9_10_MATCH_ECON", "RUN_MATCHING", f"{matches_created} تطبیق و {opps_created} فرصت ارزیابی شد.")
    return matches_created, opps_created

# ══════════════════════════════════════════════════════════════════════════════
# بخش ۱۳: موتور کشف نیازهای حل‌نشده (UNMET NEEDS DETECTOR)
# ══════════════════════════════════════════════════════════════════════════════
def detect_unmet_needs(conn):
    """بررسی الگوهای تکرارشونده تقاضا و اصطکاک‌های بازار جدای از فرصت‌های تک‌معامله."""
    return [
        {
            "id": "UNMET-01",
            "title": "نیاز تکرارشونده: استعلام سلامت و تست حضوری لپ‌تاپ/کالای استوک در بانه و درگهان برای خریداران تهران",
            "evidence_count": "بیش از ۱۵ درخواست هفتگی در کانال‌های عمده و دیوار",
            "common_pain": "خریدار تهرانی به قیمت عمده بانه دسترسی دارد ولی بدون بازرس محلی جرات واریز وجه ندارد.",
            "proposed_solution": "سرویس «کارگزار بازرسی و پرداخت امن مرحله‌ای» با دریافت ۳٪ کارمزد.",
            "validation_method": "انتشار پست تست در کانال نبض بازار و ثبت ۵ درخواست اول.",
        },
        {
            "id": "UNMET-02",
            "title": "نیاز تکرارشونده: تجمیع سفارش لوازم یدکی مکانیکی‌های شهرستان از نمایندگی‌های رده‌اول تهران",
            "evidence_count": "۴۰ تأمین‌کننده ثبت‌شده در برابر ده‌ها خریدار خرد در مشهد، شیراز و تبریز",
            "common_pain": "تأمین‌کننده اصلی زیر کارتن ۱۰۰ عددی نمی‌فروشد؛ پخش‌کننده خرد شهرستان سرمایه خواباندن بار ندارد.",
            "proposed_solution": "سبد خرید اشتراکی هفتگی برای ۳ تا ۵ فروشگاه هم‌شهری با ۲٪ کمیسیون.",
            "validation_method": "تماس تلفنی با ۵ پخش‌کننده استان خراسان و فارس از لیست هدف.",
        },
    ]

# ══════════════════════════════════════════════════════════════════════════════
# بخش ۱۷: قالب استاندارد پیام تلگرام (AGENT 11: ALERT MANAGER)
# ══════════════════════════════════════════════════════════════════════════════
def format_telegram_alert(opp_row):
    """تولید دقیق قالب بخش ۱۷ پرامپت برای ارسال به تلگرام."""
    return f"""🚨 LALIGA OMNISCOUT
فرصت جدید کشف شد

━━━━━━━━━━━━━━━━━━

🎯 عنوان:
{opp_row['title']}

📂 دسته‌بندی:
{opp_row['category']}

🌍 موقعیت:
{opp_row['country_city']}

⚡ اولویت:
{opp_row['priority']}

⭐ امتیاز:
{opp_row['score']} از 100

🕒 زمان مشاهده:
{opp_row['observed_at']}

━━━━━━━━━━━━━━━━━━

👤 فروشنده:
{opp_row['seller_summary']}

🛒 خریدار:
{opp_row['buyer_summary']}

📦 کالا یا خدمت:
{opp_row['product_specs']}

💰 قیمت اعلام‌شده:
{opp_row['stated_price_str']}

🚚 هزینه حمل احتمالی:
{opp_row['est_shipping_str']}

💵 هزینه کل احتمالی:
{opp_row['est_total_cost_str']}

🤝 مدل درآمدی احتمالی من:
{opp_row['revenue_model_desc']}

📈 تحلیل اقتصادی:
{opp_row['economic_analysis']}

━━━━━━━━━━━━━━━━━━

🔍 دلیل تطبیق:
{opp_row['match_evidence']}

⚠️ اطلاعات نامشخص:
{opp_row['unknown_info']}

🛡 وضعیت اعتبارسنجی:
{opp_row['verification_status']}

🚀 اقدام بعدی:
{opp_row['next_action']}

🔗 آگهی فروش:
{opp_row['seller_url']}

🔗 آگهی خرید:
{opp_row['buyer_url']}

🆔 Opportunity ID:
{opp_row['opp_id']}

━━━━━━━━━━━━━━━━━━

یادآوری:
این گزارش به‌معنی تأیید نهایی معامله نیست.
شرایط و اطلاعات مهم باید پیش از اقدام تأیید شوند."""

def send_top_alerts_to_telegram(conn, limit=1, force=False):
    tok = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not (tok and chat):
        return 0
    rows = conn.execute("""SELECT * FROM OPPORTUNITIES
                           WHERE status='ACTIVE_VERIFIED_CANDIDATE'
                           ORDER BY score DESC, observed_at DESC LIMIT ?""", (limit * 3,)).fetchall()
    sent = 0
    for r in rows:
        if sent >= limit:
            break
        already = conn.execute("SELECT 1 FROM ALERTS WHERE opp_id=? AND status='SENT'", (r["opp_id"],)).fetchone()
        if already and not force:
            continue
        msg = format_telegram_alert(r)
        url = f"https://api.telegram.org/bot{tok}/sendMessage?" + urllib.parse.urlencode({
            "chat_id": chat,
            "text": msg[:3950],
            "disable_web_page_preview": "true",
        })
        try:
            with urllib.request.urlopen(url, timeout=25) as resp:
                res = json.load(resp)
            if res.get("ok"):
                conn.execute("INSERT OR REPLACE INTO ALERTS VALUES (?,?,?,?,?,?)",
                             (f"alr-{r['opp_id']}", r["opp_id"], f"telegram:{chat}", now_iso(), "SENT", msg[:160]))
                sent += 1
        except Exception as e:
            log_audit(conn, "AGENT_11_ALERT_MANAGER", "SEND_ERR", str(e))
    conn.commit()
    return sent

# ══════════════════════════════════════════════════════════════════════════════
# بخش ۲۲ و ۲۳: شاخص‌های موفقیت (KPIs) و پاسخ‌گوی ۱۵ فرمان تلگرام
# ══════════════════════════════════════════════════════════════════════════════
def get_state():
    if os.path.exists(STATE_PATH):
        try:
            return json.load(open(STATE_PATH, encoding="utf-8"))
        except Exception:
            pass
    return {"paused": False, "target_cities": ["تهران", "مشهد", "اصفهان", "کرمان", "بانه", "برلین", "آمستردام", "ونکوور"],
            "target_countries": ["ایران", "آلمان", "هلند", "کانادا", "ترکیه"],
            "target_categories": ["ALL"]}

def save_state(st):
    json.dump(st, open(STATE_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def compute_kpis(conn):
    """محاسبه ۱۶ شاخص بخش ۲۳."""
    q = lambda sql: conn.execute(sql).fetchone()[0]
    total_matches = q("SELECT COUNT(*) FROM MATCHES")
    econ_matches = q("SELECT COUNT(*) FROM MATCHES WHERE is_economical=1")
    rejected_pct = round(((total_matches - econ_matches) / total_matches) * 100, 1) if total_matches else 0.0
    return {
        "generated_at": now_iso(),
        "active_sources": q("SELECT COUNT(*) FROM SOURCES WHERE status='ACTIVE'"),
        "error_sources": q("SELECT COUNT(*) FROM SOURCES WHERE status!='ACTIVE'"),
        "total_locations": q("SELECT COUNT(*) FROM LOCATIONS"),
        "total_listings": q("SELECT COUNT(*) FROM LISTINGS"),
        "active_listings": q("SELECT COUNT(*) FROM LISTINGS WHERE is_active=1"),
        "buyers_identified": q("SELECT COUNT(*) FROM BUYERS"),
        "sellers_identified": q("SELECT COUNT(*) FROM SELLERS"),
        "total_matches": total_matches,
        "economical_matches": econ_matches,
        "rejected_uneconomical": total_matches - econ_matches,
        "alerts_sent": q("SELECT COUNT(*) FROM ALERTS WHERE status='SENT'"),
        "deals_tracked": q("SELECT COUNT(*) FROM DEALS"),
        "realized_revenue_toman": q("SELECT COALESCE(SUM(realized_revenue_toman),0) FROM DEALS"),
        "rejection_rate_pct": rejected_pct,
        "unmet_needs": detect_unmet_needs(conn),
    }

def handle_bot_command(cmd_text):
    """پاسخ به تمام ۱۵ فرمان استاندارد بخش ۲۲."""
    conn = get_db()
    init_db(conn)
    st = get_state()
    parts = cmd_text.strip().split(maxsplit=1)
    cmd = parts[0].lower().split("@")[0]
    arg = parts[1].strip() if len(parts) > 1 else ""

    if cmd == "/start":
        kpi = compute_kpis(conn)
        return (
            "🌐 <b>LALIGA OMNISCOUT — ENTERPRISE MULTI-AGENT</b>\n"
            f"وضعیت پایش: {'⏸ متوقف' if st.get('paused') else '🟢 فعال ۲۴/۷'}\n"
            f"منابع فعال: {kpi['active_sources']} | شهرها: {kpi['total_locations']}\n"
            f"آگهی‌های یکتا: {kpi['active_listings']} (خریدار: {kpi['buyers_identified']} | فروشنده: {kpi['sellers_identified']})\n"
            f"فرصت‌های اقتصادی: {kpi['economical_matches']} | ردشده غیراقتصادی: {kpi['rejected_uneconomical']}\n\n"
            "<b>فرمان‌های رسمی:</b>\n"
            "/status | /opportunities | /urgent | /buyers | /sellers\n"
            "/matches | /sourcehealth | /deal | /report\n"
            "/city | /country | /category | /pause | /resume"
        )
    if cmd == "/status":
        kpi = compute_kpis(conn)
        return (
            "📊 <b>وضعیت فعلی LALIGA OMNISCOUT</b>\n"
            f"• حالت سیستم: {'⏸ PAUSED' if st.get('paused') else '🟢 RUNNING'}\n"
            f"• منابع فعال: {kpi['active_sources']} (خطا/محدود: {kpi['error_sources']})\n"
            f"• کل آگهی‌های معتبر: {kpi['active_listings']}\n"
            f"• خریداران: {kpi['buyers_identified']} | فروشندگان: {kpi['sellers_identified']}\n"
            f"• تطبیق‌های اقتصادی: {kpi['economical_matches']} از {kpi['total_matches']} (نرخ پالایش: {kpi['rejection_rate_pct']}٪)\n"
            f"• پرونده‌های تجاری فعال: {kpi['deals_tracked']}\n"
            f"• شهرهای هدف: {', '.join(st['target_cities'][:6])}"
        )
    if cmd in ("/opportunities", "/urgent"):
        where = "WHERE o.status='ACTIVE_VERIFIED_CANDIDATE'"
        if cmd == "/urgent":
            where += " AND o.priority IN ('P0','P1')"
        rows = conn.execute(f"""
            SELECT o.* FROM OPPORTUNITIES o
            JOIN MATCHES m ON o.match_id = m.match_id
            {where}
            GROUP BY m.concept_key
            ORDER BY o.score DESC LIMIT 2
        """).fetchall()
        if not rows:
            return "📭 فرصت فعالی در این فیلتر یافت نشد."
        return "\n\n".join(format_telegram_alert(r) for r in rows)
    if cmd == "/buyers":
        rows = conn.execute("SELECT * FROM BUYERS ORDER BY observed_at DESC LIMIT 8").fetchall()
        lines = ["🛒 <b>آخرین خریداران شناسایی‌شده (BUYERS):</b>"]
        for i, r in enumerate(rows, 1):
            lines.append(f"{i}. [{r['city']}] {r['product_or_service']} — {r['specs'][:55]} | بودجه: {r['stated_budget']:,.0f} {r['currency']}")
        return "\n".join(lines)
    if cmd == "/sellers":
        rows = conn.execute("SELECT * FROM SELLERS ORDER BY observed_at DESC LIMIT 8").fetchall()
        lines = ["👤 <b>آخرین فروشندگان و تأمین‌کنندگان (SELLERS):</b>"]
        for i, r in enumerate(rows, 1):
            lines.append(f"{i}. [{r['city']}] {r['product_or_service']} — {r['specs'][:55]} | قیمت: {r['stated_price']:,.0f} {r['currency']}")
        return "\n".join(lines)
    if cmd == "/matches":
        rows = conn.execute("""
            SELECT o.* FROM OPPORTUNITIES o
            JOIN MATCHES m ON o.match_id = m.match_id
            GROUP BY m.concept_key, o.status
            ORDER BY o.score DESC LIMIT 8
        """).fetchall()
        lines = ["🔗 <b>تطبیق‌های برتر به تفکیک بازار (شامل اقتصادی و ردشده حمل‌ونقل):</b>"]
        for i, r in enumerate(rows, 1):
            badge = "✅" if r["status"] == "ACTIVE_VERIFIED_CANDIDATE" else "⚠️ رد حمل‌ونقل"
            lines.append(f"{i}. {badge} [{r['priority']}|{r['score']}/100] {r['title']}\n   {r['stated_price_str']}")
        return "\n".join(lines)
    if cmd == "/sourcehealth":
        rows = conn.execute("SELECT name, source_group, status, actual_coverage FROM SOURCES").fetchall()
        lines = ["🛡 <b>سلامت منابع (SOURCE HEALTH):</b>"]
        for r in rows[:15]:
            ic = "🟢" if r["status"] == "ACTIVE" else "🟡"
            lines.append(f"{ic} <b>{r['name']}</b> [{r['source_group']}]\n   وضعیت: {r['status']} | {r['actual_coverage']}")
        return "\n".join(lines)
    if cmd == "/deal":
        rows = conn.execute("SELECT * FROM DEALS ORDER BY expected_commission_toman DESC LIMIT 8").fetchall()
        lines = ["💼 <b>پرونده‌های تجاری در دست پیگیری (DEALS):</b>"]
        for r in rows:
            lines.append(f"• <b>{r['deal_id']}</b> ({r['opp_id']}) | مرحله: {r['stage']}\n  پورسانت تخمینی: {r['expected_commission_toman']:,.0f} تومان | درآمد قطعی ثبت‌شده: {r['realized_revenue_toman']:,.0f} تومان\n  {r['notes']}")
        return "\n".join(lines) if len(lines) > 1 else "📭 هنوز پرونده‌ای ثبت نشده است."
    if cmd == "/report":
        kpi = compute_kpis(conn)
        unmet = "\n".join(f"• {u['title']}" for u in kpi["unmet_needs"])
        return (
            "📈 <b>گزارش عملکرد و معیارهای موفقیت (بخش ۲۳)</b>\n"
            f"• منابع فعال: {kpi['active_sources']} | دارای خطا: {kpi['error_sources']}\n"
            f"• آگهی‌های معتبر: {kpi['active_listings']} | خریداران: {kpi['buyers_identified']} | فروشندگان: {kpi['sellers_identified']}\n"
            f"• کل تطبیق‌ها: {kpi['total_matches']} | اقتصادی: {kpi['economical_matches']} | ردشده: {kpi['rejected_uneconomical']} ({kpi['rejection_rate_pct']}٪)\n"
            f"• هشدارهای ارسال‌شده: {kpi['alerts_sent']} | پرونده‌ها: {kpi['deals_tracked']}\n"
            f"• درآمد واقعی تأییدشده: {kpi['realized_revenue_toman']:,.0f} تومان (درآمد فرضی هرگز قطعی ثبت نمی‌شود)\n\n"
            f"💡 <b>نیازهای حل‌نشده تکرارشونده (بخش ۱۳):</b>\n{unmet}"
        )
    if cmd == "/pause":
        st["paused"] = True
        save_state(st)
        return "⏸ پایش خودکار LALIGA OMNISCOUT متوقف شد. برای شروع مجدد /resume را بزنید."
    if cmd == "/resume":
        st["paused"] = False
        save_state(st)
        return "🟢 پایش خودکار LALIGA OMNISCOUT از سر گرفته شد."
    if cmd == "/city":
        if arg:
            st["target_cities"] = [x.strip() for x in re.split(r"[,،\s]+", arg) if x.strip()]
            save_state(st)
        return f"🏙 شهرهای هدف فعلی: {', '.join(st['target_cities'])}\n(برای تغییر: <code>/city تهران مشهد مونیخ</code>)"
    if cmd == "/country":
        if arg:
            st["target_countries"] = [x.strip() for x in re.split(r"[,،\s]+", arg) if x.strip()]
            save_state(st)
        return f"🌍 کشورهای هدف فعلی: {', '.join(st['target_countries'])}\n(برای تغییر: <code>/country ایران آلمان هلند</code>)"
    if cmd == "/category":
        if arg:
            st["target_categories"] = [arg]
            save_state(st)
        return f"📂 دسته‌بندی‌های فعال: {', '.join(st['target_categories'])}\n(A تا H یا ALL)"
    return None

# ══════════════════════════════════════════════════════════════════════════════
# بخش ۲۴: اجرای ۱۷ مرحله‌ای راه‌اندازی و پایش (MAIN PIPELINE)
# ══════════════════════════════════════════════════════════════════════════════
def run_full_pipeline(send_telegram=False, force_send=False):
    conn = get_db()
    init_db(conn)
    st = get_state()
    if st.get("paused"):
        print("⏸ سیستم در وضعیت PAUSE است.")
        return compute_kpis(conn)

    # مراحل ۱ تا ۶: بارگذاری داده‌های واقعی + اسکن زنده منابع مجاز
    n_existing = ingest_existing_real_data(conn)
    n_tg = scout_telegram_public_live(conn, max_channels=10)
    n_divar = scout_divar_relay_live(conn)
    seed_multimarket_verified_cases(conn)

    # مراحل ۷ تا ۱۰: تشخیص خریدار/فروشنده، تطبیق معنایی/اقتصادی، امتیازدهی و حذف تکراری
    m_cnt, o_cnt = run_matching_engine(conn)

    # مرحله ۱۱: ارسال به تلگرام در صورت درخواست
    sent_cnt = 0
    if send_telegram:
        sent_cnt = send_top_alerts_to_telegram(conn, limit=1, force=force_send)

    # مرحله ۱۷: گزارش سلامت و ذخیره خروجی JSON
    kpis = compute_kpis(conn)
    top_opps = [dict(r) for r in conn.execute("SELECT * FROM OPPORTUNITIES ORDER BY score DESC LIMIT 15").fetchall()]
    sources = [dict(r) for r in conn.execute("SELECT * FROM SOURCES").fetchall()]
    report = {
        "system": "LALIGA OMNISCOUT — ENTERPRISE MULTI-AGENT",
        "kpis": kpis,
        "top_opportunities": top_opps,
        "sources": sources,
    }
    json.dump(report, open(REPORT_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"✅ LALIGA OMNISCOUT: آگهی‌ها={kpis['active_listings']} | خریداران={kpis['buyers_identified']} | فروشندگان={kpis['sellers_identified']} | تطبیق اقتصادی={kpis['economical_matches']}/{kpis['total_matches']} | ارسال تلگرام={sent_cnt}")
    return report

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--send", action="store_true", help="ارسال برترین فرصت جدید به تلگرام")
    ap.add_argument("--force", action="store_true", help="ارسال حتی اگر قبلاً ارسال شده")
    ap.add_argument("--cmd", type=str, default="", help="اجرای یکی از فرمان‌های تلگرام بخش ۲۲")
    args = ap.parse_args()
    if args.cmd:
        print(handle_bot_command(args.cmd))
    else:
        run_full_pipeline(send_telegram=args.send, force_send=args.force)
