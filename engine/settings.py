# -*- coding: utf-8 -*-
"""
⚙️ خواندن پنل کنترل (settings.json) + امکان بازنویسی با متغیر محیطی.
ترتیب اولویت: متغیر محیطی > settings.json > پیش‌فرض کد
این‌طور هم می‌توانی فایل را ویرایش کنی، هم در گیت‌هاب Variables بگذاری، هم در ترمینال export کنی.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "settings.json")

DEFAULTS = {
    "hot_alert": {"فعال": True, "حداکثر_عمر_دقیقه": 90, "حداقل_امتیاز": 55, "حداکثر_تعداد_در_هر_پیام": 5},
    "digest": {"فعال": True, "هر_چند_ساعت": 6},
    "content_kanal": {"کارت_قیمت_هر_چند_ساعت": 1,
                      "پست_فرصت_ها_ساعت_تهران": ["09:00", "19:00"],
                      "پست_قیمت_کانال_ها_ساعت_تهران": ["11:00"]},
    "فیلترها": {"حداقل_ارزش_معامله_تومان": 50000000,
                 "حوزه_های_فعال": ["pistachio", "steel", "scrap"],
                 "حداقل_امتیاز_فرصت": 0.62},
    "نرخ_پورسانت": {"خشکبار_و_صادرات": 0.01, "آهن_آلات_و_فولاد": 0.008, "ضایعات_و_بازیافت": 0.03},
    "پیام_رسان_ها": {"تلگرام": True, "بله": False, "روبیکا": False, "ایتا": False},
}

ENV_MAP = {                        # متغیر محیطی → مسیر در تنظیمات
    "HOT_MAX_AGE":        ("hot_alert", "حداکثر_عمر_دقیقه", int),
    "HOT_MIN_SCORE":      ("hot_alert", "حداقل_امتیاز", int),
    "HOT_MAX_ITEMS":      ("hot_alert", "حداکثر_تعداد_در_هر_پیام", int),
    "HOT_ENABLED":        ("hot_alert", "فعال", lambda v: str(v).lower() in ("1", "true", "yes")),
    "DIGEST_HOURS":       ("digest", "هر_چند_ساعت", int),
    "DIGEST_ENABLED":     ("digest", "فعال", lambda v: str(v).lower() in ("1", "true", "yes")),
    "MIN_DEAL_VALUE":     ("فیلترها", "حداقل_ارزش_معامله_تومان", int),
    "MIN_MATCH_SCORE":    ("فیلترها", "حداقل_امتیاز_فرصت", float),
    "CARD_EVERY_HOURS":   ("content_kanal", "کارت_قیمت_هر_چند_ساعت", int),
}

_cache = {}

def load(force=False):
    if _cache and not force: return _cache
    s = json.loads(json.dumps(DEFAULTS, ensure_ascii=False))
    if os.path.exists(PATH):
        try:
            user = json.load(open(PATH, encoding="utf-8"))
            for k, v in user.items():
                if k.startswith("_"): continue
                if isinstance(v, dict) and isinstance(s.get(k), dict): s[k].update(v)
                else: s[k] = v
        except Exception as e:
            print(f"⚠ settings.json خوانده نشد ({e}) — پیش‌فرض استفاده می‌شود")
    for env, (sec, key, cast) in ENV_MAP.items():
        if os.environ.get(env) not in (None, ""):
            try: s[sec][key] = cast(os.environ[env])
            except Exception: pass
    _cache.clear(); _cache.update(s)
    return s

def get(section, key=None, default=None):
    s = load()
    return s.get(section, {}).get(key, default) if key else s.get(section, default)

def save(s):
    json.dump(s, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

SUMMARY_KEYS = [
    ("⚡ هشدار فوری", "hot_alert", "فعال", "حداکثر_عمر_دقیقه", "حداقل_امتیاز"),
    ("📊 دیجست", "digest", "فعال", "هر_چند_ساعت"),
    ("🖼 کارت کانال", "content_kanal", "کارت_قیمت_هر_چند_ساعت"),
    ("🎯 فیلتر", "فیلترها", "حداقل_امتیاز_فرصت", "حداقل_ارزش_معامله_تومان"),
]

if __name__ == "__main__":
    s = load()
    print("⚙️ تنظیمات فعلی رهیاب")
    for sec, d in s.items():
        if sec.startswith("_"): continue
        print(f"\n[{sec}]")
        for k, v in d.items(): print(f"   {k}: {v}")
