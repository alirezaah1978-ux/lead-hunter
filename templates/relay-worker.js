// ===================================================================
// رله‌ی شخصی دیوار روی Cloudflare Workers (پلن رایگان: ۱۰۰٬۰۰۰ درخواست در روز)
// چرا؟ چون رله‌های عمومی سقف درخواست دارند و ممکن است روزی بمیرند.
// نصب: ۱) workers.cloudflare.com → Create Worker  ۲) این کد را جایگزین کن  ۳) Deploy
// استفاده: https://YOUR-WORKER.workers.dev/?url=https://divar.ir/s/tehran%3Fq%3D%D9%BE%D8%B3%D8%AA%D9%87
// سپس در divar_relay.py مقدار RELAY را بگذار: "https://YOUR-WORKER.workers.dev/?url="
// ⚠️ توجه: این فقط برای مصارف شخصی و با حجم کم. ربات‌های اسپم نساز.
// ===================================================================

const ALLOWED_HOSTS = ["divar.ir", "www.divar.ir"];   // فقط دیوار، تا رله‌ی سوءاستفاده نشود

export default {
  async fetch(request, env, ctx) {
    const u = new URL(request.url);
    const target = u.searchParams.get("url");
    if (!target) {
      return new Response("Usage: ?url=https://divar.ir/s/tehran%3Fq%3D...", { status: 400 });
    }
    let t;
    try { t = new URL(target); } catch { return new Response("bad url", { status: 400 }); }
    if (!ALLOWED_HOSTS.includes(t.hostname)) {
      return new Response("host not allowed", { status: 403 });
    }

    // مدت کش قابل تنظیم: پیش‌فرض ۱۰ دقیقه. با ?ttl=0 کش کاملاً دور زده می‌شود (برای هشدار فوری فوری‌ترین حالت).
    const ttl = parseInt(u.searchParams.get("ttl") ?? "600", 10);
    const cache = caches.default;
    const key = new Request(t.toString(), { method: "GET" });
    if (ttl > 0) {
      const hit = await cache.match(key);
      if (hit) return new Response(hit.body, { headers: { ...Object.fromEntries(hit.headers), "x-cache": "HIT" } });
    }

    res = await fetch(t.toString(), {
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "fa-IR,fa;q=0.9",
      },
      redirect: "follow",
    });

    const body = await res.text();
    const out = new Response(body, {
      status: res.status,
      headers: {
        "content-type": "text/html; charset=utf-8",
        "cache-control": ttl > 0 ? `public, max-age=${ttl}` : "no-store",
        "x-cache": "MISS",
      },
    });
    if (ttl > 0) ctx.waitUntil(cache.put(key, out.clone()));
    return out;
  },
};

// ── نصب سریع با CLI (جایگزین روش بالا) ─────────────────────────────
//   npm create cloudflare@latest divar-relay
//   cd divar-relay && npx wrangler deploy
//   (کد بالا را در src/index.js بگذار)
