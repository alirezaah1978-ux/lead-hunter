# -*- coding: utf-8 -*-
"""
🇮🇷 «واسطه‌ی داخل ایران» — نود ارسال
اگر سرور خارج از ایران (مثل GitHub Actions) به API بله/روبیکا/ایتا دسترسی نداشت،
این فایل را روی یک دستگاه داخل ایران اجرا کن (لپ‌تاپ، رزبری‌پای، کامپیوتر خانه).
بعد با «تونل ابری کلودفلر» (رایگان) آن را به اینترنت وصل کن تا از بیرون بتوانند پیام بفرستند.

اجرا (روی دستگاه داخل ایران):
    export RELAY_SECRET="یک-رمز-تصادفی-طولانی"
    export BALE_BOT_TOKEN="..." BALE_CHAT_ID="..."        # هر پلتفرمی که می‌خواهی
    export RUBIKA_BOT_TOKEN="..." RUBIKA_CHAT_ID="..."
    export EITAA_BOT_TOKEN="..."  EITAA_CHAT_ID="@my_channel"
    python3 iran_sender_node.py --port 8787

در ترمینال دوم (همان دستگاه):
    cloudflared tunnel --url http://127.0.0.1:8787
    → یک آدرس عمومی مثل https://xxx-yyy-zzz.trycloudflare.com می‌دهد.
      این آدرس را در GitHub Secrets بگذار: RELAY_URL=https://xxx...trycloudflare.com

نکته‌های امنیتی:
  • درخواست‌ها فقط با هدر X-Auth و رمز درست پذیرفته می‌شوند.
  • سرور فقط روی 127.0.0.1 گوش می‌دهد (از شبکه‌ی محلی هم باز نیست).
  • آدرس تونل را جایی عمومی منتشر نکن؛ هر کس آن را داشته باشد می‌تواند پیام بفرستد.
  • تونل trycloudflare آدرسش هر بار اجرا عوض می‌شود. برای آدرس ثابت: تونل نام‌دار کلودفلر.
"""
import json, os, sys, argparse, secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from notify_multi import broadcast, configured

SECRET = os.environ.get("RELAY_SECRET", "")
MAX_BYTES = 200_000

class Handler(BaseHTTPRequestHandler):
    server_version = "iran-sender/1.0"

    def _reply(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/health"):
            self._reply(200, {"ok": True, "platforms": configured()})
        else:
            self._reply(404, {"ok": False, "err": "not found"})

    def do_POST(self):
        if not self.path.startswith("/send"):
            return self._reply(404, {"ok": False, "err": "not found"})
        if not SECRET or self.headers.get("X-Auth") != SECRET:
            return self._reply(403, {"ok": False, "err": "رمز نامعتبر"})
        try:
            ln = int(self.headers.get("Content-Length", 0))
            if ln > MAX_BYTES: return self._reply(413, {"ok": False, "err": "پیام خیلی بزرگ"})
            data = json.loads(self.rfile.read(ln).decode("utf-8"))
        except Exception as e:
            return self._reply(400, {"ok": False, "err": f"بدنه نامعتبر: {e}"})

        text = data.get("text", "")
        only = data.get("only") or None
        if not text: return self._reply(400, {"ok": False, "err": "text خالی است"})
        try:
            out = broadcast(text, only=only, dry=bool(data.get("dry")))
            return self._reply(200, {"ok": True, "result": {k: v.get("ok") for k, v in out.items()}})
        except Exception as e:
            return self._reply(500, {"ok": False, "err": f"{type(e).__name__}: {e}"})

    def log_message(self, fmt, *args):
        print(f"[نود] {self.address_string()} — {fmt % args}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8787)
    a = ap.parse_args()
    if not SECRET:
        SECRET = input("RELAY_SECRET تنظیم نشده. یک رمز تصادفی بسازم؟ (Enter برای ساخت خودکار): ").strip()
        if not SECRET:
            SECRET = secrets.token_urlsafe(24)
            print(f"\n🔑 رمز ساخته شد — این را در GitHub Secrets بگذار (RELAY_SECRET):\n{SECRET}\n")
        os.environ["RELAY_SECRET"] = SECRET
    print(f"🇮🇷 نود ارسال روی http://127.0.0.1:{a.port} بالا آمد")
    print(f"   پلتفرم‌های آماده: {configured() or '⚠ هیچ‌کدام! توکن‌ها را ست کن'}")
    print(f"   سلامت: http://127.0.0.1:{a.port}/health   |   ارسال: POST /send  (هدر X-Auth)")
    ThreadingHTTPServer(("127.0.0.1", a.port), Handler).serve_forever()
