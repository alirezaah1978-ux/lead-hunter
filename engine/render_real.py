# -*- coding: utf-8 -*-
"""داشبورد داده‌ی واقعی دیوار — از خروجی real_pipeline.py"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(f"{HERE}/output/real_report.json", encoding="utf-8"))
S, I, P = D["stats"], D["intel"], D["pairs"]

FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
def n(x):
    if x is None: return "—"
    if isinstance(x, float) and x != int(x): return f"{x:,.1f}".replace(",", "٬").translate(FA)
    return f"{int(x):,}".replace(",", "٬").translate(FA)
def money(x):
    x = float(x or 0)
    if x >= 1e9: return f"{n(round(x/1e9,1))} میلیارد"
    if x >= 1e6: return f"{n(round(x/1e6))} میلیون"
    if x >= 1e3: return f"{n(round(x/1e3))} هزار"
    return n(x)

intel_rows = "".join(f"""
 <tr><td><b>{v['fa']}</b></td><td class="num">{n(v['count'])}</td><td class="num s">{n(v['sellers'])}</td>
 <td class="num b">{n(v['buyers'])}</td><td class="num">{n(v['median'])}</td>
 <td class="num sub2">{n(v['p10'])} – {n(v['p90'])}</td>
 <td class="sub2">{' • '.join(f'{c} ({k})' for c,k in v['cities'])}</td></tr>""" for v in I.values())

pair_rows = "".join(f"""
 <tr class="{'hot' if p['score']>=0.9 else ''}">
  <td class="num">{n(i)}</td>
  <td class="num"><b>{n(round(p['score']*100))}</b></td>
  <td><span class="vtag">{p['vertical_fa']}</span></td>
  <td><a href="{p['buyer_url']}" target="_blank" class="lnk">{p['need'][:80]}</a>
      <div class="sub2">{p['buyer_note']}</div></td>
  <td><a href="{p['seller_url']}" target="_blank" class="lnk">{p['seller_listing'][:60]}</a>
      <div class="sub2">{p['seller_city']} • {n(p['age_h'])} ساعت پیش • {p['source']}</div></td>
  <td class="num b">{n(p['buyer_price'])}</td>
  <td class="num s">{n(p['seller_price'])}</td>
  <td class="num spread">{n(p['spread_per_kg'])}</td>
  <td class="num">{money(p['deal_value'])}</td>
  <td class="num fee">{money(p['commission'])}</td>
 </tr>""" for i, p in enumerate(P[:25], 1))

review_rows = "".join(f"""<tr><td class="sub2">{r['why']}</td>
 <td><a href="{r['url']}" target="_blank" class="lnk">{r['listing'][:70]}</a></td>
 <td class="num sub2">{r['city']}</td><td class="num sub2">{n(r['price_raw'])}</td></tr>"""
 for r in D["review"][:12])

HTML = f"""<!DOCTYPE html><html lang="fa" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>داشبورد دیوار — داده‌ی واقعی</title>
<style>
 *{{box-sizing:border-box}} body{{margin:0;background:#0e1116;color:#e9eef6;font-family:Tahoma,"Segoe UI",sans-serif;line-height:1.75}}
 .wrap{{max-width:1420px;margin:0 auto;padding:22px 16px 60px}}
 header{{background:linear-gradient(140deg,#10233a,#0e1116 65%);border:1px solid #1f3550;border-radius:16px;padding:22px 24px}}
 h1{{margin:0 0 8px;font-size:23px}} .lead{{color:#95a8c2;font-size:13.5px}}
 h2{{font-size:18px;margin:28px 0 10px;padding-right:10px;border-right:4px solid #35d07f}}
 .kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin:16px 0}}
 .kpi{{background:#141922;border:1px solid #1f2c40;border-radius:13px;padding:13px 15px}}
 .kpi .v{{font-size:21px;font-weight:700;color:#7ee2a8}} .kpi .l{{font-size:11.5px;color:#8b9cb5}}
 .kpi.b .v{{color:#7cb0ff}} .kpi.g .v{{color:#ffd479}} .kpi.r .v{{color:#ff9d9d}}
 table{{width:100%;border-collapse:collapse;font-size:12.5px;background:#131820;border-radius:12px;overflow:hidden}}
 th,td{{padding:9px 11px;border-bottom:1px solid #1c2532;vertical-align:top}} th{{background:#182130;color:#a3b5cf;font-size:11.5px;text-align:right}}
 tr.hot{{background:rgba(126,226,168,.055)}} tr:hover{{background:#161d28}}
 .num{{text-align:left;white-space:nowrap;font-variant-numeric:tabular-nums}}
 .b{{color:#7cb0ff;font-weight:700}} .s{{color:#ffd479;font-weight:700}} .spread{{color:#7ee2a8;font-weight:700}} .fee{{color:#7ee2a8;font-weight:700}}
 .sub2{{font-size:11px;color:#8496b0}} .lnk{{color:#a8c9ff;text-decoration:none}} .lnk:hover{{text-decoration:underline}}
 .vtag{{background:#1b2536;border:1px solid #2b3c56;border-radius:20px;padding:1px 8px;font-size:11px;color:#9fb3d0;white-space:nowrap}}
 .note{{background:#151c28;border-right:3px solid #35d07f;padding:11px 14px;border-radius:9px;font-size:13px;color:#c3d1e4;margin:12px 0}}
 .warnbox{{border-right-color:#ffb86b}}
 .steps{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;margin-top:8px}}
 .step{{background:#141922;border:1px solid #1f2c40;border-radius:13px;padding:14px 16px}}
 .step h4{{margin:0 0 6px;font-size:14px;color:#7ee2a8}} .step p{{margin:0;font-size:12.5px;color:#b7c6dc}}
 code{{background:#0b1017;border:1px solid #223047;border-radius:6px;padding:1px 6px;font-size:12px;color:#8fd0ff;direction:ltr;display:inline-block}}
 footer{{margin-top:30px;color:#6d7d95;font-size:11.5px;border-top:1px solid #1c2532;padding-top:12px}}
</style></head><body><div class="wrap">
<header>
  <h1>🏠 دیوار، حل شد — داشبورد روی داده‌ی واقعی</h1>
  <div class="lead">این اعداد از <b>آگهی‌های واقعی و زنده‌ی دیوار</b> آمده‌اند که از بیرون ایران و بدون IP ایرانی،
  از طریق رله‌ی عمومی استخراج شده‌اند. نه API غیررسمی، نه لاگین، نه سرور ایران.</div>
</header>

<div class="kpis">
  <div class="kpi"><div class="v">{n(S['raw'])}</div><div class="l">آگهی خام دریافتی</div></div>
  <div class="kpi"><div class="v">{n(S['unique'])}</div><div class="l">یکتا (حذف {n(S['dupes'])} تکراری)</div></div>
  <div class="kpi b"><div class="v">{n(S['demands'])}</div><div class="l">آگهی «خریدار» پیدا شد</div></div>
  <div class="kpi g"><div class="v">{n(S['pairs'])}</div><div class="l">جفت عرضه×تقاضای معتبر</div></div>
  <div class="kpi r"><div class="v">{n(S['review'])}</div><div class="l">صف بررسی انسانی (قیمت مشکوک)</div></div>
  <div class="kpi g"><div class="v">{money(sum(p['commission'] for p in P[:25]))}</div><div class="l">پورسانت در ۲۵ فرصت اول</div></div>
</div>

<div class="note"><b>مهم‌ترین کشف این اجرا:</b> دیوار فقط مخزن «فروشنده» نیست؛ <b>{n(S['demands'])} آگهی خریدار</b> هم در همان ۴۳۰ آگهی پیدا شد
(مثل «خریدار ضایعات آهن و میلگرد با هر تناژی»). یعنی می‌توان <b>هر دو سمت معامله</b> را از همین یک منبع بیرون کشید
و فاصله‌ی قیمت پیشنهادی خریدار و فروشنده را اندازه گرفت — همان چیزی که پایه‌ی پورسانت است.</div>

<h2>۱) اطلاع از بازار واقعی (قیمت‌های نرمال‌شده به تومان/کیلو)</h2>
<table><thead><tr><th>حوزه</th><th>آگهی</th><th>فروشنده</th><th>خریدار</th><th>میانه قیمت</th><th>بازه (P10–P90)</th><th>شهرها</th></tr></thead>
<tbody>{intel_rows}</tbody></table>
<div class="note">📊 این جدول، به‌تنهایی ارزش دارد: هر کس این را داشته باشد، «مرجع قیمت» می‌شود.
همین را هفتگی در کانال تلگرام منتشر کن → لید ورودی و اعتبار، بدون تماس سرد.</div>

<h2>۲) فرصت‌های واقعی: خریدار ← فروشنده (با فاصله‌ی قیمتی)</h2>
<table><thead><tr><th>#</th><th>امتیاز</th><th>حوزه</th><th>خریدار (آگهی واقعی)</th><th>تأمین‌کننده (آگهی واقعی)</th>
<th>قیمت خریدار</th><th>قیمت فروشنده</th><th>فاصله هر کیلو</th><th>ارزش معامله*</th><th>پورسانت</th></tr></thead>
<tbody>{pair_rows}</tbody></table>
<div class="note warnbox">⚠️ <b>خط ستاره‌دار:</b> «ارزش معامله» بر مبنای <b>فرض محافظه‌کارانه‌ی ۲ تن</b> محاسبه شده چون دیوار در آگهی‌ها حجم را کم می‌نویسد.
پیش از هر پیشنهاد به دو طرف، باید حجم واقعی و اعتبار خریدار <b>تلفنی</b> تأیید شود. این اعداد «فرصت» هستند نه «تضمین».</div>

<h2>۳) صف بررسی انسانی — همان چیزی که هیچ رباتی نمی‌تواند تصمیم بگیرد</h2>
<table><thead><tr><th>دلیل توقف</th><th>آگهی/طرف</th><th>شهر</th><th>قیمت خام (تومان)</th></tr></thead>
<tbody>{review_rows or '<tr><td colspan="4" class="sub2">خالی</td></tr>'}</tbody></table>
<div class="note">این‌ها آگهی‌هایی هستند که ماشین نمی‌تواند درباره‌شان مطمئن باشد (کالای نامشخص، مقدار نامعلوم، قیمت مشکوک به اشتباه واحد).
<b>این ضعف نیست، طراحی است:</b> یک ربات بد، این‌ها را هم به عنوان «فرصت» به تو می‌فروشد و اعتبارت را نابود می‌کند.
ربات خوب، آن‌ها را در صف انسانی می‌گذارد.</div>

<h2>۴) چطور خودت همین را اجرا کنی (سه مسیر)</h2>
<div class="steps">
 <div class="step"><h4>۱. از همین‌جا، رایگان (بدون سرور)</h4>
   <p>رله‌ی عمومی: <code>python3 run.py --relay</code><br>سقف رایگان حدود ۲۰ درخواست در دقیقه است. برای پایلوت کافی است.</p></div>
 <div class="step"><h4>۲. رله‌ی شخصی روی Cloudflare (رایگان)</h4>
   <p>فایل <code>templates/relay-worker.js</code> را Deploy کن → سقف ۱۰۰٬۰۰۰ درخواست در روز، کش ۶ ساعته، بدون وابستگی به رله‌ی دیگران.</p></div>
 <div class="step"><h4>۳. سرور خودت (پایدارترین)</h4>
   <p>یک VPS ساده و کالکتور مستقیم. اول <code>python3 access_test.py</code> را اجرا کن تا بفهمی مسیر مستقیم برای IP تو باز است یا نه.</p></div>
</div>

<h2>۵) نکته‌ی حقوقی و اخلاقی (خیلی جدی بگیر)</h2>
<div class="note warnbox">
 • همه‌ی داده‌های این داشبورد <b>عمومی</b> هستند: همان چیزی که هر کاربر عادی در مرورگر می‌بیند. هیچ لاگینی، هیچ داده‌ی خصوصی، هیچ دور زدن سدی انجام نشده.<br>
 • کالکتور <b>کش ۶ ساعته</b> و <b>فاصله‌ی ۴ ثانیه</b> بین درخواست‌ها دارد؛ یعنی بار اضافه به دیوار تحمیل نمی‌کند.<br>
 • برای کار جدی و پرحجم، مسیر درست «<b>کنار دیوار</b>» است (API رسمی با تأیید اپ). ولی توجه: دیوار کسب‌وکارهای رقیب را نمی‌پذیرد؛ پس اگر نقشه‌ات پلتفرم‌شدن است، تأیید نمی‌گیری. در آن حالت «خواننده‌ی سبک» بمان و ارزش را در مهارت بستن معامله بساز.<br>
 • هرگز از این داده برای <b>ارسال انبوه پیام تبلیغاتی</b> استفاده نکن. پیام اول باید انسانی، مرتبط و کم‌حجم باشد. اسپم = بن + نابودی اعتبار در صنف.
</div>

<footer>مسیر داده: دیوار (SSR) ← رله ← استخراج <code>window.__PRELOADED_STATE__</code> ← نرمال‌سازی فارسی و قیمت ←
کنترل کیفیت (بازه‌ی قیمت هر کالا) ← تطبیق خریدار×فروشنده. موتور: <code>engine/real_pipeline.py</code> • کالکتور: <code>engine/sources/divar_relay.py</code></footer>
</div></body></html>"""

open(f"{HERE}/output/dashboard_real.html", "w", encoding="utf-8").write(HTML)
print("✔ داشبورد واقعی:", f"{HERE}/output/dashboard_real.html", f"({len(HTML)//1024} KB)")
