# -*- coding: utf-8 -*-
"""⚡ سرور فرمان زنده — Long-Polling تلگرام (بدون وب‌هوک، بدون سرور ابری، بدون کارت!)
داخل محیط خودمان اجرا می‌شود و تا وقتی بیدار است، فرمان‌ها را «لحظه‌ای» جواب می‌دهد.

اجرا:
    TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=... python3 tg_live.py
"""
import json, os, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "output"); os.makedirs(OUT, exist_ok=True)
SEEN = os.path.join(OUT, "tg_seen.json")

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT = str(os.environ.get("TELEGRAM_CHAT_ID", "")).strip()

def api(method, **params):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=70) as r:
        return json.load(r)

def main():
    if not TOKEN:
        print("⛔ توکن ربات تنظیم نشده — اجرا نشد."); return
    import tg_commands as tc          # همان هندلرهای فرمان (راهنما/رادار/وضعیت/...)
    print("⚡ سرور فرمان زنده روشن شد — منتظر پیام‌ها…", flush=True)

    last = 0
    if os.path.exists(SEEN):
        try: last = json.load(open(SEEN, encoding="utf-8")).get("last_id", 0)
        except Exception: pass
    # از آخرین پیام‌های مانده جلو نزنیم
    try:
        boot = api("getUpdates", offset=-1, timeout=0)
        for u in boot.get("result", []):
            last = max(last, u.get("update_id", 0))
    except Exception:
        pass
    json.dump({"last_id": last}, open(SEEN, "w", encoding="utf-8"))

    errors = 0
    while True:
        try:
            r = api("getUpdates", offset=last + 1, timeout=50,
                    allowed_updates=json.dumps(["message"]))
            errors = 0
            for u in r.get("result", []):
                last = max(last, u.get("update_id", 0))
                msg = u.get("message") or {}
                if str((msg.get("chat") or {}).get("id")) != CHAT:
                    continue
                txt = (msg.get("text") or "").strip()
                if not txt:
                    continue
                print(f"⌘ {txt}", flush=True)
                try:
                    tc.handle(txt)
                except Exception as e:
                    tc.send(f"⚠ خطا در اجرای فرمان ({type(e).__name__})")
            json.dump({"last_id": last}, open(SEEN, "w", encoding="utf-8"))
        except KeyboardInterrupt:
            print("خاموش شد."); break
        except Exception as e:
            errors += 1
            print(f"… خطای شبکه ({type(e).__name__}) — تلاش {errors}", flush=True)
            time.sleep(min(5 * errors, 60))

if __name__ == "__main__":
    main()
