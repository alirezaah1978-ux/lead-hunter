# -*- coding: utf-8 -*-
"""
کالکتور واقعی دیوار — همین API-ی که خود سایت دیوار در مرورگر صدا می‌زند.
⚠️ نکته‌ی حیاتی: دیوار درخواست‌های خارج از ایران را می‌بندد؛ این اسکریپت باید روی
   سرور/IP ایران اجرا شود. (در سندباکس ما تست شد: block است.)
⚠️ این API غیررسمی است و دیوار می‌تواند تغییرش دهد. برای مسیر رسمی: «کنار دیوار» (kenar.divar.ir)
   که نیاز به تأیید اپ و OAuth دارد و رقابت مستقیم با دیوار را مجاز نمی‌داند.
"""
import json, time, random, urllib.request, urllib.error

BASE = "https://api.divar.ir"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
    "Accept": "application/json",
}

# شهردId و slug دسته را یک‌بار از DevTools روی divar.ir بردار و اینجا بگذار
CITY_IDS = {"تهران": "1", "کرمان": "5", "اصفهان": "4", "مشهد": "3", "قزوین": "13"}

def search(city="تهران", query="پسته", page=1, category=None):
    """POST /v8/postlist/w/search — همان درخواستی که خود سایت می‌زند."""
    form = {"data": {"category": {"str": {"value": category or ""}}}}
    if query:
        form["data"]["q"] = {"str": {"value": query}}
    payload = {
        "city_ids": [CITY_IDS.get(city, "1")],
        "search_data": {"form_data": form, "server_payload": None},
        "pagination_data": {"@type": "type.googleapis.com/post_list.PaginationData",
                            "page": page, "layer_page": page, "last_post_date": ""},
    }
    req = urllib.request.Request(f"{BASE}/v8/postlist/w/search", data=json.dumps(payload).encode(),
                                 headers=HEADERS)
    with urllib.request.urlopen(req, timeout=25) as r:
        data = json.loads(r.read().decode())

    out = []
    for w in data.get("list_widgets", []) or data.get("web_widgets", []):
        if w.get("widget_type") not in ("POST_ROW", "post_row"): continue
        d = w.get("data", {})
        title = d.get("title", "")
        out.append({
            "id": f"dv-{d.get('token','')[:10]}",
            "source": "دیوار",
            "title": title,
            "desc": " ".join(x.get("value","") for x in d.get("middle_description_text", [])),
            "price": _parse_price(d.get("middle_description_text", [])),
            "age_hours": _age(d.get("bottom_description_text","")),
            "city": city, "url": f"https://divar.ir/v/{d.get('token','')}",
            "raw": title,
        })
    return out

def _parse_price(parts):
    """قیمت از ویجت دیوار: «۱٬۱۸۰٬۰۰۰ تومان» → عدد"""
    for p in parts or []:
        v = str(p.get("value","")).replace("٬","").replace(",","")
        digits = "".join(ch for ch in v.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹","0123456789")) if ch.isdigit())
        if digits and "تومان" in str(p.get("value","")):
            return int(digits)
    return None

def _age(txt):
    t = str(txt)
    n = "".join(ch for ch in t.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹","0123456789")) if ch.isdigit())
    n = int(n) if n else 1
    if "دقیقه" in t: return max(1, n//60)
    if "ساعت" in t:  return n
    if "روز" in t:   return n*24
    if "هفته" in t:  return n*24*7
    return 48

def crawl(queries, city="تهران", pages=3, sleep_range=(2.0, 4.5)):
    """کشیدن آرام و با فاصله — عدد بالا: کمی صبر کن، بن نشو."""
    rows = []
    for q in queries:
        for p in range(1, pages+1):
            try:
                got = search(city=city, query=q, page=p)
                rows += got
                print(f"  دیوار | {city} | «{q}» | صفحه {p} → {len(got)} آگهی")
                if not got: break
            except urllib.error.HTTPError as e:
                print(f"  ⛔ خطای HTTP {e.code} روی «{q}» — صبر می‌کنم"); time.sleep(30)
            except Exception as e:
                print(f"  ⛔ {type(e).__name__}: {e}"); break
            time.sleep(random.uniform(*sleep_range))
    return rows

if __name__ == "__main__":
    rows = crawl(["پسته", "میلگرد", "کارتن ضایعاتی"], city="تهران", pages=2)
    print(json.dumps(rows[:5], ensure_ascii=False, indent=2))
