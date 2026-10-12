# -*- coding: utf-8 -*-
"""
📡 ارسال به همه‌ی پیام‌رسان‌ها — تلگرام، بله، روبیکا، ایتا (ایتایار) — با یک اسکریپت.
هیچ کتابخانه‌ای لازم نیست (فقط پایتون استاندارد).

هر پلتفرم API ربات خودش را دارد:
  • تلگرام : https://api.telegram.org/bot<TOKEN>/sendMessage          (HTML پشتیبانی می‌شود)
  • بله    : https://tapi.bale.ai/bot<TOKEN>/sendMessage               (سازگار با تلگرام)
  • روبیکا : https://botapi.rubika.ir/v3/<TOKEN>/sendMessage           (JSON، متن ساده)
  • ایتا   : https://eitaayar.ir/api/<TOKEN>/sendMessage               (form، متن ساده)

نمونه‌ی اجرا:
    export BALE_BOT_TOKEN="..."      export BALE_CHAT_ID="123456789"
    export RUBIKA_BOT_TOKEN="..."    export RUBIKA_CHAT_ID="b0xxxxxxxx"
    export EITAA_BOT_TOKEN="..."     export EITAA_CHAT_ID="@my_channel"

    python3 notify_multi.py --test "سلام از ربات"        # تست همه‌ی پلتفرم‌های تنظیم‌شده
    python3 notify_multi.py --digest                     # فرستادن خلاصه‌ی فرصت‌ها
    python3 notify_multi.py --digest --only bale,rubika  # فقط بعضی پلتفرم‌ها
    python3 notify_multi.py --find-ids                   # پیدا کردن chat_id از getUpdates
    python3 notify_multi.py --digest --dry-run           # بدون ارسال واقعی

🚫 هرگز توکن‌ها را داخل کد نگذار — فقط متغیر محیطی (یا GitHub Secrets).
"""
import json, os, re, sys, html, argparse, urllib.request, urllib.parse

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
def strip(t): 
    t = re.sub(r"<a href=\"([^\"]+)\">([^<]+)</a>", r"\2 (\1)", t)
    return html.unescape(re.sub(r"<[^>]+>", "", t))

# ---------- لایه‌ی شبکه (با پشتیبانی پروکسی برای هر پلتفرم) ----------
def _open(req, proxy=None, timeout=30):
    if proxy:
        op = urllib.request.build_opener(urllib.request.ProxyHandler({"https": proxy, "http": proxy}))
    else:
        op = urllib.request.build_opener()
    with op.open(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))

def _post_json(url, payload, proxy=None):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    return _open(req, proxy)

def _post_form(url, payload, proxy=None):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(payload).encode())
    return _open(req, proxy)

# ---------- پیاده‌سازی هر پلتفرم ----------
def send_telegram(text, token=None, chat_id=None):
    token = token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id: return {"ok": False, "err": "توکن/چت‌آیدی تنظیم نشده"}
    try:
        r = _post_form(f"https://api.telegram.org/bot{token}/sendMessage",
                       {"chat_id": chat_id, "text": text, "parse_mode": "HTML",
                        "disable_web_page_preview": "true"})
        return {"ok": bool(r.get("ok")), "raw": r}
    except Exception as e:
        return {"ok": False, "err": f"{type(e).__name__}: {e}"}

def send_bale(text, token=None, chat_id=None):
    """بله سازگار با تلگرام است؛ برای اطمینان متن ساده می‌فرستیم."""
    token = token or os.environ.get("BALE_BOT_TOKEN", "")
    chat_id = chat_id or os.environ.get("BALE_CHAT_ID", "")
    if not token or not chat_id: return {"ok": False, "err": "توکن/چت‌آیدی تنظیم نشده"}
    proxy = os.environ.get("BALE_PROXY")
    try:
        r = _post_form(f"https://tapi.bale.ai/bot{token}/sendMessage",
                       {"chat_id": chat_id, "text": strip(text)}, proxy=proxy)
        return {"ok": bool(r.get("ok", r.get("result"))), "raw": r}
    except Exception as e:
        return {"ok": False, "err": f"{type(e).__name__}: {e}"}

