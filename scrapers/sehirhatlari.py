"""
Şehir Hatları (sehirhatlari.istanbul) — KIŞ TARİFESİ 8 Eylül 2025 - 28 Haziran 2026.
 
Site Cloudflare bot koruması arkasında olduğu için doğrudan scrape edilemiyor;
veriler resmi PDF tarifeden okunup elde derlendi:
  https://sehirhatlari.istanbul/Documents/...
 
Üç gün tipi var:
  - Hafta içi & Cumartesi (HİC): Pazartesi-Cumartesi
  - Pazar & Resmi Tatil (PZR): Pazar günü ve resmi tatiller (resmi tatil
    desteği şimdilik yok, sadece haftanın günü kullanılıyor)
  - Maltepe hattındaki bazı seferler "Pazar günleri yapılmaz" notu ile
    işaretli (PDF'te kırmızı*).
 
Hatlar:
  1. Kabataş - Adalar
  2. Adalar - Beşiktaş
  3. Maltepe - Büyükada - Heybeliada - Burgazada - Kınalıada
  4. Bostancı - Adalar Ring
  5. Büyükada - Sedef Adası
  6. Tuzla - Pendik - Büyükada (sadece Cmt/Paz/Tatil)
"""
from __future__ import annotations
import sys
import datetime as dt
from typing import List, Tuple, Optional
 
from common import Sefer
 
OPERATOR = "Şehir Hatları"
OPERATOR_KOD = "SH"
 
# ============================================================================
# YARDIMCILAR
# ============================================================================
 
def _dk_farki(s1: str, s2: str) -> int:
    """HH:MM iki saat arası dakika farkı (gece geçişi destekler)."""
    h1, m1 = map(int, s1.split(":"))
    h2, m2 = map(int, s2.split(":"))
    fark = (h2 * 60 + m2) - (h1 * 60 + m1)
    if fark < 0:
        fark += 24 * 60
    return fark
 
 
def _process_table(iskeleler: List[str], satirlar: List[Tuple],
                   gun_notu: Optional[str] = None) -> List[Sefer]:
    """
    iskeleler: rota sırasında iskele isimleri (örn ["Kabataş","Eminönü","Kadıköy",...,"Bostancı"])
    satirlar: her satır bir sefer; her hücre saat str veya "-"
    gun_notu: "sadece hafta içi/cmt", "sadece pazar/tatil" gibi
 
    Her sefer için Büyükada içeriyorsa hem geliş hem gidiş kayıtları üretilir.
    """
    out: List[Sefer] = []
    if "Büyükada" not in iskeleler:
        return out
    bua_idx = iskeleler.index("Büyükada")
 
    for sefer in satirlar:
        if sefer[bua_idx] == "-":
            continue
        bua_saat = sefer[bua_idx]
 
        # ---- Büyükada'ya GELİŞ kaydı ----
        kalkis_idx = None
        for i in range(bua_idx):
            if sefer[i] != "-":
                kalkis_idx = i
                break
        if kalkis_idx is not None:
            kalkis_saati = sefer[kalkis_idx]
            rota = [iskeleler[i] for i in range(kalkis_idx, bua_idx + 1) if sefer[i] != "-"]
            sure = _dk_farki(kalkis_saati, bua_saat)
            out.append(Sefer(
                kalkis_saati=kalkis_saati,
                operator=OPERATOR,
                operator_kod=OPERATOR_KOD,
                kalkis_iskelesi=iskeleler[kalkis_idx],
                varis_iskelesi="Büyükada",
                yon="buyukadaya",
                rota=rota,
                direkt=(len(rota) == 2),
                tahmini_sure_dk=sure,
                notlar=gun_notu,
            ))
 
        # ---- Büyükada'dan GİDİŞ kaydı ----
        varis_idx = None
        for i in range(len(sefer) - 1, bua_idx, -1):
            if sefer[i] != "-":
                varis_idx = i
                break
        if varis_idx is not None:
            varis_saati = sefer[varis_idx]
            rota = [iskeleler[i] for i in range(bua_idx, varis_idx + 1) if sefer[i] != "-"]
            sure = _dk_farki(bua_saat, varis_saati)
            out.append(Sefer(
                kalkis_saati=bua_saat,
                operator=OPERATOR,
                operator_kod=OPERATOR_KOD,
                kalkis_iskelesi="Büyükada",
                varis_iskelesi=iskeleler[varis_idx],
                yon="buyukadadan",
                rota=rota,
                direkt=(len(rota) == 2),
                tahmini_sure_dk=sure,
                notlar=gun_notu,
            ))
    return out
 
 
