import sys, os, re, json, csv
sys.path.insert(0,'.')
from sources.telegram_public import crawl
CAND = [("divar_com","نیازمندی‌های دیوار تهران (ملی)","ایران"),
 ("divarmarivanian","دیوار مریوان","ایران"),
 ("iranihaistanbul2","خانه ایرانیان استانبول","ترکیه"),
 ("IRNIST","ایرانیان استانبول","ترکیه"),
 ("divar_agahi","دیوار آگهی","ایران"),
 ("niazmandiha_divar","نیازمندی‌های دیوار","ایران"),
 ("divar_iran","دیوار ایران","ایران"),
 ("divar_sweden","دیوار سوئد","سوئد"),
 ("divar_toronto","دیوار تورنتو","کانادا"),
 ("divar_canada","دیوار کانادا","کانادا"),
 ("divar_dubai","دیوار دبی","امارات"),
 ("divar_london","دیوار لندن","انگلیس"),
 ("divar_paris","دیوار پاریس","فرانسه"),
 ("divar_australia","دیوار استرالیا","استرالیا"),
 ("amrica_divar","دیوار آمریکا","آمریکا"),
 ("berlin_divar","دیوار برلین","آلمان"),
 ("divar_hamburg","دیوار هامبورگ ۲","آلمان"),
 ("divar_munchen","دیوار مونیخ","آلمان"),
 ("divar_wien","دیوار وین","اتریش"),
 ("divar_norway","دیوار نروژ","نروژ"),
 ("divar_denmark","دیوار دانمارک","دانمارک"),
]
CATS={"خوراکی/صادرات ایرانی":["پسته","زعفران","نبات","خرما","تخمه","آجیل","ادویه","لواشک","ترشی","زرشک","حلوا"],
"خودرو":["خودرو","ماشین","پژو","پراید","بنز","بی ام و","تویوتا"],"املاک":["آپارتمان","خانه","اجاره","ملک","سوئیت","اتاق"],
"لوازم خانگی/مبلمان":["یخچال","لباسشویی","مبل","فرش","تلویزیون","کاناپه","تخت"],
"موبایل/لپ‌تاپ":["موبایل","آیفون","لپ تاپ","گوشی","کامپیوتر"],
"لوازم یدکی":["لوازم یدکی","قطعات","لنت","فیلتر","گیربکس"],
"کارگو/ارسال بار":["کارگو","ارسال بار","باربری","حمل بار","مرسوله","محموله","ارسال به ایران"],
"ارز/انتقال پول":["یورو","دلار","انتقال پول","صرافی","تتر","حواله"],
"کار/استخدام":["استخدام","کاریابی","جویای کار"],
"خدمات":["تعمیر","نظافت","راننده","ساختمان"]}
BUY=["خریدار","میخرم","می‌خرم","متقاضی","نیاز به خرید","نیاز دارم","دنبال"]
rows=[]
for h,label,reg in CAND:
    try: posts=crawl(channels=[(h,label)],pages=2)
    except Exception as e: print(f"  ⛔ {h}"); continue
    if not posts: print(f"  ⚪ {h:20s} بی‌پست/غیرعمومی"); continue
    text="\n".join((p.get("text") or "") for p in posts)
    cats={c:sum(1 for k in ks if k in text) for c,ks in CATS.items()}
    cats={c:n for c,n in cats.items() if n>=2}
    ph=set()
    for p in posts: ph|=set(p.get("phones") or [])
    buy=sum(1 for p in posts if any(b in (p.get("text") or "") for b in BUY))
    top=sorted(cats.items(),key=lambda x:-x[1])[:5]
    rows.append({"نام":label,"منطقه":reg,"handle":h,"پست":len(posts),"خریدار":buy,"شماره":len(ph),
      "حوزه‌ها":" · ".join(f"{c}({n})" for c,n in top),
      "نمونه":(posts[0].get("text") or "")[:110].replace("\n"," "),"لینک":f"https://t.me/s/{h}"})
    print(f"  ✅ {h:20s} | {len(posts):3d} پست | خریدار {buy:2d} | ☎ {len(ph):3d} | {rows[-1]['حوزه‌ها'][:65]}")
old=list(csv.DictReader(open('output/divar_channels.csv',encoding='utf-8-sig')))
with open('output/divar_channels.csv','w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=["نام","منطقه","handle","پست","خریدار","شماره","حوزه‌ها","نمونه","لینک"]);w.writeheader();w.writerows(old+rows)
print(f"\n💾 مجموع کانال‌های فعال: {len(old)+len(rows)}")