def send_rubika(text, token=None, chat_id=None):
    token = token or os.environ.get("RUBIKA_BOT_TOKEN", "")
    chat_id = chat_id or os.environ.get("RUBIKA_CHAT_ID", "")
    if not token or not chat_id: return {"ok": False, "err": "توکن/چت‌آیدی تنظیم نشده"}
    proxy = os.environ.get("RUBIKA_PROXY")
    try:
        r = _post_json(f"https://botapi.rubika.ir/v3/{token}/sendMessage",
                       {"chat_id": chat_id, "text": strip(text)}, proxy=proxy)
        return {"ok": r.get("status") == "OK", "raw": r}
    except Exception as e:
        return {"ok": False, "err": f"{type(e).__name__}: {e}"}

def send_eitaa(text, token=None, chat_id=None):
    """ایتا (ایتایار). برای کانال: chat_id را بدون @ بده یا با @."""
    token = token or os.environ.get("EITAA_BOT_TOKEN", "")
    chat_id = chat_id or os.environ.get("EITAA_CHAT_ID", "")
    if not token or not chat_id: return {"ok": False, "err": "توکن/چت‌آیدی تنظیم نشده"}
    proxy = os.environ.get("EITAA_PROXY")           # ← اگر سرورت IP ایران ندارد، پروکسی ایرانی بده
    base = os.environ.get("EITAA_API_BASE", "https://eitaayar.ir/api")
    try:
        r = _post_form(f"{base}/{token}/sendmessage",
                       {"chat_id": chat_id, "text": strip(text)}, proxy=proxy)
        return {"ok": bool(r.get("ok")), "raw": r}
    except Exception as e:
        return {"ok": False, "err": f"{type(e).__name__}: {e}"}

def send_webhook(text, url=None, token=None):
    """پلتفرم سفارشی: هر سرویسی که یک URL می‌گیرد (گپ، سروش‌پلاس، گیت‌وی شخصی، وبهوک n8n/Make...)"""
    url = url or os.environ.get("WEBHOOK_URL", "")
    token = token or os.environ.get("WEBHOOK_TOKEN", "")
    if not url: return {"ok": False, "err": "WEBHOOK_URL تنظیم نشده"}
    try:
        hdr = {"Content-Type": "application/json"}
        if token: hdr["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(url, data=json.dumps({"text": strip(text)}).encode(), headers=hdr)
        with urllib.request.urlopen(req, timeout=30) as r:
            return {"ok": 200 <= r.status < 300, "raw": r.read()[:200].decode("utf-8", "replace")}
    except Exception as e:
        return {"ok": False, "err": f"{type(e).__name__}: {e}"}

# ---------- ارسال تصویر (multipart/form-data، بدون کتابخانه‌ی خارجی) ----------
def _multipart(fields, files):
    import mimetypes, uuid
    b = "----b2b" + uuid.uuid4().hex
    body = b""
    for k, v in fields.items():
        body += f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    for k, path in files.items():
        fn = os.path.basename(path)
        ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
        body += f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{fn}\"\r\nContent-Type: {ctype}\r\n\r\n".encode()
        body += open(path, "rb").read() + b"\r\n"
    body += f"--{b}--\r\n".encode()
    return body, f"multipart/form-data; boundary={b}"

def _post_photo(url, fields, photo_path, proxy=None, timeout=120):
    body, ctype = _multipart(fields, {"photo" if "sendPhoto" in url else "file": photo_path})
    req = urllib.request.Request(url, data=body, headers={"Content-Type": ctype})
    op = (urllib.request.build_opener(urllib.request.ProxyHandler({"https": proxy, "http": proxy}))
          if proxy else urllib.request.build_opener())
    with op.open(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))

def photo_telegram(path, caption, token=None, chat_id=None):
    token = token or os.environ.get("TELEGRAM_BOT_TOKEN", ""); chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id: return {"ok": False, "err": "تنظیم نشده"}
    try:
        r = _post_photo(f"https://api.telegram.org/bot{token}/sendPhoto",
                        {"chat_id": chat_id, "caption": strip(caption)[:1000], "parse_mode": "HTML"}, path)
        return {"ok": bool(r.get("ok")), "raw": r}
    except Exception as e: return {"ok": False, "err": f"{type(e).__name__}: {e}"}

