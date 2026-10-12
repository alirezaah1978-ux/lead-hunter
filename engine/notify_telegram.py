# -*- coding: utf-8 -*-
"""
ارسال «خلاصه‌ی فرصت‌های روز» به تلگرام تو.
- فقط با کتابخانه‌های استاندارد پایتون (هیچ نصبی لازم نیست)
- توکن و chat_id از متغیر محیطی خوانده می‌شود (هیچ‌وقت در کد نگذار!)
- حالت --dry-run برای تست بدون ارسال
- پشتیبانی از پروکسی (اگر از داخل ایران اجرا می‌کنی)

اجرا:
    export TELEGRAM_BOT_TOKEN="123456:ABC..."
    export TELEGRAM_CHAT_ID="123456789"
    python3 notify_telegram.py --digest            # ارسال خلاصه
    python3 notify_telegram.py --dry-run           # فقط نمایش
    python3 notify_telegram.py --test "سلام"       # تست ساده
"""
import json, os, sys, urllib.request, urllib.parse, html, argparse

API = "https://api.telegram.org"
MAXLEN = 3800

def _opener():
    """اگر پروکسی دادی، از آن استفاده کن (برای اجرا از داخل ایران لازم است)."""
    proxy = os.environ.get("TELEGRAM_PROXY") or os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if proxy:
        return urllib.request.build_opener(urllib.request.ProxyHandler({"https": proxy, "http": proxy}))
    return urllib.request.build_opener()

def send(text, token=None, chat_id=None, dry=False):
    token = token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID", "")
    if dry:
        print("─── [DRY-RUN] پیامی که ارسال می‌شد ───")
        print(text[:1200] + ("…" if len(text) > 1200 else ""))
        return {"ok": True, "dry": True}
    if not token or not chat_id:
        return {"ok": False, "error": "TELEGRAM_BOT_TOKEN یا TELEGRAM_CHAT_ID تنظیم نشده"}
    out = []
    for chunk in [text[i:i+MAXLEN] for i in range(0, len(text), MAXLEN)]:
        data = urllib.parse.urlencode({"chat_id": chat_id, "text": chunk,
                                       "parse_mode": "HTML", "disable_web_page_preview": "true"}).encode()
        req = urllib.request.Request(f"{API}/bot{token}/sendMessage", data=data)
        try:
            with _opener().open(req, timeout=30) as r:
                out.append(json.loads(r.read().decode()))
        except Exception as e:
            body = getattr(e, "read", lambda: b"")()
            return {"ok": False, "error": f"{type(e).__name__}: {e} {body[:200].decode('utf-8','replace') if body else ''}"}
    return {"ok": True, "sent": len(out)}

# ---------- ساخت متن خلاصه از گزارش موتور ----------
FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
def n(x):
    if x is None: return "—"
    return f"{int(x):,}".replace(",", "٬").translate(FA)
def money(x):
    x = float(x or 0)
    if x >= 1e9: return f"{n(round(x/1e9,1))} میلیارد"
    if x >= 1e6: return f"{n(round(x/1e6))} میلیون"
    if x >= 1e3: return f"{n(round(x/1e3))} هزار"
    return n(x)
def e(s): return html.escape(str(s or ""))

def build_digest(report_path):
    D = json.load(open(report_path, encoding="utf-8"))
    S, P, I = D["stats"], D["pairs"], D["intel"]
    L = [f"<b>🎯 فرصت‌های امروز ({n(len(P))} مورد)</b>", ""]
    for i, p in enumerate(P[:6], 1):
        L += [
          f"<b>{n(i)}. {e(p['vertical_fa'])} — امتیاز {n(round(p['score']*100))}</b>",
          f"🛒 خریدار: {e(p['need'][:90])}",
          f"   سقف خرید: <b>{n(p['buyer_price'])}</b> تومان",
          f"🏭 تأمین‌کننده: {e(p['seller_listing'][:70])} ({e(p['seller_city'])})",
          f"   قیمت: <b>{n(p['seller_price'])}</b> تومان | فاصله: {n(p['spread_per_kg'])} ت/کیلو",
          f"💰 پورسانت برآوردی: <b>{money(p['commission'])} تومان</b>",
          f"🔗 <a href=\"{e(p['buyer_url'])}\">آگهی خریدار</a> • <a href=\"{e(p['seller_url'])}\">آگهی فروشنده</a>",
          "",
        ]
    L += ["<b>📊 تصویر بازار (میانه قیمت هر کیلو)</b>"]
    for v in I.values():
        L.append(f"• {e(v['fa'])}: {n(v['median'])} تومان | {n(v['sellers'])} فروشنده / {n(v['buyers'])} خریدار")
    L += ["", f"🕵️ صف بررسی انسانی: {n(S['review'])} مورد (قیمت مشکوک — خودت چک کن)",
          f"📁 کل آگهی‌های بررسی‌شده: {n(S['unique'])}",
          "",
          "⚠️ اعداد «فرصت» هستند نه تضمین: قبل از هر پیشنهاد، حجم و اعتبار خریدار را تلفنی تأیید کن."]
    return "\n".join(L)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--digest", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--test", default="")
    ap.add_argument("--report", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "output/real_report.json"))
    a = ap.parse_args()

    if a.test:
        print(send(a.test, dry=a.dry_run))
    elif a.digest:
        if not os.path.exists(a.report):
            sys.exit(f"❌ گزارش پیدا نشد: {a.report} — اول real_pipeline.py را اجرا کن")
        msg = build_digest(a.report)
        print(send(msg, dry=a.dry_run))
    else:
        ap.print_help()
