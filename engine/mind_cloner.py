#!/usr/bin/env python3
"""
Universal Mind Cloner (مهندسی معکوس هر کانال تلگرام: متن کامل + صدای داخل ویس‌ها)
"""
import os, re, json, html, urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUT_DIR, exist_ok=True)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def clone_telegram_channel(handle: str, max_pages: int = 15) -> dict:
    ch = handle.strip().lstrip("@").split("/")[-1].strip()
    posts = {}
    before = None
    for _ in range(max_pages):
        url = f"https://t.me/s/{ch}" + (f"?before={before}" if before else "")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            raw = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
        except Exception:
            break
        chunks = re.split(r'<div class="tgme_widget_message_wrap[^>]*>', raw)[1:]
        if not chunks:
            break
        ids = []
        for c in chunks:
            m = re.search(rf'data-post="{re.escape(ch)}/(\d+)"', c)
            if not m:
                continue
            pid = int(m.group(1))
            ids.append(pid)
            tx_m = re.search(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>', c, re.S)
            txt = ""
            if tx_m:
                t = re.sub(r"<br\s*/?>", "\n", tx_m.group(1))
                t = re.sub(r"<[^>]+>", "", t)
                txt = html.unescape(t).strip()
            vw_m = re.search(r'<span class="tgme_widget_message_views">([^<]+)</span>', c)
            au_m = re.search(r'<audio[^>]+src="([^"]+)"', c)
            posts[pid] = {
                "id": pid,
                "text": txt,
                "views": vw_m.group(1).strip() if vw_m else "",
                "has_voice": bool(au_m),
            }
        if not ids:
            break
        mn = min(ids)
        if mn <= 1 or before == mn:
            break
        before = mn

    ordered = [posts[k] for k in sorted(posts.keys())]
    out_file = os.path.join(OUT_DIR, f"clone_{ch}.json")
    json.dump(ordered, open(out_file, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    total_words = sum(len((p.get("text") or "").split()) for p in ordered)
    voices = sum(1 for p in ordered if p.get("has_voice"))
    return {
        "channel": ch,
        "posts_count": len(ordered),
        "total_words": total_words,
        "voices_count": voices,
        "path": out_file,
    }
