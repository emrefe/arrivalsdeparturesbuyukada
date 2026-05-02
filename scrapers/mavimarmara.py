"""
Mavi Marmara (mavimarmara.net) için scraper.

Site WordPress tabanlı olduğu için her rotanın kendi statik HTML sayfası var:
  https://mavimarmara.net/tarifeler/bostanci-buyukada/
  https://mavimarmara.net/tarifeler/buyukada-bostanci/  (varsa)
  vs.

Strateji: önce /tarifeler/ ana sayfasındaki linkleri topla, sonra her birine
tek tek girip tabloları parse et.
"""
from __future__ import annotations
from typing import List
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import sys
import traceback

from common import Sefer, fetch, normalize_iskele, parse_saatler, direkt_mi

OPERATOR = "Mavi Marmara"
OPERATOR_KOD = "MM"
BASE_URL = "https://mavimarmara.net"
TARIFELER_URL = f"{BASE_URL}/tarifeler/"

# Her sayfanın URL slug'ından kalkış-varış çıkarmak için harita
# slug -> (kalkış, varış)
SLUG_HARITA = {
    "bostanci-buyukada": ("Bostancı", "Büyükada"),
    "buyukada-bostanci": ("Büyükada", "Bostancı"),
    "bostanci-heybeliada-buyukada": ("Bostancı", "Büyükada"),
    "kabatas-buyukada": ("Kabataş", "Büyükada"),
    "buyukada-kabatas": ("Büyükada", "Kabataş"),
    "besiktas-buyukada": ("Beşiktaş", "Büyükada"),
    "eminonu-buyukada": ("Eminönü", "Büyükada"),
}

FALLBACK_SEFERLER = [
    # Bostancı <-> Büyükada (direkt 35 dk veya Heybeli üzerinden 50 dk)
    ("07:00", "Bostancı",  ["Bostancı","Büyükada"], "Büyükada", 35),
    ("08:00", "Bostancı",  ["Bostancı","Heybeliada","Büyükada"], "Büyükada", 50),
    ("10:00", "Bostancı",  ["Bostancı","Büyükada"], "Büyükada", 35),
    ("12:30", "Bostancı",  ["Bostancı","Büyükada"], "Büyükada", 35),
    ("14:30", "Bostancı",  ["Bostancı","Heybeliada","Büyükada"], "Büyükada", 50),
    ("16:00", "Bostancı",  ["Bostancı","Büyükada"], "Büyükada", 35),
    ("18:00", "Bostancı",  ["Bostancı","Büyükada"], "Büyükada", 35),
    ("20:00", "Bostancı",  ["Bostancı","Büyükada"], "Büyükada", 35),
    # Geri dönüş
    ("07:00", "Büyükada", ["Büyükada","Bostancı"], "Bostancı", 35),
    ("08:30", "Büyükada", ["Büyükada","Heybeliada","Bostancı"], "Bostancı", 50),
    ("10:00", "Büyükada", ["Büyükada","Bostancı"], "Bostancı", 35),
    ("12:00", "Büyükada", ["Büyükada","Bostancı"], "Bostancı", 35),
    ("14:30", "Büyükada", ["Büyükada","Heybeliada","Bostancı"], "Bostancı", 50),
    ("16:00", "Büyükada", ["Büyükada","Bostancı"], "Bostancı", 35),
    ("17:30", "Büyükada", ["Büyükada","Bostancı"], "Bostancı", 35),
    ("19:00", "Büyükada", ["Büyükada","Bostancı"], "Bostancı", 35),
]


