"""
Playwright ile siteleri ziyaret et, JS çalıştıktan sonraki HTML'i kaydet.
v2: Türkçe Cloudflare metnini algıla, domain başına root'a önce gir, daha uzun bekle.
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

# Her domain için: önce root'u ziyaret et (CF cookies için), sonra subpage'leri
GROUPS = {
    "sehirhatlari.istanbul": [
        ("sh_root",     "https://sehirhatlari.istanbul/"),
        ("sh_seferler", "https://sehirhatlari.istanbul/tr/seferler"),
        ("sh_adalar",   "https://sehirhatlari.istanbul/tr/seferler/ic-hatlar/adalar-hatlari-176"),
    ],
    "mavimarmara.net": [
        ("mm_root",                "https://mavimarmara.net/"),
        ("mm_tarifeler",           "https://mavimarmara.net/tarifeler/"),
        ("mm_bostanci_buyukada",   "https://mavimarmara.net/tarifeler/bostanci-buyukada/"),
        ("mm_kabatas_buyukada",    "https://mavimarmara.net/tarifeler/kabatas-buyukada/"),
    ],
    "prenstur.net": [
        ("pt_root",  "https://www.prenstur.net/"),
        ("pt_index", "https://www.prenstur.net/index3e95.html"),
    ],
}

# Resim URL'leri (ayrı indirilecek)
IMAGES = [
    ("pt_tarife", "https://www.prenstur.net/Tarife-2025-2026.jpg"),
]

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

CF_INDICATORS = ["just a moment", "bir dakika lütfen", "checking your browser", "challenge"]


def is_cloudflare_challenge(title: str, html: str) -> bool:
    t = title.lower()
    if any(s in t for s in CF_INDICATORS):
        return True
    # Cloudflare challenge sayfası belirteçleri
    if "cf-challenge" in html.lower() or "challenge-platform" in html.lower():
        # Ama gerçek içerik de varsa (büyük HTML), challenge geçmiş olabilir
        if len(html) < 60000:
            return True
    return False


async def wait_through_cloudflare(page, max_seconds=40):
    """Sayfa içeriğine bakarak CF challenge geçinceye kadar bekle."""
    for i in range(max_seconds // 2):
        title = await page.title()
        try:
            html = await page.content()
        except Exception:
            html = ""
        if not is_cloudflare_challenge(title, html):
            return title
        print(f"    [{i*2}s] CF bekleniyor... title={title!r}")
        await page.wait_for_timeout(2000)
    return await page.title()


async def main():
    out = Path("recon")
    out.mkdir(exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ],
        )

        for domain, urls in GROUPS.items():
            print(f"\n========== {domain} ==========", flush=True)
            context = await browser.new_context(
                user_agent=UA,
                locale="tr-TR",
                timezone_id="Europe/Istanbul",
                viewport={"width": 1366, "height": 768},
                extra_http_headers={
                    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
            )
            await context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
                "Object.defineProperty(navigator, 'languages', {get: () => ['tr-TR','tr','en-US','en']});"
                "Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});"
            )
            page = await context.new_page()

            for name, url in urls:
                print(f"\n--- {name}: {url} ---", flush=True)
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    title = await wait_through_cloudflare(page, max_seconds=40)
                    try:
                        await page.wait_for_load_state("networkidle", timeout=8000)
                    except Exception:
                        pass
                    await page.wait_for_timeout(1500)

                    title = await page.title()
                    html = await page.content()
                    (out / f"{name}.html").write_text(html, encoding="utf-8")
                    cf = is_cloudflare_challenge(title, html)
                    print(f"  ✓ size={len(html)}b  title={title!r}  CF_blocked={cf}")
                    await page.screenshot(path=str(out / f"{name}.png"), full_page=True)
                except Exception as e:
                    print(f"  ✗ HATA: {e}")

            await context.close()

        # Resimler — ayrı bir context'te
        print("\n========== resimler ==========", flush=True)
        ctx = await browser.new_context(user_agent=UA)
        for name, url in IMAGES:
            try:
                resp = await ctx.request.get(url, timeout=30000)
                if resp.ok:
                    body = await resp.body()
                    ext = url.rsplit(".", 1)[-1].lower()
                    (out / f"{name}.{ext}").write_bytes(body)
                    print(f"  ✓ {name}.{ext}: {len(body)}b")
                else:
                    print(f"  ✗ {name}: HTTP {resp.status}")
            except Exception as e:
                print(f"  ✗ {name}: {e}")
        await ctx.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
