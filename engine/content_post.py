# -*- coding: utf-8 -*-
"""
📢 انتشار خودکار محتوا در کانال‌ها — یک pipeline کامل:
  ۱) گزارش بازار را می‌خواند
  ۲) کارت تصویری می‌سازد (make_price_card.py)
  ۳) متن کپشن می‌سازد (چند نوع محتوا)
  ۴) به همه‌ی پلتفرم‌های تنظیم‌شده می‌فرستد (تصویر + متن)
  ۵) ضدتکرار: اگر محتوا نسبت به بار قبل تغییر نکرده باشد، دوباره نمی‌فرستد (تا کانال اسپم نشود)

انواع محتوا (--type):
  price     → کارت قیمت روز (پیش‌فرض) — مناسب هر ساعت
  opps      → «۳ فرصت امروز» — مناسب ۲ بار در روز
  insight   → تحلیل کوتاه بازار (متن) — مناسب روزی ۱ بار
  all       → هر سه (برای تست)

نمونه:
    python3 content_post.py --type price --dry-run
    python3 content_post.py --type opps            # ارسال واقعی
    python3 content_post.py --type price --via-relay "$RELAY_URL"
"""
import json, os, sys, argparse, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import notify_multi as nm
import settings
from notify_multi import broadcast, via_relay, configured, strip, n, money
from make_price_card import build as build_card

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
REPORT = os.path.join(OUT, "real_report.json")
STATE = os.path.join(OUT, "content_state.json")
CARD = os.path.join(OUT, "price_card.png")

def load_state():
    return json.load(open(STATE, encoding="utf-8")) if os.path.exists(STATE) else {}

