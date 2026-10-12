#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
#  نصب خودکار استک رهیاب روی سرور Ubuntu (Oracle Free / هر VPS)
#  شامل: Docker + n8n + Windmill + Postgres
#  استفاده: کل این فایل را روی سرور پیست کن (ssh) — یا:
#     bash نصب-یکخطی.sh
#  زمان تقریبی: ۴–۸ دقیقه | بعد از پایان، آدرس‌ها چاپ می‌شوند.
# ═══════════════════════════════════════════════════════════════
set -euo pipefail
say(){ echo -e "\n\033[1;32m▶ $*\033[0m"; }
warn(){ echo -e "\033[1;33m⚠ $*\033[0m"; }

# ---------- ۰) بررسی سیستم ----------
if ! command -v apt-get >/dev/null; then
  warn "این اسکریپت برای Ubuntu/Debian است. اگر ایمیج Oracle Linux داری، ایمیج را به Ubuntu 24.04 تغییر بده."
  exit 1
fi

# ---------- ۱) Docker ----------
if ! command -v docker >/dev/null; then
  say "نصب Docker…"
  sudo apt-get update -y
  sudo apt-get install -y ca-certificates curl gnupg git
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg --yes
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
  sudo apt-get update -y
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  sudo usermod -aG docker "$USER" || true
else
  say "Docker از قبل نصب است ✓"
fi

# ---------- ۲) پوشه‌ی استک ----------
say "ساخت استک در /opt/stack…"
sudo mkdir -p /opt/stack/initdb
sudo chown -R "$USER":"$USER" /opt/stack
cd /opt/stack

cat > initdb/01-databases.sh <<'EOSQL'
#!/bin/bash
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-SQL
  CREATE DATABASE windmill;
  ALTER USER admin SUPERUSER;
SQL
EOSQL
chmod +x initdb/01-databases.sh

cat > docker-compose.yml <<'YAML'
services:
  n8n:
    image: docker.n8n.io/n8nio/n8n:latest
    container_name: n8n
    restart: unless-stopped
    ports: ["5678:5678"]
    environment:
      - TZ=Asia/Tehran
      - GENERIC_TIMEZONE=Asia/Tehran
      - N8N_SECURE_COOKIE=false
      - N8N_RUNNERS_ENABLED=true
    volumes:
      - n8n_data:/home/node/.n8n

  db:
    image: postgres:16
    container_name: stack-db
    restart: unless-stopped
    environment:
      - POSTGRES_USER=admin
      - POSTGRES_PASSWORD=rahyaab_change_me
      - POSTGRES_DB=postgres
    volumes:
      - pg_data:/var/lib/postgresql/data
      - ./initdb:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U admin"]
      interval: 5s
      timeout: 5s
      retries: 20

  windmill_server:
    image: ghcr.io/windmill-labs/windmill:main
    container_name: windmill-server
    restart: unless-stopped
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgres://admin:rahyaab_change_me@db/postgres
      - MODE=server
      - BASE_INTERNAL_URL=http://localhost:8000
    depends_on:
      db:
        condition: service_healthy
      windmill_worker:
        condition: service_started

  windmill_worker:
    image: ghcr.io/windmill-labs/windmill:main
    container_name: windmill-worker
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgres://admin:rahyaab_change_me@db/postgres
      - MODE=worker
      - WORKER_GROUP=default
    shm_size: 1g
    depends_on:
      db:
        condition: service_healthy

volumes:
  n8n_data:
  pg_data:
YAML

# ---------- ۳) اجرا ----------
say "بالا آوردن سرویس‌ها (چند دقیقه طول می‌کشد)…"
sudo docker compose up -d n8n db
sleep 5
sudo docker compose up -d windmill_server windmill_worker || warn "Windmill بالا نیامد — n8n مستقل کار می‌کند (بعداً دوباره تلاش کن)"

# ---------- ۴) فایروال داخلی (اوری‌کل علاوه بر Security List، فایروال داخلی هم دارد) ----------
say "باز کردن پورت‌ها در فایروال داخلی…"
for P in 5678 8000; do
  sudo iptables -C INPUT -p tcp --dport $P -j ACCEPT 2>/dev/null || sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport $P -j ACCEPT || true
done
sudo netfilter-persistent save 2>/dev/null || sudo bash -c 'iptables-save > /etc/iptables/rules.v4' 2>/dev/null || true

# ---------- ۵) گزارش ----------
IP=$(curl -s -m 5 ifconfig.me || echo "<IP-سرور>")
cat <<EOF

════════════════════════════════════════════════════
 ✅ نصب تمام شد
────────────────────────────────────────────────────
  🟢 n8n       →  http://$IP:5678
  🟢 windmill  →  http://$IP:8000
────────────────────────────────────────────────────
  قدم بعدی: این آدرس‌ها را در مرورگر باز کن:
   ۱) n8n: اولین بازشدن، «حساب مالک» می‌سازد (ایمیل+رمز قوی)
   ۲) از من فایل‌های JSON ایمپورت را بگیر:
        - رادار tgju (هر ۳۰ دقیقه → تلگرام)
        - کانال ۳ پست (۲۴ ساعت شبانه‌روز)
  ⚠ اگر صفحه باز نشد: در کنسول اوری‌کل → Networking → Security List
     قواعد Ingress برای پورت‌های 5678 و 8000 (منبع 0.0.0.0/0) اضافه کن.
  🔒 رمز Postgres را در docker-compose.yml عوض کن (فعلی: rahyaab_change_me)
════════════════════════════════════════════════════
EOF
