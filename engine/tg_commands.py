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

HELP = """🎛️ <b>مرکز فرمان رهیاب + LALIGA OMNISCOUT</b>
کاربر: خودت (دیگران جواب نمی‌گیرند)

<b>فرمان‌های فارسی:</b>
• <b>محمد امین هستی</b> — قفل شدن روی مغز و شخصیت محمد امین حیدری 🐺
• <b>خروج از امین</b> — بازگشت به حالت عادی کارگزار
• <b>وضعیت</b> — خلاصه‌ی سیستم و داده‌ها
• <b>رادار</b> — دلار/طلا/سکه/کریپتو همین لحظه
• <b>قیمت</b> — پست کارت قیمت فوراً منتشر شود
• <b>فرصت</b> — پست فرصت‌ها فوراً منتشر شود
• <b>اسکن</b> — ۳ ساعت اخیر کانال‌های عمده
• <b>پست</b> — پست درس دلالی منتشر شود
• <b>اسکات</b> — اجرای فوری موتور LALIGA OMNISCOUT

<b>فرمان‌های رسمی LALIGA OMNISCOUT (بخش ۲۲):</b>
/start | /status | /opportunities | /urgent
/buyers | /sellers | /matches | /deal
/sourcehealth | /report | /city | /country
/category | /pause | /resume"""

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
    c_strip = cmd.strip()
    c_first = c_strip.split()[0].lower().split("@")[0] if c_strip else ""
    try:
        import amin_brain
        if any(k in c_strip for k in ("خروج از امین", "حالت عادی")) or c_first in ("/normal", "/exit_amin"):
            amin_brain.set_amin_mode(False)
            send("🔄 از حالت محمد امین حیدری خارج شدی و به مرکز فرمان رهیاب برگشتی."); return
        if "محمد امین هستی" in c_strip or "محمدامین هستی" in c_strip or c_first == "/amin":
            amin_brain.set_amin_mode(True)
            send(amin_brain.answer_as_amin(c_strip)); return
        if c_strip.startswith("امین:") or c_strip.startswith("امین "):
            send(amin_brain.answer_as_amin(c_strip)); return
    except Exception as e:
        print("amin check err:", type(e).__name__)
    if c_first in ("/start", "/status", "/opportunities", "/buyers", "/sellers", "/matches",
                   "/urgent", "/city", "/country", "/category", "/pause", "/resume",
                   "/report", "/sourcehealth", "/deal"):
        try:
            import omniscout
            ans = omniscout.handle_bot_command(c_strip)
            if ans:
                send(ans); return
        except Exception as e:
            send(f"⚠ خطای OMNISCOUT: {type(e).__name__}"); return
    if "اسکات" in cmd or "لالیگا" in cmd or c_first == "/omniscout":
        out = sh(["omniscout.py", "--send", "--force"]).strip()
        send("🌐 <b>LALIGA OMNISCOUT</b>\n" + (out[-1000:] or "✅ اجرا شد")); return
    if "راهنما" in cmd or c_strip in ("/help", "help"):
        send(HELP); return
    if "وضعیت" in cmd:
        try:
            rp = os.path.join(OUT, "real_report.json")
            D = json.load(open(rp, encoding="utf-8"))
            st = D.get("stats", {})
            n_sup = sum(1 for _ in open(os.path.join(OUT, "parts_suppliers.csv"), encoding="utf-8-sig")) - 1
            gen_at = D.get("generated_at") or datetime.fromtimestamp(os.path.getmtime(rp)).strftime("%Y-%m-%d %H:%M")
            send(f"📋 <b>وضعیت سیستم</b>\nآگهی بررسی‌شده: {st.get('unique', '?')}\n"
                 f"فرصت شناسایی‌شده: {st.get('pairs', '?')}\nتأمین‌کننده یدکی: {n_sup}\n"
                 f"کانال عمده فعال: ۷\nآخرین گزارش: {gen_at}")
        except Exception as e:
            send(f"⚠ خواندن وضعیت نشد ({type(e).__name__})"); return
    elif "کف قیمت" in c_strip or c_first == "/floor":
        try:
            import divar_floor_hunter as dfh
            body = re.sub(r"^(کف\s*قیمت|/floor)\s*", "", c_strip).strip()
            city_fa = "تهران"
            multi = False
            if " در " in body:
                parts = body.rsplit(" در ", 1)
                body, city_fa = parts[0].strip(), parts[1].strip()
            if city_fa in ("همه", "کل ایران", "ایران", "چند شهر"):
                multi = True
            q = body or "دیسک و صفحه پراید"
            res = dfh.analyze_floor_price(q, city_fa=city_fa, multi_city=multi)
            send(dfh.format_floor_report_tg(res)); return
        except Exception as e:
            send(f"⚠ خطا در استخراج کف قیمت دیوار: {type(e).__name__}"); return
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
        try:
            import amin_brain
            if amin_brain.is_amin_mode():
                send(amin_brain.answer_as_amin(c_strip)); return
        except Exception:
            pass
        send("🤔 نشناختم. بنویس «راهنما» یا «محمد امین هستی».")


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
