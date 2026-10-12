# -*- coding: utf-8 -*-
"""📡 رادار زنده‌ی دارایی‌ها (منبع: tgju — از سندباکس تست شد و کار می‌کند)
فقط داده و هشدار عددی — نه توصیه‌ی خرید/فروش (سیگنال‌فروشی طبق قانون جرم است؛ این محصول «داده» است نه «سیگنال»).

استفاده:
  python3 radar.py            # وضعیت + هشدارهای مشروط (بدون ارسال به هیچ‌جا)
  python3 radar.py --send     # ارسال هشدارها به تلگرام (وقتی توکن/چت ست باشد)

استقرار آینده (بعد از تأیید کاربر): ورک‌فلوی GitHub Actions با cron هر ۳۰ دقیقه در ساعات بازار.
"""
import json, os, re, sys, time, urllib.request

KEYS = {
    "price_dollar_rl": ("دلار آمریکا", 0.8),
    "price_eur":       ("یورو", 0.8),
    "geram18":         ("گرم طلای ۱۸", 0.8),
    "sekeb":           ("سکه امامی", 1.0),
    "nim":             ("نیم سکه", 1.0),
    "rob":             ("ربع سکه", 1.0),
    "crypto-bitcoin":  ("بیت‌کوین", 2.0),
    "crypto-ethereum": ("اتریوم", 2.5),
}
URL = "https://api.tgju.org/v1/market/indicator/summary-table-data/{k}"
STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "radar_last.json")

def clean(s):
    s = re.sub(r"<[^>]+>", "", s).replace(",", "").replace("%", "").replace("٪", "").strip()
    return float(s) if s not in ("", "-") else 0.0

def fetch(k):
    req = urllib.request.Request(URL.format(k=k), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        d = json.load(r)
    row = d["data"][0]
    return {"price": clean(row[0]), "open": clean(row[1]), "high": clean(row[2]),
            "low": clean(row[3]), "chg": clean(row[4]), "pct": clean(row[5]),
            "date": row[6], "jdate": row[7]}

def main():
    send = "--send" in sys.argv
    prev = {}
    if os.path.exists(STATE):
        prev = json.load(open(STATE, encoding="utf-8"))
    now, alerts, lines = {}, [], []
    for k, (fa, th) in KEYS.items():
        try:
            v = fetch(k)
        except Exception as e:
            lines.append(f"… {fa}: خطای دریافت ({type(e).__name__})"); continue
        if not k.startswith("crypto"):  # tgju برای طلا/ارز/سکه ریال می‌دهد → تومان
            v["price"] /= 10; v["open"] /= 10; v["high"] /= 10; v["low"] /= 10; v["chg"] /= 10
        now[k] = v
        arrow = "▲" if v["pct"] > 0 else ("▼" if v["pct"] < 0 else "=")
        unit = "$" if k.startswith("crypto") else "ت"
        lines.append(f"{fa}: {v['price']:,.0f} {unit}  {arrow}{v['pct']:+.2f}٪")
        if abs(v["pct"]) >= th:
            unit = "$" if k.startswith("crypto") else " تومان"
            alerts.append(f"⚡ {fa}: {arrow}{v['pct']:+.2f}٪ — {v['price']:,.0f}{unit}")
        p = prev.get(k)
        if p and p.get("price") and abs(v["price"] - p["price"]) / p["price"] * 100 >= th:
            alerts.append(f"🔸 {fa}: تغییر {v['price'] - p['price']:+,.0f} از اجرای قبلی")
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(now, open(STATE, "w", encoding="utf-8"), ensure_ascii=False)
    print("📡 رادار —", time.strftime("%Y-%m-%d %H:%M"))
    print("\n".join(lines))
    print("\n🚨 هشدارهای مشروط:" if alerts else "\n✅ هشدار مشروطی فعال نیست.")
    for a in alerts:
        print("  " + a)
    if send and alerts:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import notify_multi as nm
        r = nm.send_telegram("📡 <b>رادار دارایی‌ها</b>\n\n" + "\n".join(alerts))
        print("\nارسال:", r.get("ok", r))
    elif alerts:
        print("\n(حالت نمایش — چیزی ارسال نشد. برای ارسال: --send)")

if __name__ == "__main__":
    main()