def photo_bale(path, caption, token=None, chat_id=None):
    token = token or os.environ.get("BALE_BOT_TOKEN", ""); chat_id = chat_id or os.environ.get("BALE_CHAT_ID", "")
    if not token or not chat_id: return {"ok": False, "err": "تنظیم نشده"}
    try:
        r = _post_photo(f"https://tapi.bale.ai/bot{token}/sendPhoto",
                        {"chat_id": chat_id, "caption": strip(caption)[:1000]}, path, proxy=os.environ.get("BALE_PROXY"))
        return {"ok": bool(r.get("ok", r.get("result"))), "raw": r}
    except Exception as e: return {"ok": False, "err": f"{type(e).__name__}: {e}"}

def photo_eitaa(path, caption, token=None, chat_id=None):
    token = token or os.environ.get("EITAA_BOT_TOKEN", ""); chat_id = chat_id or os.environ.get("EITAA_CHAT_ID", "")
    if not token or not chat_id: return {"ok": False, "err": "تنظیم نشده"}
    base = os.environ.get("EITAA_API_BASE", "https://eitaayar.ir/api")
    try:
        r = _post_photo(f"{base}/{token}/sendfile",
                        {"chat_id": chat_id, "caption": strip(caption)[:1000]}, path, proxy=os.environ.get("EITAA_PROXY"))
        return {"ok": bool(r.get("ok")), "raw": r}
    except Exception as e: return {"ok": False, "err": f"{type(e).__name__}: {e}"}

def photo_rubika(path, caption, token=None, chat_id=None):
    """بهترین‌تلاش: روبیکا برای فایل متد sendFile دارد؛ اگر نسخه‌ی API متفاوت بود، متن جایگزین می‌شود."""
    token = token or os.environ.get("RUBIKA_BOT_TOKEN", ""); chat_id = chat_id or os.environ.get("RUBIKA_CHAT_ID", "")
    if not token or not chat_id: return {"ok": False, "err": "تنظیم نشده"}
    try:
        body, ctype = _multipart({"chat_id": chat_id, "caption": strip(caption)[:1000]}, {"file": path})
        req = urllib.request.Request(f"https://botapi.rubika.ir/v3/{token}/sendFile", data=body,
                                     headers={"Content-Type": ctype})
        with urllib.request.urlopen(req, timeout=120) as r:
            res = json.loads(r.read().decode("utf-8", "replace"))
        return {"ok": res.get("status") == "OK", "raw": res}
    except Exception as e: return {"ok": False, "err": f"{type(e).__name__}: {e}"}

PHOTO_SENDERS = {
    "telegram": photo_telegram, "bale": photo_bale, "eitaa": photo_eitaa, "rubika": photo_rubika,
}

def publish_channel(text, path=None):
    """ارسال به کانال (اگر KANAL_CHAT_ID تنظیم شده باشد)"""
    ch = os.environ.get("KANAL_CHAT_ID", "")
    if not ch: return {}
    if path and os.path.exists(path):
        return {"channel": photo_telegram(path, text, chat_id=ch)}
    return {"channel": send_telegram(text, chat_id=ch)}

def broadcast_photo(path, caption, only=None, dry=False, fallback_text=True):
    """تصویر + کپشن به همه‌ی پلتفرم‌های تنظیم‌شده. اگر ارسال تصویر نشد، متن می‌فرستد."""
    targets = only or configured()
    if not targets:
        print("⚠ هیچ پلتفرمی تنظیم نشده — حالت خشک"); print("─── کپشن ───"); print(strip(caption)[:600]); return {}
    out = {}
    for p in targets:
        if dry:
            print(f"─── [DRY-RUN:{p}] تصویر {os.path.basename(path)} + کپشن ───")
            print(strip(caption)[:300] + "…"); out[p] = {"ok": True, "dry": True}; continue
        if p in PHOTO_SENDERS:
            r = PHOTO_SENDERS[p](path, caption)
            if not r.get("ok") and fallback_text:
                print(f"   ↩ {p}: تصویر نشد ({r.get('err','')[:60]}) → متن می‌فرستم")
                r = PLATFORMS[p][0](caption)
        else:
            r = PLATFORMS[p][0](caption)
        out[p] = r
        print(f"{'✅' if r.get('ok') else '⛔'} {p}: {'تصویر+متن ارسال شد' if r.get('ok') else r}")
    return out

