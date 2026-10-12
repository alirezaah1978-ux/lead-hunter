# -*- coding: utf-8 -*-
"""
کالکتور دیوار از طریق رله — نسخه‌ی کارکرده و تست‌شده.
روش کار: صفحه‌ی دیوار سرور-رندر است و کل دیتای آگهی‌ها در `window.__PRELOADED_STATE__` داخل HTML قرار دارد.
پس فقط کافی است HTML را با یک رله (پیش‌فرض: r.jina.ai) بگیریم و JSON را از داخلش استخراج کنیم.
نیازی به API غیررسمی، لاگین، یا IP ایران نیست.

ویژگی‌ها: کش روی دیسک، فاصله‌ی محترمانه بین درخواست‌ها، backoff در خطا، پارسر قیمت/زمان فارسی.
"""
import json, os, re, time, hashlib, urllib.request, urllib.parse, argparse
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "_cache"); os.makedirs(CACHE, exist_ok=True)
RELAY = os.environ.get("RELAY_BASE", "https://r.jina.ai/")   # رله‌ی عمومی یا رله‌ی شخصی خودت (Worker)
MIN_INTERVAL = 4.0                     # ثانیه؛ محترمانه و بدون بن
_last = [0.0]

def _throttle():
    dt = time.time() - _last[0]
    if dt < MIN_INTERVAL: time.sleep(MIN_INTERVAL - dt)
    _last[0] = time.time()

def _cache_path(url):
    return os.path.join(CACHE, hashlib.md5(url.encode()).hexdigest() + ".html")

def fetch(url, use_cache=True, retries=3, cache_ttl=6*3600):
    """cache_ttl=0 یعنی همیشه تازه بگیر (برای هشدار فوری لازم است)."""
    cp = _cache_path(url)
    if use_cache and cache_ttl > 0 and os.path.exists(cp) and time.time() - os.path.getmtime(cp) < cache_ttl:
        return open(cp, encoding="utf-8").read()
    for attempt in range(retries):
        _throttle()
        try:
            target = RELAY + url
            if cache_ttl <= 0 and "?" in RELAY:      # رله‌ی شخصی: کش را دور بزن
                target += "&ttl=0"
            req = urllib.request.Request(target, headers={
                "User-Agent": "Mozilla/5.0 (compatible; B2B-lead-research/1.0)",
                "X-Return-Format": "html",
            })
            with urllib.request.urlopen(req, timeout=90) as r:
                html = r.read().decode("utf-8", "replace")
            if "__PRELOADED_STATE__" in html:
                open(cp, "w", encoding="utf-8").write(html)
                return html
            print(f"    ⚠ پاسخ بدون داده (طول {len(html)}) — تلاش مجدد")
        except Exception as e:
            wait = 8 * (attempt + 1)
            print(f"    ⛔ {type(e).__name__}: {e} — {wait} ثانیه صبر")
            time.sleep(wait)
    return ""

# ---------- پارسر ----------
def state(html):
    i = html.find("window.__PRELOADED_STATE__ = ")
    if i < 0: return {}
    obj, _ = json.JSONDecoder().raw_decode(html[i + len("window.__PRELOADED_STATE__ = "):])
    return obj

FA = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")

def price_of(txt):
    if not txt: return None
    t = txt.translate(FA).replace("٬", "").replace(",", "")
    if "توافقی" in t or "مقطوع" in t and not re.search(r"\d", t): return None
    m = re.search(r"(\d+)\s*(میلیارد|میلیون|هزار)?", t)
    if not m: return None
    v = int(m.group(1)); mult = {"میلیارد": 10**9, "میلیون": 10**6, "هزار": 10**3, None: 1}[m.group(2)]
    return v * mult

def age_minutes(txt):
    """دقت دقیقه‌ای — برای تشخیص «آگهی تازه» که هنوز کسی زنگ نزده."""
    if not txt: return 48*60
    t = txt.translate(FA)
    m = re.search(r"(\d+)\s*(دقیقه|ساعت|روز|هفته|ماه)", t)
    if not m: return 48*60
    n, u = int(m.group(1)), m.group(2)
    return {"دقیقه": n, "ساعت": n*60, "روز": n*1440, "هفته": n*10080, "ماه": n*43200}[u]

