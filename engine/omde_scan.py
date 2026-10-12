# -*- coding: utf-8 -*-
"""🔎 اسکنر عمده‌فروشی تلگرام — فقط پست‌های «به‌لحظه» (پیش‌فرض: ۲۴ ساعت اخیر)
از پیش‌نمایش عمومی کانال‌ها (t.me/s) می‌خواند: بدون لاگین، بدون اکانت.

اجرا:
    python3 omde_scan.py                 # همه کانال‌ها، پست‌های ۲۴ ساعت اخیر
    python3 omde_scan.py --hours 6       # فقط ۶ ساعت اخیر
    python3 omde_scan.py --channels salehabad --csv out.csv

خروجی: چاپ خلاصه + فایل CSV (output/omde_live.csv)
"""
import argparse, csv, json, os, re, sys, time, urllib.request
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output"); os.makedirs(OUT, exist_ok=True)

CHANNELS = {
    "salehabad":          ("صالح‌آباد — عمده عمومی (لوازم خانگی/آشپزخانه/اسباب‌بازی)", "تهران"),
    "poshakmarofi":       ("پوشاک زنانه معروفی", "بانه"),
    "hana_omde":          ("پوشاک بچگانه هانا", "بانه"),
    "arayeshi_rahimpoor": ("آرایشی‌بهداشتی رحیم‌پور", "بانه"),
    "azizi1960":          ("پوشاک بچگانه کانیابانه", "بانه"),
    "maloosak96":         ("پوشاک زنانه ملوسک (درگهان)", "قشم"),
    "lapland2":           ("لپ‌تاپ استوک لپ‌لند", "بانه"),
}
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36"

def fetch(ch):
    req = urllib.request.Request(f"https://t.me/s/{ch}", headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "ignore")

def clean(t):
    t = re.sub(r"<br\s*/?>", "\n", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"[ \t]+", " ", t).replace("&nbsp;", " ").replace("&amp;", "&").strip()

def parse(h, hours):
    # هر پست: زمان + متن + شماره‌ها
    chunks = re.split(r'class="tgme_widget_message ', h)[1:]
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    rows = []
    for c in chunks:
        tm = re.search(r'<time datetime="([^"]+)"', c)
        tx = re.search(r'tgme_widget_message_text[^>]*>(.*?)</div>', c, re.S)
        if not (tm and tx): continue
        try:
            dt = datetime.fromisoformat(tm.group(1))
        except Exception:
            continue
        if dt < cutoff: continue
        text = clean(tx.group(1))
        ph = re.findall(r"09\d{9}|021\d{7,8}", re.sub(r"\D", "", text + " " + c))
        prices = re.findall(r"\d[\d,٫٬.]*\s*(?:هزار|تومان|میلیون)", text)
        rows.append({"dt": dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M"), "text": text,
                     "phones": list(dict.fromkeys(ph))[:3], "prices": prices[:6]})
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=24)
    ap.add_argument("--channels", nargs="*", default=None)
    ap.add_argument("--csv", default=os.path.join(OUT, "omde_live.csv"))
    a = ap.parse_args()
    chans = a.channels or list(CHANNELS.keys())
    all_rows = []
    for ch in chans:
        fa, city = CHANNELS.get(ch, (ch, "?"))
        try:
            rows = parse(fetch(ch), a.hours)
        except Exception as e:
            print(f"… @{ch}: خطا ({type(e).__name__})"); continue
        print(f"• @{ch} | {fa} | {city} | {len(rows)} پست در {a.hours:g} ساعت اخیر")
        for r in rows[:3]:
            print(f"    [{r['dt']}] {r['text'][:95]}")
        all_rows += [dict(channel=f"@{ch}", region=city, **r) for r in rows]
        time.sleep(1.0)
    with open(a.csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["channel", "region", "dt", "text", "phones", "prices"])
        w.writeheader()
        for r in all_rows:
            r = dict(r); r["phones"] = " | ".join(r["phones"]); r["prices"] = " | ".join(r["prices"])
            w.writerow(r)
    print(f"\n✅ {len(all_rows)} پست زنده → {a.csv}")

if __name__ == "__main__":
    main()