PLATFORMS = {
    "telegram": (send_telegram, "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", 4000),
    "bale":     (send_bale,     "BALE_BOT_TOKEN",     "BALE_CHAT_ID",     4000),
    "rubika":   (send_rubika,   "RUBIKA_BOT_TOKEN",   "RUBIKA_CHAT_ID",   4000),
    "eitaa":    (send_eitaa,    "EITAA_BOT_TOKEN",    "EITAA_CHAT_ID",    4000),
    "webhook":  (send_webhook,  "WEBHOOK_URL",        "WEBHOOK_URL",      4000),
}

def configured():
    return [p for p, (_, tk, ck, _) in PLATFORMS.items() if os.environ.get(tk) and os.environ.get(ck)]

def via_relay(text, url, secret, only=None, timeout=60):
    """ارسال از طریق «نود داخل ایران» — وقتی APIهای ایرانی به IP ما اجازه نمی‌دهند."""
    import urllib.request as u
    payload = json.dumps({"text": text, "only": only}).encode()
    req = u.Request(url.rstrip("/") + "/send", data=payload,
                    headers={"Content-Type": "application/json", "X-Auth": secret})
    try:
        with u.urlopen(req, timeout=timeout) as r:
            res = json.loads(r.read().decode())
        print(("✅" if res.get("ok") else "⛔") + f" رله: {res}")
        return res
    except Exception as e:
        print(f"⛔ رله در دسترس نیست: {type(e).__name__}: {e}")
        return {"ok": False, "err": str(e)}

def broadcast(text, only=None, dry=False):
    targets = only or configured()
    if not targets:
        print("⚠ هیچ پلتفرمی تنظیم نشده (توکن و chat_id را ست کن) — حالت خشک اجرا می‌شود")
        print("─── متن پیام ───"); print(strip(text)[:800]); return {}
    out = {}
    for p in targets:
        fn, _, _, limit = PLATFORMS[p]
        if dry:
            print(f"─── [DRY-RUN:{p}] ───"); print(strip(text)[:400] + "…"); out[p] = {"ok": True, "dry": True}; continue
        chunks = [text[i:i+limit] for i in range(0, len(text), limit)] or [text]
        res = [fn(c) for c in chunks]
        ok = all(r.get("ok") for r in res)
        out[p] = {"ok": ok, "results": res if not ok else len(res)}
        print(f"{'✅' if ok else '⛔'} {p}: {'ارسال شد' if ok else res}")
    return out

# ---------- پیدا کردن chat_id از getUpdates ----------
def find_ids():
    print("🔎 تلاش برای پیدا کردن chat_id (اول به ربات در همان پیام‌رسان پیام بده!)\n")
    t = os.environ.get("TELEGRAM_BOT_TOKEN")
    if t:
        try:
            r = _open(urllib.request.Request(f"https://api.telegram.org/bot{t}/getUpdates"))
            for u in r.get("result", [])[:5]:
                c = (u.get("message") or u.get("channel_post") or {}).get("chat", {})
                print(f"  تلگرام → chat_id = {c.get('id')} ({c.get('title') or c.get('first_name','')})")
        except Exception as e: print("  تلگرام: خطا —", e)
    t = os.environ.get("BALE_BOT_TOKEN")
    if t:
        try:
            r = _open(urllib.request.Request(f"https://tapi.bale.ai/bot{t}/getUpdates"))
            for u in (r.get("result") or [])[:5]:
                c = (u.get("message") or {}).get("chat", {})
                print(f"  بله    → chat_id = {c.get('id')} ({c.get('title') or c.get('first_name','')})")
        except Exception as e: print("  بله: خطا —", e)
    t = os.environ.get("RUBIKA_BOT_TOKEN")
    if t:
        try:
            r = _post_json(f"https://botapi.rubika.ir/v3/{t}/getUpdates", {})
            for ch in ((r.get("data") or {}).get("chats") or [])[:5]:
                print(f"  روبیکا → chat_id = {ch.get('object_guid')} ({ch.get('title') or ch.get('first_name','')})")
        except Exception as e: print("  روبیکا: خطا —", e)
    print("\n💡 ایتا: برای کانال، آیدی کانال (بدون @) را در EITAA_CHAT_ID بگذار؛ برای کاربر، اول باید کاربر ربات را /start کند.")