# ============================================================================
# 1. KABATAŞ - ADALAR HATTI
# ============================================================================
KABATAS_USTE_ISK = ["Kabataş","Eminönü","Kadıköy","Kınalıada","Burgazada","Heybeliada","Büyükada","Bostancı"]
KABATAS_ALTA_ISK = ["Bostancı","Büyükada","Heybeliada","Burgazada","Kınalıada","Kadıköy","Eminönü","Kabataş"]
 
# Hafta içi ve Cumartesi (Kabataş kalkışlı)
KABATAS_HIC_UST = [
    ("06:45","-","07:10","07:45","08:00","08:15","08:30","09:05"),
    ("08:00","-","08:25","09:00","09:15","09:30","09:45","-"),
    ("09:00","-","09:25","10:00","10:15","10:30","10:45","-"),
    ("10:05","-","10:30","11:05","11:20","11:35","11:50","-"),
    ("11:05","-","11:30","12:05","12:20","12:35","12:50","13:25"),
    ("12:00","-","12:25","13:00","13:15","13:30","13:45","-"),
    ("14:00","-","14:25","15:00","15:15","15:30","15:45","-"),
    ("16:30","-","16:55","17:30","17:45","18:00","18:15","18:50"),
    ("17:35","-","18:00","18:35","18:50","19:05","19:20","-"),
    ("18:25","-","-","-","-","19:20","19:35","-"),
    ("18:50","19:05","19:25","20:00","20:15","20:30","20:45","-"),
    ("19:20","-","-","-","-","20:20","20:35","-"),
    ("19:40","-","20:05","20:40","20:55","21:10","21:25","-"),
    ("21:40","-","22:05","22:25","22:40","23:10","23:30","00:05"),
    ("23:30","-","23:55","00:30","00:45","01:00","01:15","-"),
]
 
# Hafta içi ve Cumartesi (Bostancı/Büyükada → Kabataş)
KABATAS_HIC_ALT = [
    ("-","05:45","06:00","06:15","06:30","07:05","07:30","07:45"),
    ("-","06:35","06:50","07:05","07:20","07:55","-","08:25"),
    ("07:05","07:40","07:55","08:10","08:25","09:00","-","09:30"),
    ("-","07:55","08:10","-","-","-","-","09:05"),
    ("-","09:00","09:15","09:30","09:45","10:20","-","10:50"),
    ("-","10:35","10:50","11:05","11:20","11:55","-","12:25"),
    ("-","12:05","12:20","12:35","12:50","13:25","-","13:55"),
    ("12:55","13:30","13:45","14:00","14:15","14:50","-","15:20"),
    ("-","15:00","15:15","15:30","15:45","16:20","-","16:50"),
    ("-","16:30","16:45","17:00","17:15","17:50","-","18:20"),
    ("-","17:35","17:50","18:05","18:20","18:55","-","19:25"),
    ("17:55","18:30","18:45","19:00","19:15","19:50","-","20:20"),
    ("-","19:35","19:50","20:05","20:20","20:55","-","21:25"),
    ("20:00","20:35","20:50","21:05","21:20","21:55","-","22:25"),
    ("-","21:45","22:00","22:15","22:30","23:05","-","23:35"),
]
 
# Pazar (Kabataş kalkışlı)
KABATAS_PZR_UST = [
    ("07:30","-","07:55","08:30","08:45","09:00","09:15","09:50"),
    ("08:30","-","08:55","09:30","09:45","10:00","10:15","-"),
    ("09:05","-","09:30","10:05","10:20","10:35","10:50","-"),
    ("10:05","-","10:30","11:05","11:20","11:35","11:50","-"),
    ("11:05","-","11:30","12:05","12:20","12:35","12:50","13:25"),
    ("12:05","-","12:30","13:05","13:20","13:35","13:50","-"),
    ("14:00","-","14:25","15:00","15:15","15:30","15:45","-"),
    ("16:30","-","16:55","17:30","17:45","18:00","18:15","18:50"),
    ("17:35","-","18:00","18:35","18:50","19:05","19:20","-"),
    ("18:25","-","-","-","-","19:20","19:35","-"),
    ("18:50","19:05","19:25","20:00","20:15","20:30","20:45","-"),
    ("19:20","-","-","-","-","20:20","20:35","-"),
    ("19:40","-","20:05","20:40","20:55","21:10","21:25","-"),
    ("21:40","-","22:05","22:25","22:40","23:10","23:30","00:05"),
    ("23:30","-","23:55","00:30","00:45","01:00","01:15","-"),
]
 