def age_hours(txt):
    return max(1, age_minutes(txt) // 60)

def district_of(txt):
    if not txt: return ""
    m = re.search(r"در\s+(.+)$", txt.strip())
    return m.group(1).strip() if m else txt.strip()

def rows_from(html, city_slug, city_fa):
    wl = state(html).get("nb", {}).get("listWidgets", [])
    out = []
    for w in wl:
        dto = w.get("data", {}).get("dto", {})
        if dto.get("widget_type") != "POST_ROW": continue
        d = dto.get("data", {})
        tok = d.get("action", {}).get("payload", {}).get("token", "")
        bottom = d.get("bottom_description_text", "")
        out.append({
            "id": f"dv-{tok}",
            "source": "دیوار",
            "token": tok,
            "title": d.get("title", ""),
            "desc": "",                                        # با details() پر می‌شود
            "price": price_of(d.get("middle_description_text", "")),
            "qty": None,
            "age_hours": age_hours(bottom),
            "age_minutes": age_minutes(bottom),
            "city": city_fa, "province": "",
            "district": district_of(bottom),
            "image": d.get("image_url", ""),
            "url": f"https://divar.ir/v/{tok}",
            "fetched_at": datetime.now().isoformat(timespec="minutes"),
            "raw": f"{d.get('title','')} {d.get('middle_description_text','')} {bottom}",
        })
    return out

def search(city_slug="tehran", city_fa="تهران", query="", category="", cache_ttl=6*3600):
    """جست‌وجوی SSR دیوار. فرمت کارکرده: divar.ir/s/{city}?q={query}"""
    url = f"https://divar.ir/s/{city_slug}"
    if category: url += "/" + category
    if query: url += "?q=" + urllib.parse.quote(query)
    html = fetch(url, cache_ttl=cache_ttl)
    return rows_from(html, city_slug, city_fa) if html else []

def details(token):
    """توضیحات و مشخصات کامل یک آگهی از صفحه‌ی /v/{token}"""
    html = fetch(f"https://divar.ir/v/{token}")
    if not html: return {}
    s = state(html)
    txt = json.dumps(s, ensure_ascii=False)
    desc = ""
    m = re.search(r'"description"\s*:\s*"((?:[^"\\]|\\.)*)"', txt)
    if m:
        try: desc = json.loads(f'"{m.group(1)}"')
        except Exception: desc = m.group(1)
    return {"desc": desc}

CITIES = {"tehran": "تهران", "mashhad": "مشهد", "isfahan": "اصفهان", "kerman": "کرمان",
          "tabriz": "تبریز", "shiraz": "شیراز", "ahvaz": "اهواز", "qom": "قم",
          "karaj": "کرج", "rasht": "رشت"}

def crawl(queries, cities=("tehran", "kerman"), with_details=False, detail_limit=6, cache_ttl=6*3600):
    all_rows, seen = [], set()
    for c in cities:
        for q in queries:
            rows = search(c, CITIES.get(c, c), q, cache_ttl=cache_ttl)
            new = [r for r in rows if r["token"] not in seen]
            seen |= {r["token"] for r in new}
            all_rows += new
            print(f"  🏠 دیوار | {CITIES.get(c,c)} | «{q}» → {len(new)} آگهی جدید (از {len(rows)})")
    if with_details:
        for r in all_rows[:detail_limit]:
            d = details(r["token"])
            r["desc"] = d.get("desc", "")
    return all_rows

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--q", nargs="+", default=["پسته"])
    ap.add_argument("--cities", nargs="+", default=["tehran"])
    ap.add_argument("--details", action="store_true")
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    rows = crawl(a.q, tuple(a.cities), with_details=a.details)
    print(f"\n✔ مجموع {len(rows)} آگهی")
    for r in rows[:8]:
        print(f"   • {r['title'][:55]} | {r['price']} | {r['district']} | {r['age_hours']}h")
    if a.json:
        json.dump(rows, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("✔ ذخیره شد:", a.json)