# ---------- خلاصه‌ی فرصت‌ها ----------
def build_digest(report_path):
    D = json.load(open(report_path, encoding="utf-8"))
    S, P, I = D["stats"], D["pairs"], D["intel"]
    shown = P[:6]
    head = (f"<b>🎯 {n(len(shown))} فرصت برتر</b> — از مجموع {n(len(P))} فرصت شناسایی‌شده" if len(P) > len(shown)
            else f"<b>🎯 {n(len(P))} فرصت امروز</b>")
    L = [head, ""]
    for i, p in enumerate(shown, 1):
        L += [f"<b>{n(i)}. {p['vertical_fa']} — امتیاز {n(round(p['score']*100))}</b>",
              f"🛒 خریدار: {p['need'][:85]} | سقف: {n(p['buyer_price'])} تومان",
              f"🏭 فروشنده: {p['seller_listing'][:60]} ({p['seller_city']}) | {n(p['seller_price'])} تومان",
              f"💰 فاصله: {n(p['spread_per_kg'])} ت/کیلو → پورسانت {money(p['commission'])} تومان",
              f"🔗 {p['seller_url']}", ""]
    L += ["<b>📊 میانه قیمت بازار</b>"]
    for v in I.values():
        L.append(f"• {v['fa']}: {n(v['median'])} تومان ({n(v['sellers'])} عرضه / {n(v['buyers'])} تقاضا)")
    if len(P) > len(shown):
        L.append(f"📄 فهرست کامل {n(len(P))} مورد در فایل real_opportunities.csv است.")
    L += ["", f"🕵️ صف بررسی انسانی: {n(S['review'])} مورد",
          "⚠️ قبل از پیشنهاد به دو طرف، حجم و اعتبار خریدار را تلفنی تأیید کن."]
    return "\n".join(L)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="ارسال به تلگرام/بله/روبیکا/ایتا")
    ap.add_argument("--test", default="")
    ap.add_argument("--digest", action="store_true")
    ap.add_argument("--report", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "output/real_report.json"))
    ap.add_argument("--only", default="")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--find-ids", action="store_true")
    ap.add_argument("--via-relay", metavar="URL", default=os.environ.get("RELAY_URL", ""),
                    help="ارسال از طریق نود داخل ایران (RELAY_URL)")
    a = ap.parse_args()

    only = [x for x in a.only.split(",") if x] or None
    if a.find_ids:
        find_ids()
    elif a.test:
        txt = f"🤖 تست اتصال ربات\n{a.test}"
        if a.via_relay and not a.dry_run:
            via_relay(txt, a.via_relay, os.environ.get("RELAY_SECRET", ""), only)
        else:
            broadcast(txt, only=only, dry=a.dry_run)
    elif a.digest:
        if not os.path.exists(a.report): sys.exit(f"❌ گزارش پیدا نشد: {a.report}")
        txt = build_digest(a.report)
        if a.via_relay and not a.dry_run:
            via_relay(txt, a.via_relay, os.environ.get("RELAY_SECRET", ""), only)
        else:
            broadcast(txt, only=only, dry=a.dry_run)
    else:
        ap.print_help()
        print(f"\nپلتفرم‌های تنظیم‌شده: {configured() or 'هیچ‌کدام'}")
