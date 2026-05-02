"""
Prens Tur (prenstur.net) için scraper.

Site eski Joomla stili, statik HTML. Saatler genelde tablo veya basit liste şeklinde.
Hangi rotaların hangi sayfada olduğunu gözlemleyip rafine etmek lazım.

Bilinen URL: https://www.prenstur.net/index3e95.html  (Kartal-Adalar tarifesi)
"""
from __future__ import annotations
from typing import List
from bs4 import BeautifulSoup
import sys
import traceback

from common import Sefer, fetch, normalize_iskele, parse_saatler, direkt_mi

OPERATOR = "Prens Tur"
OPERATOR_KOD = "PT"

URLS = [
    "https://www.prenstur.net/index3e95.html",
    "https://www.prenstur.net/",  # ana sayfa, belki başka link var
]

FALLBACK_SEFERLER = [
    # Kartal -> Büyükada (direkt 25 dk veya Heybeli üzerinden 40 dk)
    ("07:15", "Kartal",   ["Kartal","Heybeliada","Büyükada"], "Büyükada", 40),
    ("09:00", "Kartal",   ["Kartal","Büyükada"], "Büyükada", 25),
    ("11:00", "Kartal",   ["Kartal","Heybeliada","Büyükada"], "Büyükada", 40),
    ("13:30", "Kartal",   ["Kartal","Büyükada"], "Büyükada", 25),
    ("15:30", "Kartal",   ["Kartal","Heybeliada","Büyükada"], "Büyükada", 40),
    ("17:00", "Kartal",   ["Kartal","Büyükada"], "Büyükada", 25),
    ("19:00", "Kartal",   ["Kartal","Heybeliada","Büyükada"], "Büyükada", 40),
    # Büyükada -> Kartal
    ("07:30", "Büyükada", ["Büyükada","Kartal"], "Kartal", 25),
    ("09:30", "Büyükada", ["Büyükada","Heybeliada","Kartal"], "Kartal", 40),
    ("13:00", "Büyükada", ["Büyükada","Kartal"], "Kartal", 25),
    ("15:30", "Büyükada", ["Büyükada","Heybeliada","Kartal"], "Kartal", 40),
    ("17:00", "Büyükada", ["Büyükada","Kartal"], "Kartal", 25),
    ("18:30", "Büyükada", ["Büyükada","Heybeliada","Kartal"], "Kartal", 40),
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


def _scrape_canli() -> List[Sefer]:
    seferler: List[Sefer] = []
    for url in URLS:
        try:
            html = fetch(url)
            soup = BeautifulSoup(html, "html.parser")
            metin = soup.get_text(" ", strip=True).lower()
            if "kartal" not in metin and "büyükada" not in metin and "buyukada" not in metin:
                continue

            # TODO: gerçek tablo parse'ı buraya gelecek.
            # Bu site eski/dağınık olduğu için saatleri tablo bağlamından
            # çıkarmak komplike. Şu an placeholder.
        except Exception as e:
            print(f"[PT] Hata {url}: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
    return seferler


def scrape() -> List[Sefer]:
    seferler = _scrape_canli()
    if seferler:
        print(f"[PT] Canlı scrape başarılı: {len(seferler)} sefer", file=sys.stderr)
        return seferler
    print("[PT] Canlı scrape veri vermedi, fallback kullanılıyor", file=sys.stderr)
    return _fallback_seferler()


if __name__ == "__main__":
    import json
    seferler = scrape()
    print(json.dumps([s.as_dict() for s in seferler], ensure_ascii=False, indent=2))
