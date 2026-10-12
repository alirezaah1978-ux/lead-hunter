# -*- coding: utf-8 -*-
"""🎛️ مرکز فرمان تلگرام — نسخه‌ی واسطه‌محور (بدون n8n!)
ربات هر اجرا پیام‌های تازه‌ی تو را می‌خواند و به فرمان‌ها جواب می‌دهد.
روی GitHub Actions هر ۱۰ دقیقه اجرا می‌شود → عملاً «وب‌هوک بدون سرور».

فرمان‌های فارسی: راهنما | وضعیت | رادار | قیمت | فرصت | اسکن | پست
"""
import json, os, re, subprocess, sys, urllib.parse, urllib.request
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
SEEN = os.path.join(OUT, "tg_seen.json")
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT = str(os.environ.get("TELEGRAM_CHAT_ID", "")).strip()

HELP = """🎛️ <b>مرکز فرمان رهیاب</b>
کاربر: خودت (دیگران جواب نمی‌گیرند)
فرمان‌ها:
• <b>وضعیت</b> — خلاصه‌ی سیستم و داده‌ها
• <b>رادار</b> — دلار/طلا/سکه/کریپتو همین لحظه
• <b>قیمت</b> — پست کارت قیمت فوراً منتشر شود
• <b>فرصت</b> — پست فرصت‌ها فوراً منتشر شود
• <b>اسکن</b> — ۳ ساعت اخیر کانال‌های عمده
• <b>پست</b> — پست درس دلالی منتشر شود
• <b>راهنما</b> — همین متن"""

def api(method, **params):
    if not TOKEN:
        print("⛔ توکن ربات نیست"); sys.exit(0)
    url = f"https://api.telegram.org/bot{TOKEN}/{method}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)

def send(text):
    text = str(text)[:3900]
    try:
        api("sendMessage", chat_id=CHAT, text=text, parse_mode="HTML",
            disable_web_page_preview="true")
    except Exception:
        try:
            clean = re.sub(r"<[^>]*>", " ", text)
            api("sendMessage", chat_id=CHAT, text=clean[:3900], disable_web_page_preview="true")
        except Exception as e:
            print("send failed:", type(e).__name__)

def sh(args):
    try:
        p = subprocess.run([sys.executable] + args, cwd=HERE, capture_output=True, text=True, timeout=280)
        return (p.stdout or "") + (p.stderr or "")
    except Exception as e:
        return f"خطا: {type(e).__name__}"

def handle(cmd):
    if "راهنما" in cmd or cmd.strip() in ("/help", "help", "/start"):
        send(HELP); return
    if "وضعیت" in cmd:
        try:
            D = json.load(open(os.path.join(OUT, "real_report.json"), encoding="utf-8"))
            st = D.get("stats", {})
            n_sup = sum(1 for _ in open(os.path.join(OUT, "parts_suppliers.csv"), encoding="utf-8-sig")) - 1
            send(f"📋 <b>وضعیت سیستم</b>\nآگهی بررسی‌شده: {st.get('unique', '?')}\n"
                 f"فرصت شناسایی‌شده: {st.get('pairs', '?')}\nتأمین‌کننده یدکی: {n_sup}\n"
                 f"کانال عمده فعال: ۷\nآخرین گزارش: {D.get('generated_at', '?')}")
        except Exception as e:
            send(f"⚠ خواندن وضعیت نشد ({type(e).__name__})"); return
    elif "رادار" in cmd:
        out = sh(["radar.py"]).strip()
        send("📡 <b>رادار</b>\n<pre>" + out[:3300] + "</pre>"); return
    elif "قیمت" in cmd:
        out = sh(["content_post.py", "--type", "price", "--force"])
        send("✅ پست کارت قیمت ارسال شد." if "✅" in out or "نتیجه" in out else "⚠ " + out[-300:]); return
    elif "فرصت" in cmd:
        out = sh(["content_post.py", "--type", "opps", "--force"])
        send("✅ پست فرصت‌ها ارسال شد." if "نتیجه" in out or "✅" in out else "⚠ " + out[-300:]); return
    elif "پست" in cmd or "درس" in cmd:
        out = sh(["content_post.py", "--type", "insight", "--force"])
        send("✅ پست درس دلالی ارسال شد." if "نتیجه" in out or "✅" in out else "⚠ " + out[-300:]); return
    elif "اسکن" in cmd:
        out = sh(["omde_scan.py", "--hours", "3"])
        tail = out.strip().splitlines()[-14:]
        send("🔎 <b>اسکن عمده (۳ ساعت)</b>\n<pre>" + "\n".join(tail)[:3300] + "</pre>"); return
    else:
        send("🤔 نشناختم. بنویس «راهنما».")


def ensure_live_bot():
    """اگر «ربات زنده» خاموش شده باشد، دوباره روشنش می‌کند (خوددرمانی)."""
    pat = os.environ.get("GH_PAT", "").strip()
    repo = os.environ.get("GH_REPO", "alirezaah1978-ux/lead-hunter")
    if not pat: return
    H = {"Authorization": f"token {pat}", "Accept": "application/vnd.github+json",
         "User-Agent": "rahyaab"}
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/actions/workflows/live-bot.yml/runs?per_page=5",
            headers=H)
        with urllib.request.urlopen(req, timeout=25) as r:
            runs = json.load(r).get("workflow_runs", [])
        if any(x.get("status") in ("in_progress", "queued", "pending") for x in runs):
            print("✅ ربات زنده فعال است")
            return
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/actions/workflows/live-bot.yml/dispatches",
            data=json.dumps({"ref": "main"}).encode(),
            headers={**H, "Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=25)
        print("🔁 نگهبان: ربات زنده دوباره روشن شد")
    except Exception as e:
        print("watchdog:", type(e).__name__)

def main():
    os.makedirs(OUT, exist_ok=True)
    seen = {"last_id": 0}
    if os.path.exists(SEEN):
        try: seen = json.load(open(SEEN, encoding="utf-8"))
        except Exception: pass
    r = api("getUpdates", offset=seen.get("last_id", 0) + 1, timeout=0)
    msgs = r.get("result", [])
    n = 0
    for m in msgs:
        seen["last_id"] = max(seen["last_id"], m.get("update_id", 0))
        msg = m.get("message") or {}
        if str((msg.get("chat") or {}).get("id")) != CHAT:
            continue  # فقط فرمان‌های مالک
        txt = (msg.get("text") or "").strip()
        if txt:
            print("⌘", txt); handle(txt); n += 1
    json.dump(seen, open(SEEN, "w", encoding="utf-8"), ensure_ascii=False)
    try:
        hb = os.path.join(OUT, "heartbeat.txt")
        today = datetime.now().strftime("%Y-%m-%d")
        if not os.path.exists(hb) or open(hb, encoding="utf-8").read().strip().split()[0] != today:
            open(hb, "w", encoding="utf-8").write(f"{today} {datetime.now():%H:%M} رهیاب زنده است")
    except Exception: pass
    ensure_live_bot()
    print(f"✅ {n} فرمان پردازش شد — {datetime.now():%H:%M}")

if __name__ == "__main__":
    main()