# Pazar (Bostancı/Büyükada → Kabataş)
KABATAS_PZR_ALT = [
    ("-","06:15","06:30","06:45","07:00","07:35","08:00","08:15"),
    ("-","07:00","07:15","07:30","07:45","08:20","-","08:50"),
    ("07:00","07:35","07:50","08:05","08:20","09:00","-","09:30"),
    ("-","08:15","08:30","-","-","-","-","09:25"),
    ("-","09:00","09:15","09:30","09:45","10:20","-","10:50"),
    ("-","11:00","11:15","11:30","11:45","12:20","-","12:50"),
    ("-","12:05","12:20","12:35","12:50","13:25","-","13:55"),
    ("12:55","13:30","13:45","14:00","14:15","14:50","-","15:20"),
    ("-","15:00","15:15","15:30","15:45","16:20","-","16:50"),
    ("-","16:30","16:45","17:00","17:15","17:50","-","18:20"),
    ("-","17:35","17:50","18:05","18:20","18:55","-","19:25"),
    ("17:55","18:30","18:45","19:00","19:15","19:50","-","20:20"),
    ("-","19:35","19:50","20:05","20:20","20:55","-","21:25"),
    ("20:00","20:35","20:50","21:05","21:20","21:55","-","22:25"),
    ("-","21:45","22:00","22:15","22:30","23:05","-","23:35"),
]
 
# ============================================================================
# 2. ADALAR - BEŞİKTAŞ HATTI
# ============================================================================
BSK_USTE_ISK = ["Büyükada","Heybeliada","Burgazada","Kınalıada","Kadıköy","Beşiktaş"]
BSK_ALTA_ISK = ["Beşiktaş","Kınalıada","Burgazada","Heybeliada","Büyükada"]
 
BSK_HIC_UST = [
    ("07:10","07:25","07:40","07:55","08:30","09:00"),
    ("11:10","11:25","11:40","11:55","12:30","13:00"),
    ("15:40","15:55","16:10","16:25","17:00","17:30"),
    ("18:00","18:15","18:30","18:45","19:20","19:50"),
]
BSK_HIC_ALT = [
    ("07:25","08:15","08:30","08:45","09:00"),
    ("13:00","13:50","14:05","14:20","14:35"),
    ("15:15","16:05","16:20","16:35","16:50"),
    ("18:15","19:05","19:20","19:35","19:50"),
]
BSK_PZR_UST = [
    ("08:35","08:50","09:05","09:20","09:55","10:25"),
    ("10:10","10:25","10:40","10:55","11:30","12:00"),
    ("15:40","15:55","16:10","16:25","17:00","17:30"),
    ("18:00","18:15","18:30","18:45","19:20","19:50"),
]
BSK_PZR_ALT = [
    ("08:10","09:00","09:15","09:30","09:45"),
    ("13:00","13:50","14:05","14:20","14:35"),
    ("15:15","16:05","16:20","16:35","16:50"),
    ("18:15","19:05","19:20","19:35","19:50"),
]
 
# ============================================================================
# 3. MALTEPE - BÜYÜKADA - HEYBELİADA - BURGAZADA - KINALIADA HATTI
# Her gün, ama yıldızlı (★) seferler Pazar günü yapılmaz
# ============================================================================
MALTEPE_USTE_ISK = ["Maltepe","Büyükada","Heybeliada","Burgazada","Kınalıada"]
MALTEPE_ALTA_ISK = ["Kınalıada","Burgazada","Heybeliada","Büyükada","Maltepe"]
 
