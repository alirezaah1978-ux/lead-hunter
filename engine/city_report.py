# -*- coding: utf-8 -*-
"""گزارش شهر به شهر — یک دستور، همه‌چیز.
  python3 city_report.py          → تحلیل + ارسال خلاصه به تلگرام
  python3 city_report.py --quiet  → فقط تحلیل، بدون ارسال
"""
import sys, os, json, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
sys.path.insert(0, HERE)

subprocess.run([sys.executable, "city_balance.py"], cwd=HERE, check=True)
subprocess.run([sys.executable, "city_insight.py"], cwd=HERE, check=True)

ins = json.load(open(f"{OUT}/city_insight.json", encoding="utf-8"))
FA = {"tehran":"تهران","karaj":"کرج","isfahan":"اصفهان","mashhad":"مشهد","tabriz":"تبریز",
      "shiraz":"شیراز","qom":"قم","kerman":"کرمان","rasht":"رشت","arak":"اراک","yazd":"یزد","ahvaz":"اهواز"}
NAME = {"pistachio":"پسته","steel":"فولاد","scrap":"ضایعات","autoparts":"لوازم یدکی"}

lines = ["🗺 <b>نقشه‌ی شهر به شهر بازار</b>", ""]
for v in ("scrap", "steel", "pistachio", "autoparts"):
    demand = [FA.get(c, c) for c, x in ins[v].items() if "بازار فروش" in x["نقش"] and x["تقاضا"] >= 10]
    supply = [FA.get(c, c) for c, x in ins[v].items() if "منبع تأمین" in x["نقش"] and x["عرضه"] >= 5]
    lines.append(f"<b>{NAME[v]}</b>")
    lines.append(f"  🔴 تقاضا (بفروش آنجا): {'، '.join(demand[:6]) or '—'}")
    lines.append(f"  🟢 عرضه (بخر از): {'، '.join(supply[:6]) or '—'}")
    lines.append("")

pairs = []
for v in ("scrap", "steel", "pistachio", "autoparts"):
    d = {}
    for c, x in ins[v].items():
        for p, price in x["قیمت هر قلم"].items():
            d.setdefault(p, {})[c] = price
    for p, cd in d.items():
        if len(cd) < 2: continue
        s = sorted(cd.items(), key=lambda x: x[1])
        lo, hi = s[0], s[-1]
        sp = (hi[1] - lo[1]) / lo[1] * 100
        if sp >= 25:
            pairs.append((sp, f"  {p}: {FA.get(lo[0],lo[0])} {lo[1]:,} → {FA.get(hi[0],hi[0])} {hi[1]:,} ({sp:.0f}%)"))
if pairs:
    lines.append("🚚 <b>اختلاف قیمت همان قلم بین شهرها</b>")
    lines += [p[1] for p in sorted(pairs, reverse=True)[:6]]

msg = "\n".join(lines)
print(msg.replace("<b>", "").replace("</b>", ""))
if "--quiet" not in sys.argv:
    from notify_multi import broadcast
    print(broadcast(msg))
