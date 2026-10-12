# -*- coding: utf-8 -*-
"""
✅ تست اتصال — ساده‌ترین فایل پروژه.
کارش فقط یک چیز است: یک پیام تست به پیام‌رسان‌های تنظیم‌شده بفرستد.
اگر این کار کرد، یعنی «مسیر ارسال» از طرف تو به پیام‌رسان‌ها باز است و می‌توانیم
موتور کامل را روشن کنیم.

فقط پایتون استاندارد لازم دارد — هیچ نصبی لازم نیست.

اجرا در ترمینال (اختیاری، برای تست محلی):
    export TELEGRAM_BOT_TOKEN="123:ABC"
    export TELEGRAM_CHAT_ID="987654321"
    python3 send_test.py

اجرا روی گیت‌هاب: ورک‌فلوی 00-test-connection.yml همین فایل را صدا می‌زند.
"""
import json, os, sys, urllib.request, urllib.parse

FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

def guide(err_text):
    """تبدیل خطای خام به راهنمای فارسی قابل‌فهم برای مبتدی."""
    e = str(err_text)
    if "401" in e or "Unauthorized" in e:
        return "❌ توکن اشتباه است یا فاصله‌ی اضافه دارد.\n   راه‌حل: در BotFather بنویس /mybots → ربات → API Token → دوباره کپی کن (بدون فاصله)."
    if "chat not found" in e or "400" in e and "chat" in e:
        return "❌ ربات نمی‌تواند به این چت پیام بدهد.\n   راه‌حل: در تلگرام برو به ربات خودت و دکمه‌ی START را بزن. (یا اگر کانال است، ربات را ادمین کانال کن.)"
    if "403" in e or "Forbidden" in e:
        return "❌ دسترسی نداریم.\n   راه‌حل: ربات را در کانال ادمین کن یا به ربات پیام /start بده."
    if "timed out" in e or "timeout" in e or "unreachable" in e:
        return ("❌ سرور به API این پیام‌رسان نرسید (مسدود است).\n"
                "   این برای بله/روبیکا/ایتا روی سرورهای خارج از ایران معمول است.\n"
                "   راه‌حل: نود داخل ایران را بالا بیاور (iran_sender_node.py) یا از سرور ایرانی استفاده کن.")
    if "429" in e:
        return "❌ تعداد درخواست زیاد بود.\n   راه‌حل: چند دقیقه صبر کن و دوباره اجرا کن."
    return f"❌ خطای نامشخص: {e}"

def send(name, url, payload, is_json=False, headers=None):
    hdr = {"Content-Type": "application/json"} if is_json else {}
    hdr.update(headers or {})
    data = json.dumps(payload).encode() if is_json else urllib.parse.urlencode(payload).encode()
    try:
        req = urllib.request.Request(url, data=data, headers=hdr)
        with urllib.request.urlopen(req, timeout=25) as r:
            body = r.read().decode("utf-8", "replace")
        try: ok = json.loads(body).get("ok", json.loads(body).get("status") == "OK")
        except Exception: ok = True
        print(f"{'✅' if ok else '⚠️'} {name}: {'ارسال شد' if ok else body[:150]}")
        return bool(ok)
    except Exception as e:
        print(f"⛔ {name}:\n   {guide(e)}")
        return False

def main():
    text = ("✅ تست اتصال موفق\n"
            "این پیام از سیستم فرصت‌یاب خودکار ارسال شد.\n"
            "یعنی مسیر ارسال باز است و می‌توانیم سراغ موتور اصلی برویم.")

    found = False

    t = os.environ.get("TELEGRAM_BOT_TOKEN"); c = os.environ.get("TELEGRAM_CHAT_ID")
    if t and c:
        found = True
        send("تلگرام", f"https://api.telegram.org/bot{t}/sendMessage",
             {"chat_id": c, "text": text, "disable_web_page_preview": "true"})

    t = os.environ.get("BALE_BOT_TOKEN"); c = os.environ.get("BALE_CHAT_ID")
    if t and c:
        found = True
        send("بله", f"https://tapi.bale.ai/bot{t}/sendMessage", {"chat_id": c, "text": text})

    t = os.environ.get("RUBIKA_BOT_TOKEN"); c = os.environ.get("RUBIKA_CHAT_ID")
    if t and c:
        found = True
        send("روبیکا", f"https://botapi.rubika.ir/v3/{t}/sendMessage",
             {"chat_id": c, "text": text}, is_json=True)

    t = os.environ.get("EITAA_BOT_TOKEN"); c = os.environ.get("EITAA_CHAT_ID")
    if t and c:
        found = True
        base = os.environ.get("EITAA_API_BASE", "https://eitaayar.ir/api")
        send("ایتا", f"{base}/{t}/sendmessage", {"chat_id": c, "text": text})

    if not found:
        print("""⚠️ هیچ توکنی تنظیم نشده.

برای تلگرام (پیشنهادی برای شروع) این دو را در Secrets گیت‌هاب بگذار:
    TELEGRAM_BOT_TOKEN = توکنی که از @BotFather گرفتی
    TELEGRAM_CHAT_ID   = عددی که از @userinfobot گرفتی

بعد ورک‌فلوی «تست اتصال» را در تب Actions دستی اجرا کن.""")

if __name__ == "__main__":
    print("=" * 60)
    print("  تست اتصال به پیام‌رسان‌ها")
    print("=" * 60)
    main()
    print("=" * 60)
