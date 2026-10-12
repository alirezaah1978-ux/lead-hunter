# -*- coding: utf-8 -*-
"""
اجرای کامل پایپ‌لاین:
  ۱) جمع‌آوری (seed یا دیوار واقعی)
  ۲) پاک‌سازی + حذف تکراری
  ۳) تطبیق عرضه×تقاضا و امتیازدهی
  ۴) اقتصاد فرصت (پورسانت، EV)
  ۵) تولید خروجی: matches.csv + matches.json + داشبورد عملیاتی + شبیه‌سازی درآمد
"""
import csv, json, random, sys, os
from core import clean_listing, dedupe, score_match, economics, human, fa_num
from seed_data import build_supply, DEMAND
from config import VERTICALS, THRESHOLD_QUALIFIED, THRESHOLD_ACTION

random.seed(7)
OUT = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUT, exist_ok=True)

# ---------- ۱) جمع‌آوری ----------
if "--relay" in sys.argv:
    # مسیر اثبات‌شده: دیوار از طریق رله (بدون نیاز به IP ایران)
    from sources.divar_relay import crawl as relay_crawl, details
    queries = [q for v in VERTICALS.values() for q in v.get("b2b_queries", [])]
    raw = relay_crawl(queries, cities=("tehran", "kerman", "isfahan"))
    print(f"🏠 کالکتور دیوار (رله): {len(raw)} آگهی واقعی")
    # غنی‌سازی توضیحات فقط برای آگهی‌های امیدبخش (صرفه‌جویی در درخواست)
    hot_markers = ["عمده", "تن", "صادرات", "بارگیری", "کیلو", "خرید", "قرارداد"]
    hot = [r for r in raw if any(m in r["title"] for m in hot_markers)][:12]
    for r in hot:
        d = details(r["token"])
        if d.get("desc"):
            r["desc"] = d["desc"]; r["raw"] = r["title"] + " " + d["desc"]
    print(f"   ↳ توضیحات کامل برای {sum(1 for r in hot if r['desc'])} آگهی غنی شد")
elif "--live" in sys.argv:
    from sources.divar_collector import crawl
    queries = [k for v in VERTICALS.values() for k in v["keywords"]][:9]
    raw = crawl(queries, city="تهران", pages=1)
    print(f"کالکتور زنده: {len(raw)} رکورد")
else:
    raw = build_supply()
    print(f"داده‌ی نمونه: {len(raw)} آگهی خام")

# ---------- ۲) پاک‌سازی و حذف تکراری ----------
listings = [clean_listing(l) for l in raw]
listings, n_dupes = dedupe(listings)
print(f"بعد از حذف {n_dupes} آگهی تکراری: {len(listings)} عرضه‌ی یکتا")

# ---------- ۳) تطبیق ----------
rows = []
for d in DEMAND:
    for l in listings:
        if l["vertical"] != d["vertical"]: continue
        m = score_match(d, l)
        if m["score"] < THRESHOLD_QUALIFIED: continue
        eco = economics(d, l, m)
        rows.append({"demand": d, "listing": l, "m": m, "eco": eco})
rows.sort(key=lambda r: r["m"]["score"] * r["eco"]["ev"], reverse=True)
print(f"تطبیق واجد شرایط: {len(rows)}")

# هر آگهی فقط به بهترین خریدارش پیشنهاد می‌شود (تا موازی‌کاری و بی‌اعتباری نشود)
best_per_listing = {}
for r in rows:
    key = r["listing"]["id"]
    if key not in best_per_listing or r["m"]["score"] > best_per_listing[key]["m"]["score"]:
        best_per_listing[key] = r

# ---------- ۴) خروجی CSV ----------
csv_path = f"{OUT}/matches.csv"
with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["رتبه","امتیاز","اقدام","خریدار","نیاز خریدار","فروشنده/آگهی","منبع","قیمت واحد (تومان)",
                "مقدار","ارزش معامله","پورسانت","احتمال بستن","EV خالص","شهر","یادداشت‌ها"])
    for i, r in enumerate(rows, 1):
        d, l, m, e = r["demand"], r["listing"], r["m"], r["eco"]
        act = "🟢 مذاکره" if m["score"] >= THRESHOLD_ACTION else "🟡 ارزیابی"
        w.writerow([i, m["score"], act, d["buyer"], d["need"], l["title"][:70], l["source"],
                    l["price"] or "-", l["qty"] or "-", round(e["deal_value"]), round(e["fee"]),
                    e["close_prob"], round(e["ev"]), l["city"], "؛ ".join(m["notes"]) or "-"])

# ---------- ۵) شبیه‌سازی درآمد ۹۰ روزه (مونت‌کارلو) ----------
CFG = {"reached": [], "quoted": [], "won": []}
for r in rows:
    e, m, l, d = r["eco"], r["m"], r["listing"], r["demand"]
    CFG["reached"].append(True)                                  # فرض: پیگیری موفق
    CFG["quoted"].append(random.random() < 0.55 + 0.3*m["score"])# فروشنده/خریدار وارد مذاکره می‌شود
    CFG["won"].append(random.random() < e["close_prob"])         # معامله بسته می‌شود

