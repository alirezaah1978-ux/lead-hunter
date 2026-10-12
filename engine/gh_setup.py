# -*- coding: utf-8 -*-
"""
🚀 واسطه‌ی گیت‌هاب — همه‌ی کارهای گیت‌هاب را بدون کلیک‌کردن انجام می‌دهد.
می‌تواند روی ماشین من (رهیاب) اجرا شود یا روی کامپیوتر خودت — در هر دو حالت یکسان کار می‌کند.

قابلیت‌ها:
  1) create-repo : ساخت ریپو (اگر خودت نساخته باشی)
  2) push        : آپلود کل پروژه با یک کامیت (شامل پوشه‌ی مخفی .github)
  3) secrets     : ساخت Secrets با رمزنگاری استاندارد گیت‌هاب (توکن تلگرام و...)
  4) run         : اجرای ورک‌فلو و گزارش نتیجه‌ی واقعی (سبز/قرمز + خطا)
  5) status      : وضعیت آخرین اجراها

نمونه:
  python3 gh_setup.py create-repo --token ghp_xxx --name lead-hunter
  python3 gh_setup.py push        --token ghp_xxx --repo USER/lead-hunter
  python3 gh_setup.py secrets     --token ghp_xxx --repo USER/lead-hunter \
                                  --set TELEGRAM_BOT_TOKEN=7123:ABC --set TELEGRAM_CHAT_ID=123
  python3 gh_setup.py run         --token ghp_xxx --repo USER/lead-hunter \
                                  --workflow 00-test-connection.yml --wait
  python3 gh_setup.py status      --token ghp_xxx --repo USER/lead-hunter
"""
import argparse, base64, json, os, subprocess, sys, time, urllib.request, urllib.error

API = "https://api.github.com"
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(HERE)          # ریشه‌ی پروژه (پوشه‌ی بالای engine)
UA = {"User-Agent": "rahyab-setup/1.0", "Accept": "application/vnd.github+json"}

# فایل‌هایی که آپلود می‌شوند (کش موقت حذف می‌شود)
INCLUDE = ["engine", "templates", ".github", "send_test.py",
           "STATUS.md", "NEXT.md", "راهنمای-قدم-به-قدم.md", "گام-صفر-روشن‌سازی-ارسال.md"]
EXCLUDE_DIRS = {"_cache", "__pycache__", "node_modules", ".git", "_probe"}

