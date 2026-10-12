# -*- coding: utf-8 -*-
"""پیدا کردن خودکار chat_id کانال و ثبت آن در پنل کنترل.
پیش‌نیاز: ربات ادمین کانال باشد و حداقل یک پیام در کانال باشد.
  python3 kanal_setup.py
"""
import os, sys, json, urllib.request, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
if not TOKEN:
    print("⛔ توکن ربات نیست (TELEGRAM_BOT_TOKEN)"); sys.exit(1)

url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?limit=100&allowed_updates=%5B%22channel_post%22%2C%22my_chat_member%22%5D"
upd = json.load(urllib.request.urlopen(url, timeout=30))
found = {}
for u in upd.get("result", []):
    for k in ("channel_post", "edited_channel_post", "my_chat_member"):
        c = (u.get(k) or {}).get("chat")
        if c and c.get("type") == "channel":
            found[c["id"]] = c.get("title", "")

if not found:
    print("⚪ کانالی پیدا نشد. مطمئن شو: ۱) ربات ادمین کانال است ۲) یک پیام در کانال گذاشته‌ای")
    sys.exit(0)

print("🎯 کانال‌های پیدا‌شده:")
for cid, title in found.items():
    print(f"   • {title} → chat_id = {cid}")

cid, title = list(found.items())[0]
p = os.path.join(HERE, "settings.json")
d = json.load(open(p, encoding="utf-8"))
d.setdefault("content_kanal", {})["chat_id"] = cid
d["content_kanal"]["نام"] = title
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"\n✅ در پنل کنترل ثبت شد: {title} ({cid})")
print("   از این لحظه هر محتوایی که منتشر شود، یک نسخه هم در کانال می‌رود.")
