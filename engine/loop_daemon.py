# -*- coding: utf-8 -*-
"""
🔁 دیمن رهیاب — ارسال مستقیم از همین محیط، بدون گیت‌هاب.
تا وقتی این محیط زنده است، خودش می‌گردد و به تلگرام تو می‌فرستد.
مناسب برای اثبات مفهوم و کار فوری. برای ۲۴/۷ پایدار، همان گیت‌هاب یا ماشین خودت لازم است.

اجرا:  python3 loop_daemon.py --hours 15 --interval 15
"""
import os, sys, time, json, argparse, traceback
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import settings

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "output", "daemon.log")
os.makedirs(os.path.join(HERE, "output"), exist_ok=True)

def log(msg):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f: f.write(line + "\n")

def tehran_hour():
    """ساعت تهران = UTC + 3:30 (ایران از ۱۴۰۱ ساعت تابستانی ندارد)"""
    import datetime as dt
    return (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=3, minutes=30)).hour

def is_quiet_hours():
    """سکوت بین ۲۳ شب تا ۷ صبح تهران"""
    h = tehran_hour()
    return h >= 23 or h < 7

def tick(n):
    """یک دور: جست‌وجوی آگهی تازه + ارسال"""
    try:
        from hot_alert import run as hot_run
        hits = hot_run(dry=False, rotation=n["tick"] % 2)
        n["hot_sent"] += len(hits)
        log(f"⚡ دور {n['tick']}: {len(hits)} هشدار تازه ارسال شد")
    except Exception as e:
        log(f"⛔ خطا در هشدار: {type(e).__name__}: {e}")

def side_jobs(n):
    """کارهای دوره‌ای دیمن: نقشه‌ی شهرها (۲۴ ساعت) + لیست تأمین‌کننده‌ها (۱۲ ساعت)"""
    try:
        if n["tick"] >= 5 and (n["tick"] - 5) % 96 == 0:      # هر ۲۴ ساعت (اولین‌بار دور ۵)
            log("🗺 شروع تحلیل شهر به شهر (۲۴ ساعتی)")
            import subprocess
            r = subprocess.run([sys.executable, "city_report.py"], cwd=HERE,
                               capture_output=True, text=True, timeout=900)
            log("🗺 گزارش شهر به شهر ارسال شد" if r.returncode == 0 else f"⛔ خطای تحلیل شهرها: {r.stderr[-200:]}")
        if n["tick"] >= 8 and (n["tick"] - 8) % 48 == 0:      # هر ۱۲ ساعت (اولین‌بار دور ۸)
            import subprocess
            r = subprocess.run([sys.executable, "collect_parts_suppliers.py"], cwd=HERE,
                               capture_output=True, text=True, timeout=900)
            tail = [l for l in (r.stdout or "").split("\n") if "تأمین‌کننده" in l]
            log("🏪 لیست تأمین‌کننده‌ها به‌روز شد: " + (tail[0].strip() if tail else "?"))
    except Exception as e:
        log(f"⛔ خطا در کارهای دوره‌ای: {type(e).__name__}: {e}")

def digest(n, force=False):
    """دیجست فقط وقتی محتوای تازه‌ای هست یا بیش از ۲۴ ساعت سکوت بوده"""
    try:
        import hot_alert
        from notify_multi import broadcast, build_digest
        has_news = force or getattr(hot_alert, "LAST_NEW", 0) > 0
        # اگر گزارش قدیمی است، تازه‌سازی
        rp = os.path.join(HERE, "output/real_report.json")
        if os.path.exists(rp) and (time.time() - os.path.getmtime(rp)) > 3*3600:
            import subprocess
            subprocess.run([sys.executable, "real_pipeline.py", "--offline"], cwd=HERE, timeout=180)
        if not has_news:
            log(f"💤 دیجست نفرستادم — چیز تازه‌ای نبود (دور {n['tick']})")
            return False
        if os.path.exists(rp):
            broadcast(build_digest(rp)); log("📊 دیجست ارسال شد (محتوای تازه داشت)"); return True
    except Exception as e:
        log(f"⛔ خطا در دیجست: {type(e).__name__}: {e}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=15)
    ap.add_argument("--interval", type=int, default=None)
    a = ap.parse_args()

    interval = a.interval or settings.get("hot_alert", "حداکثر_عمر_دقیقه", 90) // 6 or 15
    interval = max(5, int(interval))
    log(f"🚀 دیمن رهیاب شروع شد | هر {interval} دقیقه | به مدت {a.hours} ساعت")
    log(f"   فعال: هشدار={settings.get('hot_alert','فعال')} دیجست={settings.get('digest','فعال')}")

    t0, n = time.time(), {"tick": 0, "hot_sent": 0}
    digest_hours = max(1, settings.get("digest", "هر_چند_ساعت", 12))
    last_digest = None
    log(f"   دیجست هر {digest_hours} ساعت و فقط وقتی محتوای تازه باشد")
    end = t0 + a.hours*3600

    while time.time() < end:
        tick_start = time.time()
        n["tick"] += 1
        if is_quiet_hours() and n["tick"] > 1:
            log(f"🌙 ساعت سکوت ({tehran_hour()}:۰۰ تهران) — دور {n['tick']} رد شد")
        else:
            tick(n)
            side_jobs(n)
            if settings.get("digest", "فعال", True):
                due = last_digest is None or (time.time() - last_digest) >= digest_hours * 3600
                if due and getattr(__import__("hot_alert"), "LAST_NEW", 0) > 0:
                    digest(n); last_digest = time.time()
        # اسکن خودش ~۳ دقیقه طول می‌کشد؛ پس فاصله را جبران می‌کنیم تا چرخه دقیقاً «interval» دقیقه باشد
        elapsed = time.time() - tick_start
        wait = max(60, interval * 60 - elapsed)
        log(f"⏳ دور بعدی {int(wait//60)} دقیقه و {int(wait%60)} ثانیه دیگر ({int(elapsed)} ثانیه اسکن شد)")
        time.sleep(wait)
    log(f"🏁 پایان دیمن | {n['tick']} دور | {n['hot_sent']} هشدار")
