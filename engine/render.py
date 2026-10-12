# -*- coding: utf-8 -*-
"""تبدیل خروجی موتور به داشبورد HTML تک‌فایلی (RTL، بدون منبع خارجی)."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(f"{HERE}/output/matches.json", encoding="utf-8"))
K = D["kpi"]

def n(x):
    if isinstance(x, float) and x != int(x):
        return f"{x:,.1f}".replace(",", "٬").replace(".", "٫").translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))
    return f"{int(x):,}".replace(",", "٬").translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))

def money(x):
    x = float(x)
    if x >= 1e9: return f"{n(round(x/1e9, 1) if x/1e9 < 100 else round(x/1e9))} میلیارد"
    if x >= 1e6: return f"{n(round(x/1e6, 1))} میلیون"
    if x >= 1e3: return f"{n(round(x/1e3))} هزار"
    return n(x)

rows_html = []
for i, m in enumerate(D["matches"], 1):
    p = m["parts"]
    bar = lambda v: f'<span class="bar"><i style="width:{int(v*100)}%"></i></span>'
    notes = "".join(f'<span class="tag {"bad" if "⛔" in x or "واسطه" in x else ""}">{x}</span>' for x in m["notes"]) or '<span class="tag ok">بدون هشدار</span>'
    green = m["score"] >= 0.72
    script = (f"سلام، وقتتون بخیر. دربارهی آگهی «{m['listing']}» تماس گرفتم. "
              f"من سمت خریدار کار میکنم و دنبال {m['need']} هستم. "
              f"دو سؤال کوتاه: ۱) موجودی واقعی الان چقدره؟ ۲) کمترین قیمت برای این حجم و شرایط تسویهتون چیه؟ "
              f"اگر رقمها بخوره، هماهنگی با خریدار با من.")
    rows_html.append(f"""
    <tr class="{'hot' if green else ''}">
      <td class="num">{n(i)}</td>
      <td class="score"><b>{n(round(m['score']*100))}</b>{bar(m['score'])}</td>
      <td><div class="buyer">{m['buyer']}</div><div class="sub">{m['need']}</div>
          <div class="sub {'warn' if not m['verified'] else ''}">{'✔ خریدار اعتبارسنجیشده' if m['verified'] else '⚠ خریدار اعتبارسنجینشده'}</div></td>
      <td><div class="lst">{m['listing']}</div><div class="sub">{m['vertical_fa']} • {m['source']} • {m['city']}</div>
          <div class="sub">{'قیمت: ' + n(m['price']) + ' تومان' if m['price'] else 'قیمت: نامشخص'} {' • مقدار: ' + n(m['qty']) + ' ' + m['unit'] if m['qty'] else ''}</div></td>
      <td class="num"><div>{money(m['deal_value'])}</div><div class="sub">تومان ارزش معامله</div></td>
      <td class="num fee"><div>{money(m['fee'])}</div><div class="sub">٪{n(round(m['fee_rate']*100,1))} • برد {n(round(m['close_prob']*100))}٪</div></td>
      <td class="num"><div>{money(m['ev'])}</div><div class="sub">EV خالص</div></td>
      <td><div class="action">{m['action']}</div><div class="tags">{notes}</div>
          <details><summary>متن اولین تماس</summary><textarea readonly rows="4">{script}</textarea></details></td>
    </tr>""")

model_rows = "".join(f"""
  <tr><td><b>{s['name']}</b></td><td class="num">{n(s['opp_per_month'])}</td>
      <td class="num">{n(round(s['quote']*100))}٪</td><td class="num">{n(round(s['win']*100))}٪</td>
      <td class="num">{n(s['avg_fee']/1e6)} م</td>
      <td class="num p10">{money(s['p10'])}</td><td class="num p50">{money(s['p50'])}</td><td class="num p90">{money(s['p90'])}</td>
      <td class="num">{n(s['team'])} نفر</td></tr>""" for s in D["model"])

best_rows = "".join(f"""<li><b>{b['buyer']}</b> ¬ {b['listing']} <span class="sub">— پورسانت {money(b['fee'])} تومان • امتیاز {n(round(b['score']*100))}</span></li>"""
                    for b in D["best"])

HTML = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>داشبورد کارگزاری B2B — پایلوت</title>
<style>
 * {{ box-sizing:border-box }}
 body {{ margin:0; background:#0f1218; color:#e8ecf3; font-family:Tahoma,"Segoe UI",sans-serif; line-height:1.7 }}
 .wrap {{ max-width:1400px; margin:0 auto; padding:24px 18px 60px }}
 header {{ background:linear-gradient(135deg,#152036,#0f1218 60%); border:1px solid #24304a; border-radius:16px; padding:22px 24px; margin-bottom:18px }}
 h1 {{ margin:0 0 6px; font-size:24px }}
 h2 {{ font-size:19px; margin:30px 0 12px; padding-right:10px; border-right:4px solid #4d7cfe }}
 h3 {{ font-size:16px; margin:18px 0 8px; color:#b9c6dd }}
 .lead {{ color:#9fb0c9; font-size:14px }}
 .kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:12px; margin:18px 0 }}
 .kpi {{ background:#151a24; border:1px solid #23304a; border-radius:14px; padding:14px 16px }}
 .kpi .v {{ font-size:22px; font-weight:700; color:#7ee2a8 }}
 .kpi .l {{ font-size:12px; color:#93a3bd }}
 .kpi.blue .v {{ color:#7cb0ff }} .kpi.gold .v {{ color:#ffd479 }}
 table {{ width:100%; border-collapse:collapse; font-size:13px; background:#131822; border-radius:12px; overflow:hidden }}
 th,td {{ padding:10px 12px; border-bottom:1px solid #1e2735; vertical-align:top }}
 th {{ background:#182031; color:#a9bad4; font-size:12px; text-align:right; position:sticky; top:0 }}
 tr.hot {{ background:rgba(126,226,168,.05) }}
 tr:hover {{ background:#161d2a }}
 .num {{ white-space:nowrap; text-align:left; font-variant-numeric:tabular-nums }}
 .sub {{ font-size:11.5px; color:#8b9bb4 }}
 .sub.warn {{ color:#ffb86b }}
 .buyer {{ font-weight:700; color:#cfe0ff }}
 .lst {{ color:#e6ecf7 }}
 .fee {{ color:#7ee2a8; font-weight:700 }}
 .score b {{ font-size:15px }}
 .bar {{ display:block; width:70px; height:5px; background:#20293a; border-radius:3px; margin-top:5px }}
 .bar i {{ display:block; height:5px; background:linear-gradient(90deg,#4d7cfe,#7ee2a8); border-radius:3px }}
 .tags {{ margin-top:5px; display:flex; flex-wrap:wrap; gap:4px }}
 .tag {{ font-size:11px; background:#1c2636; border:1px solid #2c3a52; border-radius:20px; padding:1px 8px; color:#9fb0c9 }}
 .tag.bad {{ background:#2c1b1b; border-color:#5c2b2b; color:#ff9d9d }}
 .tag.ok {{ background:#16281f; border-color:#245c3c; color:#89e0b0 }}
 .action {{ font-size:12px; color:#ffd479 }}
 textarea {{ width:100%; margin-top:6px; background:#0e131c; color:#cfe0ff; border:1px solid #2a3750; border-radius:8px; padding:8px; font-family:Tahoma; font-size:12px; direction:rtl }}
 details summary {{ cursor:pointer; font-size:11.5px; color:#7cb0ff; margin-top:6px }}
 .grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:16px }}
 @media (max-width:900px) {{ .grid2 {{ grid-template-columns:1fr }} }}
 .card {{ background:#131822; border:1px solid #23304a; border-radius:14px; padding:16px 18px }}
 .card ul {{ margin:8px 0 0; padding-right:18px }}
 .card li {{ margin-bottom:6px; font-size:13.5px }}
 .p10 {{ color:#ff9d9d }} .p50 {{ color:#ffd479 }} .p90 {{ color:#7ee2a8 }}
 .note {{ background:#171d2a; border-right:3px solid #4d7cfe; padding:10px 14px; border-radius:8px; font-size:13.5px; color:#c3d0e4; margin:12px 0 }}
 .ok {{ color:#7ee2a8 }} .warn2 {{ color:#ffb86b }} .bad2 {{ color:#ff9d9d }}
 footer {{ margin-top:34px; color:#6f7f97; font-size:12px; border-top:1px solid #1e2735; padding-top:14px }}
</style></head><body><div class="wrap">

<header>
  <h1>🏗️ داشبورد کارگزاری B2B — نسخه‌ی پایلوت</h1>
  <div class="lead">موتور جست‌وجو → تطبیق → امتیازدهی → محاسبه‌ی پورسانت. داده: نمونه‌ی شبیه‌سازی‌شده با نویز واقعی
  (آگهی تکراری، آگهی «خریدار» به‌جای فروشنده، قیمت نامشخص، فروشنده‌ی بدقلق).</div>
</header>

<div class="kpis">
  <div class="kpi"><div class="v">{n(K['unique_supply'])}</div><div class="l">عرضه‌ی یکتا (از {n(K['raw_listings'])} آگهی خام)</div></div>
  <div class="kpi"><div class="v">{n(K['demands'])}</div><div class="l">تقاضای اعتبارسنجی‌شده</div></div>
  <div class="kpi blue"><div class="v">{n(K['qualified_matches'])}</div><div class="l">فرصت واجد شرایط (امتیاز ≥ ۰.۶۲)</div></div>
  <div class="kpi blue"><div class="v">{n(K['green'])}</div><div class="l">آماده‌ی مذاکره (≥ ۰.۷۲)</div></div>
  <div class="kpi gold"><div class="v">{money(K['pipeline_value'])}</div><div class="l">ارزش خط لوله (تومان)</div></div>
  <div class="kpi gold"><div class="v">{money(K['pipeline_fee'])}</div><div class="l">پورسانت در خط لوله</div></div>
  <div class="kpi"><div class="v">{money(K['expected_net'])}</div><div class="l">سود انتظاری خالص (EV)</div></div>
</div>

<div class="note">📌 <b>خواندن این اعداد:</b> این ۷ فرصت از فقط <b>۲۴ آگهی</b> و <b>۶ خریدار</b> در <b>۳ حوزه</b> بیرون آمد.
یعنی موتور «کار می‌کند» — ولی ارزش واقعی موتور در <b>مقیاس</b> است: ۱۰ حوزه × ۵ شهر × ۵۰۰ آگهی/روز = هزاران فرصت پویا.
هزینه‌ی واقعی این مدل، جمع‌آوری نیست؛ <b>پیگیری انسانی و بستن معامله</b> است.</div>

<h2>۱) خط لوله‌ی فرصت‌ها — امروز چه کسی را باید زنگ بزنم؟</h2>
<table>
<thead><tr><th>#</th><th>امتیاز</th><th>خریدار</th><th>تأمین‌کننده / آگهی</th><th>ارزش معامله</th><th>پورسانت</th><th>EV خالص</th><th>اقدام و هشدارها</th></tr></thead>
<tbody>{''.join(rows_html)}</tbody></table>

<h2>۲) باارزش‌ترین معامله‌ها در یک نگاه</h2>
<div class="card"><ul>{best_rows}</ul></div>

<h2>۳) مدل درآمد ۹۰ روزه (شبیه‌سازی مونت‌کارلو، ۳۰۰۰ اجرا)</h2>
<table>
<thead><tr><th>سناریو</th><th>فرصت/ماه</th><th>نرخ مذاکره</th><th>نرخ برد</th><th>میانگین پورسانت</th>
<th>بدبینانه (P10)</th><th>میانه (P50)</th><th>خوش‌بینانه (P90)</th><th>تیم لازم</th></tr></thead>
<tbody>{model_rows}</tbody></table>
<div class="note">⚠️ <b>هشدار صادقانه:</b> سناریوی «محافظه‌کارانه» با اختلاف فاحش زیر هزینه‌ی یک تیم ۳ نفره در ۹۰ روز است
(حقوق + ابزار ≈ ۱۵۰ تا ۳۰۰ میلیون تومان). یعنی این کار <b>فقط در مقیاس و با تیم لاغر</b> معنا دارد،
و راه سریع‌تر رسیدن به سود: <b>معامله‌های درشت با حاشیه‌ی بالا</b> (خشکبار صادراتی، فولاد) نه تعداد زیاد معامله‌ی کوچک.</div>

<h2>۴) پنج مدل پورسانت — چه بگیری، چه‌وقت بگیری</h2>
<table>
<thead><tr><th>مدل</th><th>مبنا</th><th>عدد پیشنهادی</th><th>مناسب برای</th><th>ریسک تو</th></tr></thead>
<tbody>
<tr><td><b>فقط موفق</b></td><td>٪ از ارزش معامله</td><td>خشکبار ۱–۲٪ • فولاد ۰.۵–۱٪ • ضایعات ۲–۴٪</td><td>هفته‌های ۱ تا ۸ — بهترین شروع</td><td>صفر درآمد تا معامله‌ی اول</td></tr>
<tr><td><b>کمیسیون لید (CPL)</b></td><td>مبلغ ثابت / لید تأییدشده</td><td>۲–۵ میلیون تومان به‌ازای هر خریدار واجد شرایط</td><td>وقتی اسکریپت و مهارت جا افتاد</td><td>بحث «لیدت بی‌کیفیت بود»</td></tr>
<tr><td><b>ریتینر + پاداش</b></td><td>ماهانه + ٪ کمتر</td><td>۲۵–۶۰ میلیون ماهانه + ۰.۵٪</td><td>ماه ۶ به بعد، تأمین‌کننده‌ی اصلی</td><td>باید جریان پیوسته بسازی</td></tr>
<tr><td><b>حاشیه‌ی حجمی</b></td><td>به‌ازای هر تن/کامیون</td><td>۲۰۰–۶۰۰ هزار تومان به‌ازای هر تن</td><td>فولاد، ضایعات، سیمان</td><td>مدیریت هم‌زمان دو طرف</td></tr>
<tr><td><b>معامله‌گری (Trading)</b></td><td>خرید با سرمایه‌ی خودت</td><td>حاشیه‌ی ۵–۱۵٪</td><td>فاز ۳ — اگر سرمایه داری</td><td>سرمایه، اعتبار، مالیات، انبار</td></tr>
</tbody></table>

<h2>۵) واقعه‌نگاری پلتفرم‌ها: در دنیای واقعی کدام‌شان جواب می‌دهد؟</h2>
<table>
<thead><tr><th>منبع</th><th>رصد خودکار (اسکرپ/API)</th><th>ارسال پیام خودکار</th><th>واقعیت اجرایی</th></tr></thead>
<tbody>
<tr><td><b>دیوار</b></td><td class="warn2">ممکن، از IP ایران (API غیررسمی)</td><td class="bad2">ممنوع/پرریسک — گزارش‌دهی کاربران</td><td>بزرگ‌ترین مخزن عرضه در ایران. سرور ما (خارج ایران) به آن دسترسی نداشت؛ باید روی VPS ایران اجرا شود. مسیر رسمی: «کنار دیوار» (نیاز به تأیید اپ + OAuth) که کسب‌وکار رقیب را نمی‌پذیرد → پس ما فقط «خواننده» می‌مانیم.</td></tr>
<tr><td><b>تلگرام</b></td><td class="ok">ممکن و کم‌ریسک (گروه‌هایی که عضوی)</td><td class="warn2">پیام مستقیم انبوه = ریسک بن؛ پیام هدفمند = اکی</td><td>پرارزش‌ترین منبع برای معامله‌های عمده و ضایعات. خواندن تاریخچه در ۱–۲ ثانیه فاصله، پایدار است. ولی <b>عضویت انبوه در گروها</b> محدودیت می‌آورد (FloodWait) و <b>ارسال سرد انبوه</b> به بن می‌رسد.</td></tr>
<tr><td><b>اینستاگرام</b></td><td class="warn2">هشتگ/پیج عمومی — سخت و پرریسک؛ بدون لاگین محدود</td><td class="bad2">DM سرد از بات = محدودیت قطعی</td><td>برای <b>کشف</b> تأمین‌کننده‌های صنفی خوب است (پیج‌های عمده‌فروشی)، ولی مسیر ارسال باید انسانی باشد. API رسمی فقط برای اکانت‌های تجاری خودت.</td></tr>
<tr><td><b>باسکول / ایستابای / دیجی‌عمده</b></td><td class="ok">ساختار تمیز، قابل رصد سبک</td><td class="bad2">شماره‌ها پشت لاگین — نیاز به اکانت و تماس انسانی</td><td>دقیقاً همان بازار هدف B2B. اینجا کیفیت لید از دیوار بالاتر است، ولی حجم کمتر.</td></tr>
<tr><td><b>خارج از نت</b></td><td>—</td><td>—</td><td class="ok">شبکه‌ی شخصی، اتحادیه‌ها/انجمن‌های صنفی، نمایشگاه‌ها، دفاتر حمل‌ونقل. در ایران هنوز <b>بیشترین معامله از همین‌جا</b> می‌آید — ابزار، تسریع‌کننده است، نه جانشین.</td></tr>
</tbody></table>

<h2>۶) پلن ۷ روز اول (حداقل کار مؤثر)</h2>
<div class="card"><ul>
<li><b>روز ۱:</b> یک حوزه انتخاب کن — ترجیحاً چیزی که خودت یا خانواده/دوستت در آن فعال است (شبکه‌ی گرم = مزیت غیرقابل کپی). خشکبار یا ضایعات = بهترین نقطه‌ی شروع.</li>
<li><b>روز ۱:</b> ۳۰ خریدار بالقوه را از مخاطبان گوشی‌ات دربیاور (همیشه بیشترین خریدار در دفترچه‌تلفن توست، نه در نت).</li>
<li><b>روز ۲:</b> ۱۰ تماس اعتبارسنجی خریدار با قالب ۰۱ → هدف: ۳ خریدار تأییدشده با سقف قیمت مکتوب.</li>
<li><b>روز ۳:</b> ۱۵ تماس با فروشنده با قالب ۰۲ → هدف: ۵ تأمین‌کننده‌ی همکار با موجودی واقعی.</li>
<li><b>روز ۴:</b> کالکتور را روی VPS ایران بالا بیاور (یا دستی ۱۰۰ آگهی را جمع کن) و به موتور بده.</li>
<li><b>روز ۵:</b> اولین وصل‌کردن دو طرف — با <b>تماس سه‌طرفه</b> و توافق‌نامه‌ی سه‌خطی از قبل گرفته‌شده.</li>
<li><b>روز ۶ و ۷:</b> پیگیری + راه‌اندازی کانال «قیمت روز بازار [حوزه]» برای ساخت مرجعیت و لید ارگانیک.</li>
</ul></div>

<footer>داده‌ی این داشبورد «نمونه‌ی شبیه‌سازی‌شده» است تا موتور و منطق تصمیم را نشان دهد؛
اعداد واقعی وقتی معنا پیدا می‌کنند که کالکتور روی IP ایران به دیوار و منابع واقعی وصل شود.
ساخته‌شده در Arena — فایل‌های موتور: <code>engine/run.py</code> • خروجی: <code>engine/output/matches.csv</code></footer>
</div></body></html>"""

open(f"{HERE}/output/dashboard.html", "w", encoding="utf-8").write(HTML)
print("✔ داشبورد ساخته شد:", f"{HERE}/output/dashboard.html", f"({len(HTML)//1024} KB)")
