"""
Mavi Marmara (mavimarmara.net) — 2026 YAZ TARİFESİ.

Sayfalar Cloudflare bot koruması arkasında olduğu için otomatik scrape
zor; tarife HTML tablosundan elden derlendi. Kaynaklar:
  https://mavimarmara.net/tarifeler/buyukada-bostanci/
  https://mavimarmara.net/tarifeler/bostanci-buyukada/

Notlar:
* 07:25 Büyükada → Bostancı: PAZAR/RESMİ TATİL YAPILMAZ.
** 01:00 Büyükada → Bostancı: CUMARTESİYİ PAZARA BAĞLAYAN GECE
   (yani Pazar günü sabahının 01:00 seferi).
"""
from __future__ import annotations
import sys
import datetime as dt
from typing import List, Optional

from common import Sefer

OPERATOR = "Mavi Marmara"
OPERATOR_KOD = "MM"
BASE_URL = "https://mavimarmara.net"

# --- Yaz 2026 tarifesi ---
# tip: "direkt"   (~35 dk, direkt Bostancı/Büyükada)
#      "ugrakli"  (~50 dk, Heybeliada üzerinden)
# gunler_flag:
#   None            = HER GÜN
#   "pazar_haric"   = Pazar/resmi tatil YAPILMAZ  (site notasyonu: *)
#   "pazar_gecesi"  = Sadece Pazar sabahının 01:00 seferi (site notasyonu: **)

# Bostancı kalkışlı → Büyükada'ya geliş
# "BÜYÜKADA - HEYBELİADA" güzergahı Büyükada için DİREKT (önce Büyükada)
# "HEYBELİADA - BÜYÜKADA" güzergahı Büyükada için UĞRAKLI (önce Heybeliada)
BOSTANCI_KALKIS = [
    ("07:10", "ugrakli", None),
    ("08:00", "ugrakli", None),
    ("09:00", "direkt",  None),
    ("09:50", "direkt",  None),
    ("10:45", "direkt",  None),
    ("11:45", "ugrakli", None),
    ("12:40", "direkt",  None),
    ("13:30", "direkt",  None),
    ("14:30", "ugrakli", None),
    ("15:15", "ugrakli", None),
    ("15:50", "ugrakli", None),
    ("16:35", "ugrakli", None),
    ("17:15", "ugrakli", None),
    ("17:45", "direkt",  None),
    ("18:20", "direkt",  None),
    ("19:00", "ugrakli", None),
    ("19:30", "direkt",  None),
    ("20:15", "ugrakli", None),
    ("21:00", "ugrakli", None),
    ("22:00", "ugrakli", None),
    ("23:00", "ugrakli", None),
    ("23:45", "direkt",  None),
]

# Büyükada kalkışlı → Bostancı'ya gidiş
BUYUKADA_KALKIS = [
    ("06:25", "ugrakli", None),
    ("07:25", "direkt",  "pazar_haric"),   # *
    ("08:00", "direkt",  None),
    ("08:50", "direkt",  None),
    ("09:35", "ugrakli", None),
    ("10:25", "ugrakli", None),
    ("11:20", "ugrakli", None),
    ("12:35", "direkt",  None),
    ("13:15", "ugrakli", None),
    ("14:05", "ugrakli", None),
    ("15:20", "direkt",  None),
    ("16:05", "direkt",  None),
    ("16:40", "direkt",  None),
    ("17:25", "direkt",  None),
    ("18:05", "direkt",  None),
    ("18:20", "ugrakli", None),
    ("18:55", "ugrakli", None),
    ("19:50", "direkt",  None),
    ("20:35", "direkt",  None),
    ("21:05", "direkt",  None),
    ("21:50", "direkt",  None),
    ("22:50", "direkt",  None),
    ("01:00", "direkt",  "pazar_gecesi"),  # ** (Pazar 01:00)
]


def _make(saat, kalkis, varis, yon, tip, gunler_flag: Optional[str]) -> Sefer:
    if tip == "direkt":
        rota = [kalkis, varis]
        sure = 35
        direkt = True
    else:
        ara = "Heybeliada"
        rota = [kalkis, ara, varis] if kalkis != ara and varis != ara else [kalkis, varis]
        sure = 50
        direkt = (len(rota) == 2)

    notlar_map = {
        "pazar_haric":  "pazar/resmi tatil yok",
        "pazar_gecesi": "sadece pazar gecesi (cumartesiyi pazara bağlayan)",
    }
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
        notlar=notlar_map.get(gunler_flag),
    )


def _dahil_mi(gunler_flag: Optional[str], weekday: int) -> bool:
    """Bugünün haftagünü (0=Pzt..6=Paz) verildiğinde bu sefer bugün var mı?"""
    if gunler_flag is None:
        return True
    if gunler_flag == "pazar_haric":
        # Pazar (6) yok. Resmi tatil kontrolü şu an eklenmemiş.
        return weekday != 6
    if gunler_flag == "pazar_gecesi":
        # 01:00 seferi teknik olarak Pazar günü.
        return weekday == 6
    return True


def scrape() -> List[Sefer]:
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=3)))
    weekday = now.weekday()

    seferler: List[Sefer] = []
    for saat, tip, gf in BOSTANCI_KALKIS:
        if not _dahil_mi(gf, weekday):
            continue
        seferler.append(_make(saat, "Bostancı", "Büyükada", "buyukadaya", tip, gf))
    for saat, tip, gf in BUYUKADA_KALKIS:
        if not _dahil_mi(gf, weekday):
            continue
        seferler.append(_make(saat, "Büyükada", "Bostancı", "buyukadadan", tip, gf))

    print(f"[MM] {len(seferler)} sefer (weekday={weekday}, tarife=2026 YAZ)", file=sys.stderr)
    return seferler


if __name__ == "__main__":
    import json
    seferler = scrape()
    print(json.dumps([s.as_dict() for s in seferler], ensure_ascii=False, indent=2))