def save_state(st):
    json.dump(st, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------- ۳ نوع متن ----------
def caption_price(D):
    s, P, I = D["stats"], D["pairs"], D["intel"]
    L = ["📊 <b>قیمت روز بازار</b>", ""]
    for v in I.values():
        unit = "عدد" if v.get("key") == "autoparts" or "یدکی" in v.get("fa", "") else "کیلو"
        L.append(f"• <b>{v['fa']}</b>: {n(v['median'])} تومان/{unit}  ({n(v['sellers'])} عرضه / {n(v['buyers'])} تقاضا)")
    L += ["", f"🔎 در {n(s['unique'])} آگهی بررسی‌شده، {n(s['pairs'])} فرصت معاملاتی شناسایی شد.", "",
          "📌 میانه‌ی آگهی‌های عمومی امروز — پسته/فولاد/ضایعات: تومان بر کیلو · لوازم یدکی: تومان بر عدد."]
    return "\n".join(L)

def caption_opps(D):
    P = D["pairs"]
    L = ["🎯 <b>۳ فرصت برتر امروز</b>", ""]
    for i, p in enumerate(P[:3], 1):
        L += [f"<b>{n(i)}. {p['vertical_fa']}</b>",
              f"خریدار: {n(p['buyer_price'])} • فروشنده: {n(p['seller_price'])} تومان/کیلو",
              f"فاصله: <b>{n(p['spread_per_kg'])}</b> تومان در کیلو  |  {p['seller_city']}", ""]
    L += ["⚠️ هر فرصت باید با تماس تلفنی (موجودی و اعتبار خریدار) تأیید شود.",
          "💬 برای دریافت تأمین/خرید در این حوزه‌ها، همین کانال را دنبال کنید."]
    return "\n".join(L)

def caption_tg_price(D):
    """قیمت از کانال‌های تخصصی + روند (مقایسه‌ی آخرین لیست با لیست قبلی) — محتوای بسیار معتبر برای کانال"""
    T = D.get("telegram_intel", [])
    if not T: return None
    # آخرین لیست هر کانال
    latest = {}
    for t in T:
        if t["channel"] not in latest or t["age_h"] < latest[t["channel"]]["age_h"]:
            latest[t["channel"]] = t
    L = ["💹 <b>قیمت روز از کانال‌های تخصصی</b>", ""]
    for ch, t in latest.items():
        prev = None
        for x in T:
            if x["channel"] == ch and x["age_h"] > t["age_h"]:
                if prev is None or x["age_h"] < prev["age_h"]: prev = x
        L.append(f"<b>{t['title'][:60]}</b>  <i>({n(t['age_h'])} ساعت پیش)</i>")
        pmap = {i["name"]: i["price"] for i in (prev or {}).get("items", [])}
        for it in t["items"][:7]:
            arrow = ""
            if it["name"] in pmap and pmap[it["name"]]:
                d = (it["price"] - pmap[it["name"]]) / pmap[it["name"]]
                if abs(d) >= 0.01: arrow = " 🔼" if d > 0 else " 🔽"
            mark = {"➕": " 🔼", "➖": " 🔽", "🔶": " ▪️"}.get(it.get("mark") or "", "")
            L.append(f"• {it['name'][:34]}: <b>{n(it['price'])}</b> تومان{arrow or mark}")
        if t.get("phone"): L.append(f"📞 {t['phone']}")
        L.append("")
    L += ["📌 قیمت‌ها عیناً از پست عمومی کانال‌های تخصصی استخراج شده‌اند (بدون دست‌کاری).", ""]
    return "\n".join(L)

def caption_insight(D):
    I, s = D["intel"], D["stats"]
    items = list(I.values())
    rich = max(items, key=lambda v: (v["buyers"] or 0) / max(1, v["sellers"]))
    thin = min(items, key=lambda v: (v["buyers"] or 0) / max(1, v["sellers"]))
    L = ["🧠 <b>تحلیل کوتاه بازار</b>", "",
         f"• بیشترین فشار تقاضا در «{rich['fa']}» است: {n(rich['buyers'])} آگهی خریدار در برابر "
         f"{n(rich['sellers'])} آگهی فروشنده.",
         f"• کم‌رونق‌ترین سمت تقاضا: «{thin['fa']}» با {n(thin['buyers'])} خریدار.",
         "",
         "💡 معنی‌اش برای معامله‌گر: جایی که خریدار بیشتر است، دست واسطه بازتر و پورسانت راحت‌تر است.",
         "",
         f"📈 نمونه‌ی امروز: میانگین فاصله‌ی قیمتی فرصت‌های شناسایی‌شده "
         f"{n(round(sum(p['spread_per_kg'] for p in D['pairs'][:10])/max(1,len(D['pairs'][:10]))))} تومان بر کیلو."]
    return "\n".join(L)

# ---------- ۲ و ۴: ساخت و انتشار ----------
def publish(kind="price", dry=False, relay_url="", relay_secret="", force=False):
    D = json.load(open(REPORT, encoding="utf-8"))
    # اگر chat_id کانال در پنل کنترل ثبت شده، خودکار به کانال هم می‌رود
    try:
        import settings as _st
        kch = _st.get("content_kanal", "chat_id", "") or _st.get("content_kanal", "کانال", "")
        if kch and not os.environ.get("KANAL_CHAT_ID"): os.environ["KANAL_CHAT_ID"] = str(kch)
    except Exception: pass
    st = load_state()
    card_path, text = None, ""

    if kind == "price":
        card_path = build_card(REPORT)
        text = caption_price(D)
        payload_key = hashlib.md5((open(card_path, "rb").read()[:50000].hex() + text).encode()).hexdigest()
    elif kind == "opps":
        text = caption_opps(D)
        payload_key = hashlib.md5(text.encode()).hexdigest()
    elif kind == "insight":
        text = caption_insight(D)
        payload_key = hashlib.md5(text.encode()).hexdigest()
    elif kind == "tg_price":
        text = caption_tg_price(D) or ""
        if not text: print("⏭ لیست قیمت تلگرامی موجود نیست."); return False
        payload_key = hashlib.md5(text.encode()).hexdigest()
    else:
        raise SystemExit("نوع نامعتبر: price | opps | insight | tg_price")

    if not force and st.get(kind) == payload_key:
        print(f"⏭ محتوای «{kind}» نسبت به بار قبل تغییری نکرده — ارسال نشد (ضداسپم). با --force اجبار کن.")
        return False

    print(f"📤 انتشار محتوا: {kind} {'(همراه تصویر)' if card_path else '(متن)'}")
    if card_path and not dry:
        res = nm.broadcast_photo(card_path, text, relay=bool(relay_url))
        print("   نتیجه:", res)
    elif relay_url and not dry:
        via_relay(text, relay_url, relay_secret)
    else:
        broadcast(text, dry=dry)

    if not dry:
        ch = nm.publish_channel(text, card_path)
        if ch: print("   کانال:", ch)
    st[kind] = payload_key
    save_state(st)
    return True

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", default="price", choices=["price", "opps", "insight", "tg_price"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    publish(a.type, a.dry_run, os.environ.get("RELAY_URL", ""), os.environ.get("RELAY_SECRET", ""), a.force)
