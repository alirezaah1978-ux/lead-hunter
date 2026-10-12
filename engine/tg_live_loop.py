# -*- coding: utf-8 -*-
"""⚡ حلقه‌ی زنده‌ی ربات روی GitHub Actions — جواب در چند ثانیه، ۲۴/۷
به مدت «LOOP_SECONDS» (پیش‌فرض ~۵ ساعت و ۴۰ دقیقه) به تلگرام وصل می‌ماند،
بعد خودش اجرای بعدی را می‌سازد (زنجیره) → عملاً همیشه روشن، رایگان، بدون سرور.
"""
import json, os, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT = str(os.environ.get("TELEGRAM_CHAT_ID", "")).strip()
LOOP = int(os.environ.get("LOOP_SECONDS", "20400"))     # ~۵:۴۰
PAT = os.environ.get("GH_PAT", "").strip()
REPO = os.environ.get("GH_REPO", "alirezaah1978-ux/lead-hunter")
WF = "live-bot.yml"

def api(method, **params):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=70) as r:
        return json.load(r)

def dispatch_next():
    if not PAT:
        print("ℹ GH_PAT نیست — اجرای بعدی با زمان‌بندی می‌آید"); return
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/actions/workflows/{WF}/dispatches",
            data=json.dumps({"ref": "main"}).encode(),
            headers={"Authorization": f"token {PAT}", "Accept": "application/vnd.github+json",
                     "User-Agent": "rahyaab"}, method="POST")
        urllib.request.urlopen(req, timeout=25)
        print("🔁 اجرای بعدی زنجیر شد")
    except Exception as e:
        print("⚠ زنجیر نشد:", type(e).__name__)

def main():
    if not TOKEN:
        print("⛔ توکن نیست"); return
    import tg_commands as tc
    # از انبار عقب‌مانده رد شو
    last = 0
    try:
        for u in api("getUpdates", offset=-1, timeout=0).get("result", []):
            last = max(last, u.get("update_id", 0))
    except Exception:
        pass
    start = time.time()
    print(f"⚡ حلقه‌ی زنده شروع شد — {LOOP//60} دقیقه", flush=True)
    while time.time() - start < LOOP:
        try:
            r = api("getUpdates", offset=last + 1, timeout=50,
                    allowed_updates=json.dumps(["message"]))
            for u in r.get("result", []):
                last = max(last, u.get("update_id", 0))
                msg = u.get("message") or {}
                if str((msg.get("chat") or {}).get("id")) != CHAT:
                    continue
                txt = (msg.get("text") or "").strip()
                if not txt:
                    continue
                print("⌘", txt, flush=True)
                try:
                    tc.handle(txt)
                except Exception as e:
                    tc.send(f"⚠ خطا در فرمان ({type(e).__name__})")
        except Exception as e:
            print("… شبکه:", type(e).__name__, flush=True)
            time.sleep(4)
    print("⏰ پایان دوره — زنجیر کردن اجرای بعدی", flush=True)
    dispatch_next()

if __name__ == "__main__":
    main()
