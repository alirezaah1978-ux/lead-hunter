# -*- coding: utf-8 -*-
"""🚀 استقرار کامل سرور رهیاب روی Hugging Face — همه‌چیز از طریق API (بدون کلیک!)

استفاده:
  python3 hf_deploy.py --hf hf_xxx --bot 123456:ABC --secret mylongsecret [--pat ghp_xxx]

این اسکریپت:
  ۱) Space می‌سازد   ۲) سه فایل را آپلود می‌کند   ۳) سکرت‌ها را ست می‌کند
  ۴) منتظر RUNNING می‌ماند   ۵) وب‌هوک تلگرام را وصل می‌کند   ۶) پیام تست می‌فرستد
  ۷) SPACE_URL را در سکرت‌های گیت‌هاب ثبت می‌کند (ضدخواب ۲۴/۷)
"""
import argparse, json, os, secrets as pysecrets, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
HF_DIR = os.path.join(HERE, "hf")
API = "https://huggingface.co/api"

def post(url, data=None, headers=None, method="POST"):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers or {"Content-Type": "application/json"},
                                 method=method)
    with urllib.request.urlopen(req, timeout=40) as r:
        raw = r.read()
        try: return json.loads(raw)
        except Exception: return {"raw": raw.decode("utf-8", "ignore")}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hf", required=True, help="توکن Hugging Face (write)")
    ap.add_argument("--bot", required=True, help="توکن ربات تلگرام")
    ap.add_argument("--secret", default=None, help="رمز وب‌هوک (خالی = خودکار)")
    ap.add_argument("--chat", default="7662582059")
    ap.add_argument("--pat", default=os.environ.get("GH_PAT", ""), help="توکن گیت‌هاب (برای SPACE_URL)")
    ap.add_argument("--repo", default="alirezaah1978-ux/lead-hunter")
    ap.add_argument("--name", default="rahyab")
    a = ap.parse_args()
    a.secret = a.secret or pysecrets.token_urlsafe(16)

    from huggingface_hub import HfApi, whoami
    api = HfApi(token=a.hf)
    me = whoami(token=a.hf)
    user = me["name"]
    print(f"👤 حساب: {user}")

    # ۱) ساخت Space
    repo_id = f"{user}/{a.name}"
    try:
        api.create_repo(repo_id=repo_id, repo_type="space", space_sdk="docker", private=False, exist_ok=True)
        print(f"✅ Space ساخته شد: https://huggingface.co/spaces/{repo_id}")
    except Exception as e:
        print(f"⚠ ساخت Space: {e}")

    # ۲) آپلود فایل‌ها
    for f in ("app.py", "Dockerfile", "README.md"):
        api.upload_file(path_or_fileobj=os.path.join(HF_DIR, f), path_in_repo=f,
                        repo_id=repo_id, repo_type="space")
        print(f"   ⬆ {f}")

    # ۳) سکرت‌ها
    pairs = {"TELEGRAM_BOT_TOKEN": a.bot, "TELEGRAM_CHAT_ID": a.chat,
             "WEBHOOK_SECRET": a.secret, "GH_REPO": a.repo}
    if a.pat: pairs["GH_PAT"] = a.pat
    for k, v in pairs.items():
        try:
            api.add_space_secret(repo_id=repo_id, key=k, value=v)
            print(f"   🔐 {k} ✓")
        except Exception as e:
            print(f"   ⚠ {k}: {e}")

    # ۴) منتظر RUNNING
    url = f"https://{user}-{a.name}.hf.space"
    print(f"⏳ انتظار بالا آمدن سرور (تا ۵ دقیقه): {url}")
    ok = False
    for i in range(60):
        time.sleep(5)
        try:
            r = post(f"{API}/spaces/{repo_id}/runtime", method="GET") if False else None
            import urllib.request as u
            with u.urlopen(u.Request(f"{API}/spaces/{repo_id}/runtime",
                                     headers={"Authorization": f"Bearer {a.hf}"}), timeout=20) as rr:
                st = json.load(rr)
            stage = st.get("stage", "?")
            print(f"   [{i*5}s] {stage}")
            if stage == "RUNNING":
                ok = True
                for _ in range(20):          # کمی صبر تا اپ جواب بدهد
                    try:
                        with u.urlopen(f"{url}/ping", timeout=20) as pr:
                            if b"ok" in pr.read(): ok = True; break
                    except Exception: time.sleep(5)
                break
            if stage in ("BUILD_ERROR", "RUNTIME_ERROR", "CONFIG_ERROR"):
                print(f"❌ خطای استقرار: {stage}"); sys.exit(1)
        except Exception:
            continue

    # ۵) وب‌هوک تلگرام
    hook = f"{url}/webhook/{a.secret}"
    res = post(f"https://api.telegram.org/bot{a.bot}/setWebhook",
               data={"url": hook}, headers={"Content-Type": "application/json"})
    print(f"🪝 وب‌هوک: {res.get('description', res)}")

    # ۶) پیام تست
    post(f"https://api.telegram.org/bot{a.bot}/sendMessage",
         data={"chat_id": a.chat,
               "text": "🎉 سرور رهیاب بالا آمد! از این لحظه فرمان‌ها لحظه‌ای جواب می‌گیرند.\nبنویس: راهنما | رادار | وضعیت"},
         headers={"Content-Type": "application/json"})
    print("📨 پیام تست ارسال شد")

    # ۷) SPACE_URL در گیت‌هاب
    if a.pat:
        try:
            import base64
            from urllib.request import Request
            pub = None
            req = Request(f"https://api.github.com/repos/{a.repo}/actions/secrets/public-key",
                          headers={"Authorization": f"token {a.pat}", "Accept": "application/vnd.github+json",
                                   "User-Agent": "rahyaab"})
            with urllib.request.urlopen(req, timeout=25) as r:
                pub = json.load(r)
            try:
                from nacl import encoding, public  # PyNaCl
                pk = public.PublicKey(pub["key"].encode(), encoding.Base64Encoder())
                sealed = public.SealedBox(pk).encrypt(url.encode())
                val = base64.b64encode(sealed).decode()
                req = Request(f"https://api.github.com/repos/{a.repo}/actions/secrets/SPACE_URL",
                              data=json.dumps({"encrypted_value": val, "key_id": pub["key_id"]}).encode(),
                              headers={"Authorization": f"token {a.pat}",
                                       "Accept": "application/vnd.github+json",
                                       "User-Agent": "rahyaab", "Content-Type": "application/json"},
                              method="PUT")
                with urllib.request.urlopen(req, timeout=25) as r:
                    print("✅ SPACE_URL در سکرت‌های گیت‌هاب ثبت شد (ضدخواب فعال)")
            except ImportError:
                print("ℹ برای ثبت خودکار SPACE_URL: pip install pynacl")
        except Exception as e:
            print(f"⚠ SPACE_URL ثبت نشد ({type(e).__name__}) — دستی بگذار: {url}")

    print(f"\n🎯 تمام! پنل: {url}\n   در تلگرام به رباتت بنویس: رادار")

if __name__ == "__main__":
    main()