# (satir, pazar_yapilmaz)
MALTEPE_UST = [
    (("06:45","07:05","07:20","07:35","07:50"), True),
    (("08:20","08:40","08:55","-","-"),         True),
    (("09:15","09:35","09:50","10:05","10:20"), False),
    (("10:05","10:25","-","-","-"),             False),
    (("11:20","11:40","11:55","12:10","12:25"), False),
    (("12:00","12:20","12:35","-","-"),         False),
    (("13:45","14:05","14:20","-","-"),         False),
    (("15:35","15:55","16:10","16:25","16:40"), False),
    (("16:50","17:10","-","-","-"),             False),
    (("17:50","18:10","18:25","-","-"),         False),
    (("18:35","18:55","19:10","-","-"),         False),
    (("19:05","19:25","19:40","-","-"),         False),
    (("20:05","20:25","20:40","-","-"),         False),
    (("20:40","21:00","21:15","-","-"),         False),
    (("21:45","22:05","22:20","22:35","22:50"), False),
]
MALTEPE_ALT = [
    (("07:05","07:20","07:35","07:50","08:10"), True),
    (("08:00","08:15","08:30","08:45","09:05"), True),
    (("-","-","09:15","09:30","09:50"),         False),
    (("-","-","-","10:55","11:15"),             False),
    (("10:30","10:45","11:00","11:15","11:35"), False),
    (("-","-","12:45","13:00","13:20"),         False),
    (("14:00","14:15","14:30","14:45","15:05"), False),
    (("-","-","15:40","15:55","16:15"),         False),
    (("-","-","-","17:20","17:40"),             False),
    (("17:10","17:25","17:40","17:55","18:15"), False),
    (("-","-","18:30","18:40","19:00"),         False),
    (("-","-","19:15","19:30","19:50"),         False),
    (("-","-","19:45","20:00","20:20"),         False),
    (("-","-","20:45","21:00","21:20"),         False),
    (("-","-","21:20","21:35","21:55"),         False),
]
 
# ============================================================================
# 4. BOSTANCI - ADALAR RİNG HATTI
# ============================================================================
RING_USTE_ISK = ["Bostancı","Kınalıada","Burgazada","Heybeliada","Büyükada","Bostancı"]
RING_ALTA_ISK = ["Bostancı","Büyükada","Heybeliada","Burgazada","Kınalıada","Bostancı"]
 
RING_HIC_UST = [
    ("02:00","02:25","02:40","02:55","03:10","03:45"),
    ("04:45","05:10","05:25","05:40","05:55","06:30"),
    ("-","-","-","08:35","08:50","-"),
    ("08:20","08:45","09:00","-","-","09:35"),
    ("15:10","15:35","15:50","16:05","16:20","16:55"),
    ("-","-","-","17:30","17:45","18:20"),
    ("21:45","22:10","22:25","22:40","22:55","23:30"),
]
RING_HIC_ALT = [
    ("-","06:45","07:00","-","-","07:30"),
    ("07:45","08:20","08:35","-","-","-"),
    ("09:25","10:00","10:15","10:30","10:45","11:10"),
    ("11:00","11:35","11:50","-","-","-"),
    ("18:35","19:10","19:25","19:40","19:55","20:20"),
    ("00:00","00:35","00:50","01:05","01:20","01:45"),
]
RING_PZR_UST = [
    ("02:00","02:25","02:40","02:55","03:10","03:45"),
    ("04:45","05:10","05:25","05:40","05:55","06:30"),
    ("-","-","-","08:35","08:50","09:35"),
    ("08:20","08:45","09:00","-","-","-"),
    ("15:10","15:35","15:50","16:05","16:20","16:55"),
    ("-","-","-","17:30","17:45","18:20"),
    ("21:45","22:10","22:25","22:40","22:55","23:30"),
]
RING_PZR_ALT = [
    ("-","07:05","07:20","-","-","07:45"),
    ("07:45","08:20","08:35","-","-","-"),
    ("10:05","10:40","10:55","11:10","11:25","11:50"),
    ("11:00","11:35","11:50","-","-","-"),
    ("18:35","19:10","19:25","19:40","19:55","20:20"),
    ("00:00","00:35","00:50","01:05","01:20","01:45"),
]
 
# ============================================================================
# 5. BÜYÜKADA - SEDEF ADASI HATTI
# ============================================================================
SEDEF_HIC = [  # (Sedef→Büyükada, Büyükada→Sedef)
    ("Sedef Adası", "07:35", "Büyükada", "07:50"),
    ("Büyükada", "19:45", "Sedef Adası", "20:00"),
]
SEDEF_PZR = [
    ("Sedef Adası", "07:55", "Büyükada", "08:10"),
    ("Büyükada", "19:45", "Sedef Adası", "20:00"),
]
 
