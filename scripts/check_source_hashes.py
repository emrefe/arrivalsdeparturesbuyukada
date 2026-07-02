"""
Kaynak sayfaların hash'ini kontrol eder — MM/PT/SH sitelerindeki tarife tablosu
değişince farklılık bulur. Değişiklik varsa GitHub Issue açar (workflow üzerinden).

Nasıl çalışır:
  1. Her kaynak URL'ini indirir (Playwright ile Cloudflare bypass).
  2. Sayfanın "tarife tablosu" kısmının SHA-256 hash'ini alır.
  3. `state/source_hashes.json` içindeki önceki hash'lerle karşılaştırır.
  4. Fark varsa → stdout'a JSON diff bas + exit 1 (workflow issue açar).
  5. Yoksa → state'i güncelle + exit 0.

Playwright yoksa requests-html fallback'i.
"""
from __future__ import annotations
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Optional, Dict, Any

ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = ROOT / "state" / "source_hashes.json"

# İzlenen kaynaklar — (isim, URL, sadece_bu_regex_alan)
# sadece_bu_regex_alan: None ise tüm sayfa; regex ise sadece o kısmın hash'i
# Amaç: navbar/footer değişikliklerinden etkilenmemek, sadece tarife tablosunu izlemek.
SOURCES = [
    {
        "name": "mm_buyukada_bostanci",
        "url": "https://mavimarmara.net/tarifeler/buyukada-bostanci/",
        "extract": r"Büyükada.*?Bostancı.*?Tarifesi(.*?)(?=SİTE MENÜ|©)",
    },
    {
        "name": "mm_bostanci_buyukada",
        "url": "https://mavimarmara.net/tarifeler/bostanci-buyukada/",
        "extract": r"Bostancı.*?Büyükada.*?Tarifesi(.*?)(?=SİTE MENÜ|©)",
    },
    {
        "name": "prenstur_saatler",
        "url": "https://www.prenstur.net/index3e95.html?option=com_content&view=article&id=75&Itemid=477",
        "extract": r"KARTAL[’']dan Kalkış(.*?)(?=Tüm Hakkı|Copyright)",
    },
    {
        "name": "sehirhatlari_tarife_pdf",
        "url": "https://files.sehirhatlari.istanbul/tarife.pdf",
        "extract": None,  # PDF binary hash'i
    },
]


def fetch(url: str) -> Optional[bytes]:
    """Sayfayı indir. Cloudflare arkasında ise Playwright kullan."""
    import requests
    try:
        r = requests.get(url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        })
        if r.ok:
            return r.content
    except Exception as e:
        print(f"[!] requests fail for {url}: {e}", file=sys.stderr)

    # Playwright fallback
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")
            page = ctx.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)
            content = page.content().encode("utf-8")
            browser.close()
            return content
    except Exception as e:
        print(f"[!] playwright fail for {url}: {e}", file=sys.stderr)
        return None


def extract_relevant(content: bytes, regex: Optional[str]) -> bytes:
    if regex is None:
        return content
    text = content.decode("utf-8", errors="ignore")
    # HTML tag'lerini strip et — sadece text kısmına odaklan
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    m = re.search(regex, text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).encode("utf-8")
    return text.encode("utf-8")


def hash_content(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def load_state() -> Dict[str, Any]:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: Dict[str, Any]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def main() -> int:
    state = load_state()
    changes = []

    for src in SOURCES:
        name = src["name"]
        url = src["url"]
        print(f"[.] {name} — fetching...", file=sys.stderr)
        content = fetch(url)
        if content is None:
            print(f"[X] {name}: fetch failed, skipping", file=sys.stderr)
            continue
        relevant = extract_relevant(content, src.get("extract"))
        current_hash = hash_content(relevant)
        prev = state.get(name, {}).get("hash")

        if prev is None:
            print(f"[+] {name}: yeni kaynak, hash saklandı ({current_hash[:12]}...)", file=sys.stderr)
        elif prev != current_hash:
            print(f"[!] {name}: DEĞİŞİKLİK ({prev[:12]}... → {current_hash[:12]}...)", file=sys.stderr)
            changes.append({
                "name": name,
                "url": url,
                "prev_hash": prev,
                "new_hash": current_hash,
            })
        else:
            print(f"[✓] {name}: aynı", file=sys.stderr)

        state[name] = {
            "hash": current_hash,
            "url": url,
            "last_checked": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        }

    save_state(state)

    if changes:
        # GitHub Actions için: değişiklikleri JSON olarak bas
        print(json.dumps({"changes": changes}, ensure_ascii=False, indent=2))
        return 1  # workflow bu return kodunu görüp Issue açacak
    return 0


if __name__ == "__main__":
    sys.exit(main())
