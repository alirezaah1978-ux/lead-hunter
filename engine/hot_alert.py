# -*- coding: utf-8 -*-
"""
⚡ هشدار فوری — فقط آگهی‌های «تازه» و «باکیفیت» را همان لحظه می‌فرستد.
تفاوت با دیجست ۶ ساعته: دیجست همه‌ی فرصت‌ها را دسته‌ای می‌فرستد؛ این یکی فقط
آگهی‌هایی که «چند دقیقه پیش» ثبت شده‌اند و نشانه‌ی معامله‌ی عمده دارند.
منطق: در معامله‌ی عمده، زنگ اول برنده است. آگهی ۳ روزه را همه دیده‌اند.

اجرا:
    python3 hot_alert.py --dry-run                    # تست بدون ارسال
    python3 hot_alert.py                              # ارسال واقعی (به همه‌ی پلتفرم‌های تنظیم‌شده)
    python3 hot_alert.py --max-age 30 --min-score 60  # سخت‌گیرانه‌تر
"""
import json, os, sys, argparse, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import settings
from sources.divar_relay import crawl, CITIES
from notify_multi import broadcast, via_relay, configured
from config import VERTICALS

HERE = os.path.dirname(os.path.abspath(__file__))
LAST_NEW = 0        # تعداد آگهی‌های تازه‌ی این دور (برای تصمیم‌گیری دیجست)
LAST_FRESH = 0
OUT = os.path.join(HERE, "output"); os.makedirs(OUT, exist_ok=True)
STATE = os.path.join(OUT, "hot_seen.json")

# نشانه‌های «معامله‌ی عمده» در متن آگهی — بدون این‌ها، آگهی خرده‌فروشی است
BULK = ["عمده", "تن ", "تناژ", "بارگیری", "کامیون", "صادرات", "صادراتی", "کیلو",
        "کارخانه", "قرارداد", "مستقیم از", "باغدار", "تولیدکننده", "انبار", "فله"]
NEG = ["فروشگاه", "خدمات", "دستگاه", "تعمیر", "آموزش", "نصب", "قسط", "بسته بندی", "خرده"]

def score(r):
    """امتیاز سریع ۰-۱۰۰ برای آگهی تازه"""
    t = (r.get("title","") + " " + r.get("desc","")).lower()
    s = 40
    hits = [b for b in BULK if b in t]
    s += min(35, 9 * len(hits))
    neg = [n for n in NEG if n in t]
    s -= 25 * len(neg)
    # قیمت معقول برای همان حوزه؟
    from core import clean_listing
    l = clean_listing(dict(r))
    if l.get("unit_price"): s += 12
    elif l.get("price"):    s -= 8
    if l.get("is_demand_post"): s += 15        # آگهی «خریدار» = تقاضای آماده
    if r.get("age_minutes", 999) <= 30: s += 10
    return max(0, min(100, s)), hits, neg

