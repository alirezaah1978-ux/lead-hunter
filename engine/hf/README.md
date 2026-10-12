---
title: Rahyaab Control
emoji: 📡
colorFrom: indigo
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# 📡 مرکز فرمان رهیاب

سرور سبک رایگان روی Hugging Face Space:
- وب‌هوک تلگرام → پاسخ **لحظه‌ای** به فرمان‌ها (رادار / وضعیت / قیمت / فرصت / اسکن / پست)
- داشبورد وضعیت در صفحه‌ی اصلی
- `/ping` برای بیدار نگه‌داشتن (پینگ خودکار از GitHub Actions)

## رمزها (Settings → Variables and secrets → Secrets)
| نام | چیست |
|---|---|
| `TELEGRAM_BOT_TOKEN` | توکن ربات تلگرام |
| `TELEGRAM_CHAT_ID` | چت‌آیدی مالک (فقط او فرمان می‌دهد) |
| `WEBHOOK_SECRET` | رمز مسیر وب‌هوک (حداقل ۲۰ کاراکتر تصادفی) |
| `GH_PAT` | (اختیاری) توکن گیت‌هاب برای انتشار فوری محتوا |
| `GH_REPO` | `alirezaah1978-ux/lead-hunter` |

## فعال‌سازی وب‌هوک (یک‌بار)
در مرورگر باز کن:
`https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<USER>-<SPACE>.hf.space/webhook/<WEBHOOK_SECRET>`
