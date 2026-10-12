# -*- coding: utf-8 -*-
"""
تست دسترسی به دیوار — این را روی هر ماشینی (لپ‌تاپ خودت، VPS، سرور) اجرا کن.
می‌گوید کدام مسیر برای تو کار می‌کند: مستقیم، رله، یا هیچ‌کدام.
    python3 access_test.py
"""
import json, socket, ssl, sys, time, urllib.request, urllib.parse

TARGET = "https://divar.ir/s/tehran"
RELAY = "https://r.jina.ai/"

def probe(url, headers=None, timeout=15):
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
        return {"ok": True, "code": getattr(r, "status", 200), "size": len(body),
                "ms": int((time.time()-t0)*1000), "has_data": b"__PRELOADED_STATE__" in body}
    except Exception as e:
        return {"ok": False, "err": f"{type(e).__name__}: {e}", "ms": int((time.time()-t0)*1000)}

def dns(host):
    try:
        return socket.gethostbyname(host)
    except Exception as e:
        return f"FAIL ({e})"

print("="*66); print("  تست دسترسی به دیوار — کدام مسیر برای تو باز است؟"); print("="*66)
print(f"  DNS دیوار: {dns('divar.ir')}")
print(f"  DNS api : {dns('api.divar.ir')}")

print("\n۱) مسیر مستقیم (بدون واسطه)…")
d = probe(TARGET)
if d["ok"]:
    print(f"   ✅ مستقیم کار می‌کند! ({d['code']} در {d['ms']}ms، داده: {'دارد' if d['has_data'] else 'ندارد'})")
    print("   → کافی است کالکتور را مستقیم اجرا کنی:  python3 sources/divar_relay.py --q پسته")
else:
    print(f"   ❌ مستقیم بسته است ({d['err']})")

print("\n۲) مسیر رله (r.jina.ai)…")
r = probe(RELAY + TARGET, headers={"User-Agent": "Mozilla/5.0", "X-Return-Format": "html"}, timeout=60)
if r["ok"] and r.get("has_data"):
    print(f"   ✅ رله کار می‌کند ({r['ms']}ms، حجم {r['size']//1024}KB، داده: دارد)")
    print("   → کالکتور رله فعال است:  python3 run.py --relay")
elif r["ok"]:
    print(f"   ⚠ رله جواب داد ولی داده ندارد ({r['size']} بایت) — رله را عوض کن یا بعداً امتحان کن")
else:
    print(f"   ❌ رله هم جواب نداد ({r.get('err')})")

print("\n۳) جمع‌بندی و توصیه")
if d["ok"]:
    print("   بهترین حالت: مستقیم. سریع‌ترین و بدون سقف درخواست.")
elif r["ok"] and r.get("has_data"):
    print("   از رله استفاده کن. سقف رایگان Jina حدود ۲۰ درخواست در دقیقه است؛")
    print("   برای حجم بالاتر: کلید رایگان بگیر (jina.ai) یا Worker شخصی بالا بیاور (templates/relay-worker.js).")
else:
    print("   هیچ‌کدام باز نیست. گزینه‌ها:")
    print("   • VPS در آلمان/هلند (۵ یورو در ماه) — معمولاً مستقیم کار می‌کند")
    print("   • Worker روی Cloudflare (رایگان) به عنوان رله‌ی شخصی — templates/relay-worker.js")
    print("   • سرویس اسکرپینگ پولی (ScraperAPI و مانند آن) — گران‌تر ولی پایدار")
print("\n💡 نکته: اگر روی سرور داخل ایران اجرا می‌کنی، مستقیم کار می‌کند ولی برای فرستادن داده به بیرون به یک واسطه نیاز داری.")