def _fallback_seferler() -> List[Sefer]:
    out = []
    for saat, kalk, rota, varis, sure in FALLBACK_SEFERLER:
        rota_norm = [normalize_iskele(x) for x in rota]
        yon = "buyukadadan" if rota_norm[0] == "Büyükada" else "buyukadaya"
        out.append(Sefer(
            kalkis_saati=saat,
            operator=OPERATOR,
            operator_kod=OPERATOR_KOD,
            kalkis_iskelesi=normalize_iskele(kalk),
            varis_iskelesi=normalize_iskele(varis),
            yon=yon,
            rota=rota_norm,
            direkt=direkt_mi(rota_norm),
            tahmini_sure_dk=sure,
            notlar="fallback",
        ))
    return out


def _rota_sayfalarini_bul() -> List[str]:
    """Tarifeler ana sayfasından alt sayfaların URL'lerini topla."""
    try:
        html = fetch(TARIFELER_URL)
        soup = BeautifulSoup(html, "html.parser")
        urls = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/tarifeler/" in href and href.rstrip("/") != TARIFELER_URL.rstrip("/"):
                full = urljoin(BASE_URL, href)
                # Sadece adalarla ilgili olanları al
                low = full.lower()
                if any(k in low for k in ["buyukada", "büyükada", "heybel", "burgaz", "kinali", "kınalı", "ada"]):
                    urls.add(full)
        return sorted(urls)
    except Exception as e:
        print(f"[MM] Tarifeler sayfası okunamadı: {e}", file=sys.stderr)
        return []


def _sayfayi_parse_et(url: str) -> List[Sefer]:
    """Tek bir rota sayfasından sefer saatlerini çıkar."""
    out: List[Sefer] = []
    try:
        html = fetch(url)
        soup = BeautifulSoup(html, "html.parser")

        # Slug'dan kalkış/varış çıkarmaya çalış
        slug = url.rstrip("/").split("/")[-1].lower()
        kalk, varis = SLUG_HARITA.get(slug, (None, None))
        if not kalk or not varis:
            # Slug'da iki şehir adı bulmaya çalış
            print(f"[MM] Slug'tan kalkış/varış çıkarılamadı: {slug}", file=sys.stderr)
            return out

        # Ana içerik bölgesini al
        icerik = soup.find("article") or soup.find("main") or soup
        metin = icerik.get_text(" ", strip=True)

        # Saatleri çıkar
        saatler = parse_saatler(metin)
        if not saatler:
            return out

        # Rota: şu an basit — sadece kalkış→varış. Heybeli durağı vs. detayını
        # gerçek HTML'i görünce iyileştirmek lazım.
        rota = [kalk, varis]

        for saat in sorted(set(saatler)):
            yon = "buyukadadan" if normalize_iskele(kalk) == "Büyükada" else "buyukadaya"
            out.append(Sefer(
                kalkis_saati=saat,
                operator=OPERATOR,
                operator_kod=OPERATOR_KOD,
                kalkis_iskelesi=normalize_iskele(kalk),
                varis_iskelesi=normalize_iskele(varis),
                yon=yon,
                rota=[normalize_iskele(x) for x in rota],
                direkt=True,
                tahmini_sure_dk=35,
                notlar=f"kaynak: {url}",
            ))
    except Exception as e:
        print(f"[MM] Sayfa parse hatası {url}: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
    return out


def _scrape_canli() -> List[Sefer]:
    seferler: List[Sefer] = []
    sayfalar = _rota_sayfalarini_bul()
    print(f"[MM] {len(sayfalar)} rota sayfası bulundu", file=sys.stderr)
    for url in sayfalar:
        seferler.extend(_sayfayi_parse_et(url))
    return seferler


def scrape() -> List[Sefer]:
    seferler = _scrape_canli()
    if seferler:
        print(f"[MM] Canlı scrape başarılı: {len(seferler)} sefer", file=sys.stderr)
        return seferler
    print("[MM] Canlı scrape veri vermedi, fallback kullanılıyor", file=sys.stderr)
    return _fallback_seferler()


if __name__ == "__main__":
    import json
    seferler = scrape()
    print(json.dumps([s.as_dict() for s in seferler], ensure_ascii=False, indent=2))