def simulate(runs=2000, p_quote=0.70, p_win=0.28, fee_avg=None):
    """مدل ساده: n فرصت/ماه × نرخ تبدیل → درآمد. برای تعیین تیم لازم."""
    out = []
    for _ in range(runs):
        rev = sum(1 for _ in range(60) if random.random() < p_quote and random.random() < p_win)
        out.append(rev * (fee_avg or 0))
    return out

matched_fees = [r["eco"]["fee"] for r in rows]
avg_fee = sum(matched_fees)/len(matched_fees) if matched_fees else 0

# ---------- ۶) JSON برای داشبورد و مستندات ----------
summary = {
    "kpi": {
        "raw_listings": len(raw), "unique_supply": len(listings), "dupes_removed": n_dupes,
        "demands": len(DEMAND), "qualified_matches": len(rows),
        "green": sum(1 for r in rows if r["m"]["score"] >= THRESHOLD_ACTION),
        "pipeline_value": round(sum(r["eco"]["deal_value"] for r in best_per_listing.values())),
        "pipeline_fee": round(sum(r["eco"]["fee"] for r in best_per_listing.values())),
        "expected_net": round(sum(r["eco"]["ev"] for r in best_per_listing.values())),
        "avg_matched_fee": round(avg_fee),
    },
    "matches": [{
        "score": r["m"]["score"], "parts": r["m"]["parts"], "notes": r["m"]["notes"],
        "buyer": r["demand"]["buyer"], "buyer_note": r["demand"]["note"],
        "need": r["demand"]["need"], "verified": r["demand"]["verified"],
        "listing": r["listing"]["title"], "source": r["listing"]["source"],
        "city": r["listing"]["city"], "url": r["listing"]["url"],
        "price": r["listing"]["price"], "qty": r["listing"]["qty"],
        "unit": {"kg": "کیلوگرم"}.get(VERTICALS[r["listing"]["vertical"]].get("unit"), "واحد"),
        "vertical_fa": VERTICALS[r["listing"]["vertical"]]["fa"],
        "deal_value": round(r["eco"]["deal_value"]), "fee": round(r["eco"]["fee"]),
        "fee_rate": r["eco"]["fee_rate"], "close_prob": r["eco"]["close_prob"],
        "ev": round(r["eco"]["ev"]),
        "action": "🟢 مذاکره کن" if r["m"]["score"] >= THRESHOLD_ACTION else "🟡 ارزیابی بیشتر",
    } for r in rows],
    "best": [{
        "listing": r["listing"]["title"], "buyer": r["demand"]["buyer"], "score": r["m"]["score"],
        "fee": round(r["eco"]["fee"]),
    } for r in sorted(best_per_listing.values(), key=lambda x: -x["eco"]["fee"])[:6]],
}
with open(f"{OUT}/matches.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

# ---------- ۷) چاپ خلاصه ----------
print("\n" + "="*74)
print(f"  خط لوله: {len(best_per_listing)} فرصت یکتا | ارزش معاملات: {human(summary['kpi']['pipeline_value'])} تومان")
print(f"  پورسانت در خط لوله: {human(summary['kpi']['pipeline_fee'])} تومان | سود انتظاری خالص: {human(summary['kpi']['expected_net'])}")
print("="*74)
print(f"{'#':<3}{'امتیاز':<7}{'خریدار':<22}{'آگهی':<34}{'پورسانت':>12}")
for i, r in enumerate(rows[:12], 1):
    print(f"{i:<3}{r['m']['score']:<7}{r['demand']['buyer'][:20]:<22}{r['listing']['title'][:32]:<34}{human(r['eco']['fee']):>12}")
print(f"\n✔ {csv_path}\n✔ {OUT}/matches.json")

# ---------- ۸) مدل درآمد و تیم (برای بخش «پول‌سازی») ----------
print("\n" + "="*74); print("  مدل درآمد (۹۰ روزه) — سه سناریو"); print("="*74)
scen = [("محافظه‌کارانه", 40, 0.50, 0.16, 3_500_000),
        ("واقع‌بینانه",    80, 0.60, 0.26, 4_800_000),
        ("تهاجمی",        150, 0.68, 0.34, 6_500_000)]
model = []
for name, opp, pq, pw, fee in scen:
    sims = []
    for _ in range(3000):
        wins = sum(1 for _ in range(opp) if random.random() < pq and random.random() < pw)
        sims.append(wins * fee)
    sims.sort()
    p10, p50, p90 = sims[300], sims[1500], sims[2700]
    team = max(1, round(opp/25))  # هر اپراتور ~۲۵ فرصت فعال در ماه
    model.append({"name": name, "opp_per_month": opp, "quote": pq, "win": pw, "avg_fee": fee,
                  "p10": round(p10), "p50": round(p50), "p90": round(p90),
                  "team": team, "per_head_p50": round(p50/team)})
    print(f"  {name:<12} {opp:>3} فرصت/ماه | نرخ مذاکره {pq:.0%} | نرخ برد {pw:.0%} | "
          f"درآمد ۹۰ روزه: {human(p10)} – {human(p50)} – {human(p90)} | تیم: {team} نفر")
summary["model"] = model
with open(f"{OUT}/matches.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print("\n✔ مدل درآمد در matches.json ذخیره شد.")
