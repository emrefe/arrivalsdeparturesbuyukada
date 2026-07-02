"""
Prens Tur (prenstur.net) — 2026 YAZ TARİFESİ.

Saatler https://www.prenstur.net/ adlı sitede tablo halinde yayınlanıyor
(sefer saatleri sayfası). Aşağıdaki tablo doğrudan siteden okundu.
Tarife değişikliği: `scripts/check_source_hashes.py` haftalık kontrol eder ve
farklılık olursa Issue açar.
"""
from __future__ import annotations
import sys
import hashlib
import datetime as dt
from typing import List
import requests

from common import Sefer

OPERATOR = "Prens Tur"
OPERATOR_KOD = "PT"
TARIFE_IMG_URL = "https://www.prenstur.net/Tarife-2025-2026.jpg"

# 2026 YAZ TARİFESİ — Prens Tur "Sefer Saatleri" sayfasından okundu.
# (saat, sadece_hafta_ici)  — yıldızlı (*) seferler hafta sonu/tatil yok

# Sol tablo: KARTAL'dan kalkış (rota: Kartal → Büyükada → Heybeliada, ~25 dk Büyükada'ya)
KARTAL_BUYUKADA = [
    ("06:20", True),   # *
    ("07:15", False),
    ("08:00", False),
    ("08:30", False),
    ("09:00", False),
    ("09:30", False),
    ("10:00", False),
    ("10:30", False),
    ("11:00", False),
    ("11:30", False),
    ("12:00", False),
    ("12:30", False),
    ("13:00", False),
    ("13:30", False),
    ("14:00", False),
    ("14:30", False),
    ("15:00", False),
    ("15:30", False),
    ("16:00", False),
    ("16:30", False),
    ("17:00", False),
    ("17:30", False),
    ("18:00", False),
    ("18:30", False),
    ("19:00", False),
    ("19:45", False),
    ("20:30", False),
    ("21:30", False),
]

# Sağ tablo: ADALAR'dan kalkış (rota: Heybeliada → Büyükada → Kartal)
# Büyükada'dan binme zamanı, sonra ~25 dk sonra Kartal'a varış
BUYUKADA_KARTAL = [
    ("07:15", True),   # *
    ("08:15", False),
    ("08:50", False),
    ("09:30", False),
    ("10:00", False),
    ("10:30", False),
    ("11:00", False),
    ("11:30", False),
    ("12:00", False),
    ("12:30", False),
    ("13:00", False),
    ("13:30", False),
    ("14:00", False),
    ("14:30", False),
    ("15:00", False),
    ("15:30", False),
    ("16:00", False),
    ("16:30", False),
    ("17:00", False),
    ("17:30", False),
    ("18:00", False),
    ("18:30", False),
    ("19:00", False),
    ("19:30", False),
    ("20:00", False),
    ("20:45", False),
    ("21:30", False),
    ("22:30", False),
]


def _resim_hash_kontrol():
    """Tarife resmini indir, hash'le. Değişirse log'a uyarı bas."""
    try:
        r = requests.get(TARIFE_IMG_URL, timeout=20, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        if r.ok:
            md5 = hashlib.md5(r.content).hexdigest()
            print(f"[PT] resim md5={md5} size={len(r.content)}b", file=sys.stderr)
        else:
            print(f"[PT] resim {r.status_code}", file=sys.stderr)
    except Exception as e:
        print(f"[PT] resim hash kontrolü başarısız: {e}", file=sys.stderr)


def scrape() -> List[Sefer]:
    _resim_hash_kontrol()

    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=3)))
    hafta_sonu = now.weekday() >= 5  # 5=Cmt, 6=Paz

    def make_sefer(saat: str, hafta_ici_only: bool, kalkis: str, varis: str, yon: str):
        if hafta_ici_only and hafta_sonu:
            return None
        return Sefer(
            kalkis_saati=saat,
            operator=OPERATOR,
            operator_kod=OPERATOR_KOD,
            kalkis_iskelesi=kalkis,
            varis_iskelesi=varis,
            yon=yon,
            rota=[kalkis, varis],
            direkt=True,
            tahmini_sure_dk=25,
            notlar=("sadece hafta içi" if hafta_ici_only else None),
        )

    seferler: List[Sefer] = []

    for saat, hi in KARTAL_BUYUKADA:
        s = make_sefer(saat, hi, "Kartal", "Büyükada", "buyukadaya")
        if s:
            seferler.append(s)

    for saat, hi in BUYUKADA_KARTAL:
        s = make_sefer(saat, hi, "Büyükada", "Kartal", "buyukadadan")
        if s:
            seferler.append(s)

    print(f"[PT] {len(seferler)} sefer (hafta_sonu={hafta_sonu})", file=sys.stderr)
    return seferler


if __name__ == "__main__":
    import json
    seferler = scrape()
    print(json.dumps([s.as_dict() for s in seferler], ensure_ascii=False, indent=2))
