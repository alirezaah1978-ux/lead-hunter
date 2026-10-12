# ⚡ سرور رهیاب روی Vercel (رایگان، بدون کارت)

سرورلس — همیشه روشن، بدون خواب، بدون کارت بانکی.

## استقرار (من انجام می‌دهم؛ فقط توکن لازم است)
```
cd engine/vercel
npx vercel deploy --prod --yes --token <VC-TOKEN> \
  -e TELEGRAM_BOT_TOKEN=... -e TELEGRAM_CHAT_ID=... \
  -e WEBHOOK_SECRET=... -e GH_PAT=... -e GH_REPO=...
```
سپس: `setWebhook` روی `https://<deploy>.vercel.app/webhook/<WEBHOOK_SECRET>`

## مسیرها
- `/ping` → ok (ضدخواب)
- `/` → پنل (رادار زنده + وضعیت)
- `POST /webhook/<secret>` → فرمان‌های تلگرام: راهنما · رادار · وضعیت · قیمت · فرصت · اسکن · پست
