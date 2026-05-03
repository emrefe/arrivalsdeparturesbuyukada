"""
Mavi Marmara (mavimarmara.net) — 2026 BAHAR TARİFESİ.
 
Sayfalar Cloudflare bot koruması arkasında olduğu için doğrudan scrape
edilemiyor; tarife resmi/ekran görüntüsünden okunup elden derlendi.
 
Şu an sadece Bostancı-Büyükada hattı var. MM'in diğer hatları (Kabataş,
Beşiktaş, Eminönü) için tarife tablosu paylaşıldıkça eklenecek.
"""
from __future__ import annotations
import sys
import datetime as dt
from typing import List
 
from common import Sefer
 
OPERATOR = "Mavi Marmara"
OPERATOR_KOD = "MM"
BASE_URL = "https://mavimarmara.net"
 
# 2026 BAHAR TARİFESİ — HER GÜN — Bostancı ↔ Büyükada
# rota_tipi: "direkt" = Bostancı-Büyükada (uğraksız ~35 dk)
#            "ugrakli" = Bostancı-Heybeliada-Büyükada (~50 dk)
# (saat, rota_tipi, sadece_hafta_ici)
 
# Bostancı kalkışlı (Büyükada'ya geliş)
BOSTANCI_KALKIS = [
    ("07:10", "ugrakli", True),   # *
    ("08:00", "ugrakli", False),
    ("09:00", "direkt",  False),
    ("10:30", "direkt",  False),
    ("11:30", "ugrakli", False),
    ("12:30", "direkt",  False),
    ("13:30", "direkt",  False),
    ("14:45", "direkt",  False),
    ("15:30", "ugrakli", False),
    ("16:20", "direkt",  False),
    ("17:30", "ugrakli", False),
    ("18:20", "direkt",  False),
    ("19:30", "direkt",  False),
    ("21:00", "ugrakli", False),
    ("22:00", "direkt",  False),
    ("23:00", "ugrakli", False),
]
 
# Büyükada kalkışlı (Bostancı'ya gidiş)
BUYUKADA_KALKIS = [
    ("06:20", "ugrakli", False),
    ("07:25", "direkt",  True),   # *
    ("08:00", "direkt",  False),
    ("08:50", "direkt",  False),
    ("09:35", "ugrakli", False),
    ("11:05", "ugrakli", False),
    ("12:20", "direkt",  False),
    ("13:05", "ugrakli", False),
    ("14:05", "ugrakli", False),
    ("15:20", "ugrakli", False),
    ("16:20", "direkt",  False),
    ("17:25", "direkt",  False),
    ("18:20", "direkt",  False),
    ("19:20", "direkt",  False),
    ("20:35", "direkt",  False),
    ("21:50", "direkt",  False),
]
 
 
def _make(saat, kalkis, varis, yon, tip, hafta_ici_only):
    if tip == "direkt":
        rota = [kalkis, varis]
        sure = 35
        direkt = True
    else:
        ara = "Heybeliada"
        rota = [kalkis, ara, varis] if kalkis != ara and varis != ara else [kalkis, varis]
        sure = 50
        direkt = (len(rota) == 2)
    return Sefer(
        kalkis_saati=saat,
        operator=OPERATOR,
        operator_kod=OPERATOR_KOD,
        kalkis_iskelesi=kalkis,
        varis_iskelesi=varis,
        yon=yon,
        rota=rota,
        direkt=direkt,
        tahmini_sure_dk=sure,
        notlar=("sadece hafta içi" if hafta_ici_only else None),
    )
 
 
def scrape() -> List[Sefer]:
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=3)))
    hafta_sonu = now.weekday() >= 5
 
    seferler: List[Sefer] = []
    for saat, tip, hi in BOSTANCI_KALKIS:
        if hi and hafta_sonu:
            continue
        seferler.append(_make(saat, "Bostancı", "Büyükada", "buyukadaya", tip, hi))
    for saat, tip, hi in BUYUKADA_KALKIS:
        if hi and hafta_sonu:
            continue
        seferler.append(_make(saat, "Büyükada", "Bostancı", "buyukadadan", tip, hi))
 
    print(f"[MM] {len(seferler)} sefer (hafta_sonu={hafta_sonu})", file=sys.stderr)
    return seferler
 
 
if __name__ == "__main__":
    import json
    seferler = scrape()
    print(json.dumps([s.as_dict() for s in seferler], ensure_ascii=False, indent=2))
