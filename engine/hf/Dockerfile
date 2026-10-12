# 📡 سرور فرمان رهیاب — تصویر مینیمال بدون وابستگی خارجی
FROM python:3.11-slim

WORKDIR /app
COPY app.py .

ENV PORT=7860
EXPOSE 7860

CMD ["python", "app.py"]
