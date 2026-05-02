"""
Playwright ile siteleri ziyaret et, JS çalıştıktan sonraki HTML'i kaydet.
Cloudflare challenge geçilmiş hâlini almak için.
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

URLS = [
    ("sh_root",                  "https://sehirhatlari.istanbul/"),
    ("sh_adalar",                "https://sehirhatlari.istanbul/tr/seferler/ic-hatlar/adalar-hatlari-176"),
    ("sh_seferler",              "https://sehirhatlari.istanbul/tr/seferler"),
    ("mm_root",                  "https://mavimarmara.net/"),
    ("mm_tarifeler",             "https://mavimarmara.net/tarifeler/"),
    ("mm_bostanci_buyukada",     "https://mavimarmara.net/tarifeler/bostanci-buyukada/"),
    ("mm_kabatas_buyukada",      "https://mavimarmara.net/tarifeler/kabatas-buyukada/"),
    ("pt_root",                  "https://www.prenstur.net/"),
    ("pt_index",                 "https://www.prenstur.net/index3e95.html"),
    ("pt_tarife_resmi",          "https://www.prenstur.net/Tarife-2025-2026.jpg"),
]

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


async def main():
    out = Path("recon")
    out.mkdir(exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            user_agent=UA,
            locale="tr-TR",
            timezone_id="Europe/Istanbul",
            viewport={"width": 1366, "height": 768},
        )
        # webdriver tespitini gizle
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page = await context.new_page()

        for name, url in URLS:
            print(f"\n--- {name}: {url} ---", flush=True)

            # Resim ise direkt indir
            if url.lower().endswith((".jpg", ".jpeg", ".png")):
                try:
                    resp = await context.request.get(url)
                    if resp.ok:
                        ext = url.rsplit(".", 1)[-1].lower()
                        body = await resp.body()
                        (out / f"{name}.{ext}").write_bytes(body)
                        print(f"  ✓ resim kaydedildi: {len(body)} bytes")
                    else:
                        print(f"  ✗ resim alınamadı: HTTP {resp.status}")
                except Exception as e:
                    print(f"  ✗ resim hatası: {e}")
                continue

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                # Cloudflare challenge'ın geçmesi için bekle
                for _ in range(8):
                    title = await page.title()
                    if "moment" not in title.lower() and "just a" not in title.lower():
                        break
                    print(f"  bekleniyor... title: {title}")
                    await page.wait_for_timeout(2000)

                # Network'un sakinleşmesini bekle
                try:
                    await page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass
                await page.wait_for_timeout(2000)

                title = await page.title()
                html = await page.content()
                (out / f"{name}.html").write_text(html, encoding="utf-8")
                print(f"  ✓ kaydedildi  title='{title}'  size={len(html)}")

                # Ekran görüntüsü
                await page.screenshot(path=str(out / f"{name}.png"), full_page=True)
            except Exception as e:
                print(f"  ✗ HATA: {e}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