# ============================================================================
# 6. TUZLA - PENDİK - BÜYÜKADA HATTI (sadece Cmt/Paz/Tatil)
# ============================================================================
TUZLA_USTE_ISK = ["Tuzla","Pendik","Büyükada"]
TUZLA_ALTA_ISK = ["Büyükada","Pendik","Tuzla"]
TUZLA_UST = [("10:35","11:30","12:15")]
TUZLA_ALT = [("18:20","19:05","20:00")]
 
 
def _process_sedef(rows: List[Tuple], gun_notu: str) -> List[Sefer]:
    """Sedef Adası seferleri için özel işleyici (basit 2-iskele rota)."""
    out = []
    for kalkis, k_saat, varis, v_saat in rows:
        yon = "buyukadaya" if varis == "Büyükada" else "buyukadadan"
        out.append(Sefer(
            kalkis_saati=k_saat,
            operator=OPERATOR,
            operator_kod=OPERATOR_KOD,
            kalkis_iskelesi=kalkis,
            varis_iskelesi=varis,
            yon=yon,
            rota=[kalkis, varis],
            direkt=True,
            tahmini_sure_dk=_dk_farki(k_saat, v_saat),
            notlar=gun_notu,
        ))
    return out
 
 
# ============================================================================
# ANA SCRAPE FONKSİYONU
# ============================================================================
 
def scrape() -> List[Sefer]:
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=3)))
    weekday = now.weekday()  # 0=Pzt, 5=Cmt, 6=Paz
    pazar = (weekday == 6)
    cumartesi_pazar_tatil = weekday >= 5  # Tuzla için
 
    seferler: List[Sefer] = []
    note_hic = "hafta içi/cumartesi tarifesi"
    note_pzr = "pazar/tatil tarifesi"
    note_hg  = "her gün"
 
    # 1. Kabataş - Adalar
    if pazar:
        seferler += _process_table(KABATAS_USTE_ISK, KABATAS_PZR_UST, note_pzr)
        seferler += _process_table(KABATAS_ALTA_ISK, KABATAS_PZR_ALT, note_pzr)
    else:
        seferler += _process_table(KABATAS_USTE_ISK, KABATAS_HIC_UST, note_hic)
        seferler += _process_table(KABATAS_ALTA_ISK, KABATAS_HIC_ALT, note_hic)
 
    # 2. Adalar - Beşiktaş
    if pazar:
        seferler += _process_table(BSK_USTE_ISK, BSK_PZR_UST, note_pzr)
        seferler += _process_table(BSK_ALTA_ISK, BSK_PZR_ALT, note_pzr)
    else:
        seferler += _process_table(BSK_USTE_ISK, BSK_HIC_UST, note_hic)
        seferler += _process_table(BSK_ALTA_ISK, BSK_HIC_ALT, note_hic)
 
    # 3. Maltepe (her gün, ama yıldızlı satırlar Pazar yok)
    maltepe_ust = [r for r, pzr_yok in MALTEPE_UST if not (pzr_yok and pazar)]
    maltepe_alt = [r for r, pzr_yok in MALTEPE_ALT if not (pzr_yok and pazar)]
    seferler += _process_table(MALTEPE_USTE_ISK, maltepe_ust, note_hg)
    seferler += _process_table(MALTEPE_ALTA_ISK, maltepe_alt, note_hg)
 
    # 4. Bostancı Ring
    if pazar:
        seferler += _process_table(RING_USTE_ISK, RING_PZR_UST, note_pzr)
        seferler += _process_table(RING_ALTA_ISK, RING_PZR_ALT, note_pzr)
    else:
        seferler += _process_table(RING_USTE_ISK, RING_HIC_UST, note_hic)
        seferler += _process_table(RING_ALTA_ISK, RING_HIC_ALT, note_hic)
 
    # 5. Büyükada - Sedef
    if pazar:
        seferler += _process_sedef(SEDEF_PZR, note_pzr)
    else:
        seferler += _process_sedef(SEDEF_HIC, note_hic)
 
    # 6. Tuzla - Pendik - Büyükada (Cmt, Paz, Tatil)
    if cumartesi_pazar_tatil:
        seferler += _process_table(TUZLA_USTE_ISK, TUZLA_UST, "cumartesi/pazar/tatil")
        seferler += _process_table(TUZLA_ALTA_ISK, TUZLA_ALT, "cumartesi/pazar/tatil")
 
    print(f"[SH] {len(seferler)} sefer (gün={weekday}, pazar={pazar})", file=sys.stderr)
    return seferler
 
 
if __name__ == "__main__":
    import json
    seferler = scrape()
    print(json.dumps([s.as_dict() for s in seferler], ensure_ascii=False, indent=2))