def _req(method, path, token, body=None, raw=False):
    url = path if path.startswith("http") else API + path
    data = json.dumps(body).encode() if body is not None else None
    hdr = dict(UA)
    if token: hdr["Authorization"] = f"Bearer {token}"
    if data: hdr["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=hdr, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            payload = r.read()
        return json.loads(payload) if payload else {}
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", "replace")[:400]
        print(f"⛔ خطای گیت‌هاب ({e.code}): {msg}")
        if e.code == 401: print("   → توکن نامعتبر یا منقضی است.")
        if e.code == 403: print("   → توکن دسترسی لازم را ندارد (Contents/Workflows/Actions/Secrets).")
        if e.code == 404: print("   → ریپو پیدا نشد یا توکن به آن دسترسی ندارد (دامنه‌ی دسترسی PAT را چک کن).")
        sys.exit(1)

# ---------- ۱) ساخت ریپو ----------
def create_repo(a):
    r = _req("POST", "/user/repos", a.token, {
        "name": a.name,
        "description": "فرصت‌یاب خودکار بازار — دیوار + تلگرام (ساخته‌شده توسط رهیاب)",
        "private": bool(a.private),
        "auto_init": False,
    })
    print(f"✅ ریپو ساخته شد: {r['html_url']}\n   دامنه: {r['owner']['login']}/{r['name']}")

# ---------- ۲) آپلود پروژه ----------
def _collect():
    files = []
    for item in INCLUDE:
        p = os.path.join(PROJECT_DIR, item)
        if os.path.isfile(p):
            files.append((item, p)); continue
        for root, dirs, names in os.walk(p):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for n in names:
                if n.endswith((".pyc",)): continue
                fp = os.path.join(root, n)
                rel = os.path.relpath(fp, PROJECT_DIR)
                if os.path.getsize(fp) > 400_000 and "assets" not in rel:
                    continue                      # دیتای خام بزرگ لازم نیست در ریپو باشد
                files.append((rel, fp))
    return files

def push(a):
    files = _collect()
    total = sum(os.path.getsize(f) for _, f in files)
    print(f"📦 {len(files)} فایل ({total//1024} KB) آماده‌ی آپلود")
    if not os.path.exists(os.path.join(PROJECT_DIR, ".git")):
        subprocess.run(["git", "init", "-q"], cwd=PROJECT_DIR, check=True)
    subprocess.run(["git", "checkout", "-q", "-B", "main"], cwd=PROJECT_DIR, check=True)
    subprocess.run(["git", "config", "user.email", "rahyab@local"], cwd=PROJECT_DIR, check=True)
    subprocess.run(["git", "config", "user.name", "Rahyab Setup"], cwd=PROJECT_DIR, check=True)
    for rel, fp in files:
        subprocess.run(["git", "add", "-f", rel], cwd=PROJECT_DIR, check=True)
    subprocess.run(["git", "-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty", "-m",
                    "راه‌اندازی فرصت‌یاب خودکار (دیوار + تلگرام)"], cwd=PROJECT_DIR)
    url = f"https://x-access-token:{a.token}@github.com/{a.repo}.git"
    r = subprocess.run(["git", "push", "-q", "-f", url, "main:main"], cwd=PROJECT_DIR,
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("⛔ خطای push:\n", (r.stderr or r.stdout)[-600:])
        print("\n💡 معمولاً یعنی: توکن scope ندارد (نیاز: repo + workflow) یا ریپو درست نیست.")
        sys.exit(1)
    print(f"✅ پروژه آپلود شد → https://github.com/{a.repo}")
    print("   (شامل پوشه‌ی مخفی .github و همه‌ی ورک‌فلوها)")

# ---------- ۳) Secrets ----------
def set_secrets(a):
    from nacl import encoding, public
    pk = _req("GET", f"/repos/{a.repo}/actions/secrets/public-key", a.token)
    key = public.PublicKey(pk["key"].encode(), encoding.Base64Encoder())
    for kv in a.set or []:
        if "=" not in kv:
            print("⚠ نادیده گرفته شد (فرمت باید KEY=VALUE باشد):", kv); continue
        name, value = kv.split("=", 1)
        sealed = base64.b64encode(public.SealedBox(key).encrypt(value.encode())).decode()
        _req("PUT", f"/repos/{a.repo}/actions/secrets/{name}", a.token,
             {"encrypted_value": sealed, "key_id": pk["key_id"]})
        print(f"✅ Secret ثبت شد: {name}")
    if not (a.set or []):
        print("ℹ️ چیزی برای ثبت ندادی (--set KEY=VALUE)")

def list_secrets(a):
    r = _req("GET", f"/repos/{a.repo}/actions/secrets", a.token)
    print(f"🔐 {r.get('total_count', 0)} Secret ثبت‌شده:")
    for s in r.get("secrets", []):
        print(f"   • {s['name']}  (آخرین تغییر: {s.get('updated_at','?')[:10]})")

# ---------- ۴) اجرای ورک‌فلو ----------
def run_workflow(a):
    _req("POST", f"/repos/{a.repo}/actions/workflows/{a.workflow}/dispatches", a.token, {"ref": "main"})
    print(f"🚀 ورک‌فلو «{a.workflow}» اجرا شد. منتظر نتیجه…")
    if not a.wait: return
    run = None
    for i in range(60):                      # تا ۵ دقیقه
        time.sleep(5)
        r = _req("GET", f"/repos/{a.repo}/actions/workflows/{a.workflow}/runs?per_page=1", a.token)
        runs = r.get("workflow_runs", [])
        if not runs: continue
        run = runs[0]
        if run["status"] == "completed": break
        print(f"   … {run['status']} ({i*5} ثانیه)", end="\r")
    if not run or run["status"] != "completed":
        print("\n⚠ نتیجه نامشخص — در گیت‌هاب Actions چک کن."); return
    ok = run["conclusion"] == "success"
    print(f"\n{'✅ موفق!' if ok else '⛔ ناموفق'}   نتیجه: {run['conclusion']}")
    print(f"   جزئیات: {run['html_url']}")
    if not ok:
        jid = run["id"]
        jobs = _req("GET", f"/repos/{a.repo}/actions/runs/{jid}/jobs", a.token)
        for j in jobs.get("jobs", []):
            for st in j.get("steps", []):
                if st.get("conclusion") == "failure":
                    print(f"   ❌ گام ناموفق: {st['name']}")
        print("\n📋 لاگ کامل را از لینک بالا ببین، یا متن خطا را برای رهیاب بفرست.")

def all_in_one(a):
    """همه‌چیز با یک دستور: ساخت ریپو → آپلود → Secrets → اجرای تست"""
    class NS: pass
    repo = a.repo
    if not repo:
        r = _req("POST", "/user/repos", a.token, {
            "name": a.name, "description": "فرصت‌یاب خودکار بازار (رهیاب)",
            "private": bool(a.private), "auto_init": False})
        repo = r["full_name"]
        print(f"✅ ریپو ساخته شد: {r['html_url']}")
        print(f"   ⚠ اگر ریپو را خصوصی ساختی، سهمیه‌ی Actions ماهانه ۲۰۰۰ دقیقه است (کافی نیست) → عمومی بهتر است")
    ns = NS(); ns.token = a.token; ns.repo = repo; push(ns)
    kvs = list(a.set or [])
    for k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "RELAY_BASE"):
        v = os.environ.get(k)
        if v: kvs.append(f"{k}={v}")
    if kvs:
        ns2 = NS(); ns2.token = a.token; ns2.repo = repo; ns2.set = kvs; set_secrets(ns2)
    ns3 = NS(); ns3.token = a.token; ns3.repo = repo
    ns3.workflow = a.workflow; ns3.wait = True; run_workflow(ns3)
    ns4 = NS(); ns4.token = a.token; ns4.repo = repo; status(ns4)
    print(f"\n🎉 تمام. پنل: https://github.com/{repo}/actions")

def status(a):
    r = _req("GET", f"/repos/{a.repo}/actions/runs?per_page=8", a.token)
    runs = r.get("workflow_runs", [])
    if not runs: print("ℹ️ هنوز هیچ اجرایی ثبت نشده."); return
    icon = {"success": "✅", "failure": "⛔", "cancelled": "⚪️", None: "🟡"}
    for run in runs:
        print(f"  {icon.get(run['conclusion'],'🟡')} {run['name'][:38]:40} "
              f"{run['created_at'][:16].replace('T',' ')}  {run['conclusion'] or run['status']}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="واسطه‌ی گیت‌هاب — راه‌اندازی خودکار پروژه")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("create-repo"); p.add_argument("--token", required=True)
    p.add_argument("--name", default="lead-hunter"); p.add_argument("--private", action="store_true")
    p.set_defaults(fn=create_repo)

    p = sub.add_parser("push"); p.add_argument("--token", required=True)
    p.add_argument("--repo", required=True, help="مثال: username/lead-hunter"); p.set_defaults(fn=push)

    p = sub.add_parser("secrets"); p.add_argument("--token", required=True)
    p.add_argument("--repo", required=True); p.add_argument("--set", action="append")
    p.add_argument("--list", action="store_true"); p.set_defaults(fn=lambda a: list_secrets(a) if a.list else set_secrets(a))

    p = sub.add_parser("run"); p.add_argument("--token", required=True)
    p.add_argument("--repo", required=True); p.add_argument("--workflow", default="00-test-connection.yml")
    p.add_argument("--wait", action="store_true"); p.set_defaults(fn=run_workflow)

    p = sub.add_parser("all", help="همه‌چیز با یک دستور")
    p.add_argument("--token", required=True)
    p.add_argument("--name", default="lead-hunter")
    p.add_argument("--repo", help="اگر ریپو از قبل هست: username/name")
    p.add_argument("--private", action="store_true")
    p.add_argument("--workflow", default="00-test-connection.yml")
    p.add_argument("--set", action="append", help="KEY=VALUE")
    p.set_defaults(fn=all_in_one)

    p = sub.add_parser("status"); p.add_argument("--token", required=True)
    p.add_argument("--repo", required=True); p.set_defaults(fn=status)

    a = ap.parse_args()
    a.fn(a)