def run(max_age=None, min_score=None, dry=False, relay_url="", relay_secret="", rotation=None):
    max_age = max_age if max_age is not None else settings.get("hot_alert","حداکثر_عمر_دقیقه",90)
    min_score = min_score if min_score is not None else settings.get("hot_alert","حداقل_امتیاز",55)
    if not settings.get("hot_alert","فعال",True):
        print("⏸ هشدار فوری در settings.json خاموش است — کاری انجام نشد."); return []
    allq = [q for v in VERTICALS.values() for q in v.get("b2b_queries", [])]
    # چرخش کوئری‌ها: هر دور نصف کوئری‌ها → اسکن سبک و سریع (هر کوئری هر ۲ دور = ۳۰ دقیقه یک‌بار)
    queries = allq[rotation % 2::2] if rotation is not None else allq
    city_map = {"تهران": "tehran", "کرمان": "kerman", "اصفهان": "isfahan", "مشهد": "mashhad",
                "تبریز": "tabriz", "شیراز": "shiraz", "اهواز": "ahvaz", "قم": "qom",
                "کرج": "karaj", "رشت": "rasht"}
    cities = tuple(city_map.get(c, "tehran") for c in settings.get("فیلترها", "شهرها", ["تهران", "کرمان", "اصفهان", "مشهد"]))
    rows = crawl(queries, cities=cities, cache_ttl=0)   # همیشه تازه — وگرنه آگهی جدید نمی‌بینیم
    print(f"🔎 بررسی {len(rows)} آگهی از {len(cities)} شهر")

    seen = set(json.load(open(STATE, encoding="utf-8"))) if os.path.exists(STATE) else set()
    fresh = [r for r in rows if r.get("age_minutes", 9999) <= max_age]
    new = [r for r in fresh if r["token"] not in seen]
    print(f"⏱ تازه (≤{max_age} دقیقه): {len(fresh)} | تازه و ندیده: {len(new)}")
    global LAST_NEW, LAST_FRESH
    LAST_NEW, LAST_FRESH = len(new), len(fresh)

    # فیلتر سودمحور: پورسانت برآوردی باید از کف تعیین‌شده بیشتر باشد
    from core import clean_listing
    from config import VERTICALS as VV
    min_fee = settings.get("فیلترها", "حداقل_پورسانت_برای_هشدار_تومان", 3_000_000)
    per_dom = settings.get("فیلترها", "حداقل_پورسانت_به_تفکیک_حوزه", {}) or {}
    hits, skipped_low = [], 0
    for r in new:
        sc, b, neg = score(r)
        if sc < min_score: continue
        l = clean_listing(dict(r))
        v = l.get("vertical") or "scrap"
        cfg = VV.get(v, {})
        price = l.get("unit_price") or 0
        qty = l.get("qty") or cfg.get("assumed_qty", 2000)   # فرض محافظه‌کارانه (۲ تن وزنی / ۱۰۰ عدد قطعه)
        est_fee = max(price * qty * cfg.get("fee_rate", 0.01), cfg.get("min_fee", 0)) if price else 0
        floor = per_dom.get(v, min_fee)                  # کف پورسانت به تفکیک حوزه
        if est_fee and est_fee < floor:
            skipped_low += 1; continue                   # نمی‌ارزد — مزاحم نشو
        r["est_fee"] = round(est_fee)
        hits.append((sc, r, b))
    if skipped_low: print(f"   💤 {skipped_low} مورد به‌خاطر پورسانت کم رد شد (کف: {min_fee:,} تومان)")
    hits.sort(key=lambda x: -x[0])
    print(f"🎯 واجد شرط (امتیاز ≥{min_score}): {len(hits)}")

    if not hits:
        print("   → چیزی برای هشدار نیست (این یعنی「کار می‌کند»، نه «خراب است»)")

    if hits:
        L = [f"⚡ <b>{len(hits)} آگهی تازه‌ی عمده — قبل از همه زنگ بزن</b>", ""]
        top = settings.get("hot_alert","حداکثر_تعداد_در_هر_پیام",5)
        for sc, r, b in hits[:top]:
            L += [f"<b>[{sc}] {r['title'][:60]}</b>",
                  (f"   💰 پورسانت برآوردی: {r.get('est_fee',0):,} تومان" if r.get("est_fee") else ""),
                  f"   📍 {r['city']} • {r.get('age_minutes','?')} دقیقه پیش • قیمت خام: {r.get('price','—')}",
                  f"   🔑 نشانه‌ها: {'، '.join(b[:4]) or '—'}",
                  f"   🔗 {r['url']}", ""]
        L.append("⏱ زنگ اول برنده است — این آگهی‌ها کمتر از ۹۰ دقیقه عمر دارند.")
        msg = "\n".join(L)
        if relay_url and not dry:
            via_relay(msg, relay_url, relay_secret)
        else:
            broadcast(msg, dry=dry)

    seen |= {r["token"] for r in rows}
    json.dump(sorted(seen)[-4000:], open(STATE, "w", encoding="utf-8"))
    return hits

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-age", type=int, default=None)
    ap.add_argument("--min-score", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    run(a.max_age, a.min_score, a.dry_run,
        os.environ.get("RELAY_URL",""), os.environ.get("RELAY_SECRET",""))
