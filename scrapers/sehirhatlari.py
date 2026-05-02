"""
Şehir Hatları (sehirhatlari.istanbul) için scraper.

NOT: Site dinamik olabilir (dropdown'la yüklenen tablolar). Bu durumda direkt HTML
parse'ı yetmezse şu seçeneklere bakılır:
  1. Sayfanın altta yatan JSON/AJAX endpoint'lerini bulup oradan çekmek
  2. Playwright ile tarayıcı simülasyonu
  3. Gözlemlenen sefer saatlerini elden bir tabloya yazıp scrape başarısız olunca
     fallback olarak kullanmak (aşağıda var).

Bu scraper'ı ilk gerçek çalışmasında loglara bakarak rafine edeceğiz.
"""
from __future__ import annotations
from typing import List
from bs4 import BeautifulSoup
import sys
import traceback

from common import Sefer, fetch, normalize_iskele, parse_saatler, direkt_mi

OPERATOR = "Şehir Hatları"
OPERATOR_KOD = "SH"

# Şehir Hatları'nın Adalar hattıyla ilgili olan URL'leri
ROTALAR = [
    # (url, kalkış_iskelesi_adı, varış_iskelesi_adı, beklenen_uğraklar, yön, tahmini_süre_dk)
    # Bu liste site yapısını gözlemleyip rafine edilecek
    {
        "url": "https://sehirhatlari.istanbul/tr/seferler/ic-hatlar/adalar-hatlari-176",
        "ad": "Adalar Ana Hat",
    },
]

# Eğer scrape başarısız olursa kullanılacak elle-derlenmiş fallback tarife.
# Bu Şehir Hatları'nın bilinen, kararlı olarak çalışan seferlerinin yaklaşık dökümüdür.
# Gerçek scrape başarılı olduğunda devre dışı bırakılır.
FALLBACK_SEFERLER = [
    # (saat, kalkış, rota_listesi, varış, süre_dk)
    # — Kabataş kalkışlı (büyük vapur, ~95 dk Büyükada'ya)
    ("06:50", "Kabataş",  ["Kabataş","Kadıköy","Kınalıada","Burgazada","Heybeliada","Büyükada"], "Büyükada", 95),
    ("09:35", "Kabataş",  ["Kabataş","Kadıköy","Kınalıada","Burgazada","Heybeliada","Büyükada"], "Büyükada", 95),
    ("12:00", "Kabataş",  ["Kabataş","Kadıköy","Kınalıada","Burgazada","Heybeliada","Büyükada"], "Büyükada", 95),
    ("14:00", "Kabataş",  ["Kabataş","Kadıköy","Kınalıada","Burgazada","Heybeliada","Büyükada"], "Büyükada", 95),
    ("17:35", "Kabataş",  ["Kabataş","Kadıköy","Kınalıada","Burgazada","Heybeliada","Büyükada"], "Büyükada", 95),
    ("19:30", "Kabataş",  ["Kabataş","Kadıköy","Kınalıada","Burgazada","Heybeliada","Büyükada"], "Büyükada", 95),
    ("22:00", "Kabataş",  ["Kabataş","Kadıköy","Kınalıada","Burgazada","Heybeliada","Büyükada"], "Büyükada", 95),
    # — Bostancı ring (~50 dk)
    ("06:30", "Bostancı", ["Bostancı","Heybeliada","Burgazada","Kınalıada","Büyükada"], "Büyükada", 50),
    ("07:30", "Bostancı", ["Bostancı","Heybeliada","Büyükada"], "Büyükada", 45),
    ("10:30", "Bostancı", ["Bostancı","Heybeliada","Burgazada","Kınalıada","Büyükada"], "Büyükada", 50),
    ("13:00", "Bostancı", ["Bostancı","Heybeliada","Büyükada"], "Büyükada", 45),
    ("15:00", "Bostancı", ["Bostancı","Heybeliada","Burgazada","Kınalıada","Büyükada"], "Büyükada", 50),
    ("16:30", "Bostancı", ["Bostancı","Heybeliada","Büyükada"], "Büyükada", 45),
    ("18:30", "Bostancı", ["Bostancı","Heybeliada","Burgazada","Kınalıada","Büyükada"], "Büyükada", 50),
    ("21:00", "Bostancı", ["Bostancı","Heybeliada","Büyükada"], "Büyükada", 45),
    ("23:30", "Bostancı", ["Bostancı","Heybeliada","Burgazada","Kınalıada","Büyükada"], "Büyükada", 50),
    # — Eminönü
    ("08:30", "Eminönü", ["Eminönü","Karaköy","Kabataş","Kadıköy","Kınalıada","Burgazada","Heybeliada","Büyükada"], "Büyükada", 105),
    # — Geri yön (Büyükada -> ...)
    ("06:45", "Büyükada", ["Büyükada","Heybeliada","Burgazada","Kınalıada","Bostancı"], "Bostancı", 50),
    ("08:00", "Büyükada", ["Büyükada","Heybeliada","Burgazada","Kınalıada","Kadıköy","Kabataş"], "Kabataş", 95),
    ("09:00", "Büyükada", ["Büyükada","Heybeliada","Bostancı"], "Bostancı", 45),
    ("11:00", "Büyükada", ["Büyükada","Heybeliada","Burgazada","Kınalıada","Kadıköy","Kabataş"], "Kabataş", 95),
    ("14:00", "Büyükada", ["Büyükada","Heybeliada","Burgazada","Kınalıada","Bostancı"], "Bostancı", 50),
    ("15:00", "Büyükada", ["Büyükada","Heybeliada","Burgazada","Kınalıada","Kadıköy","Kabataş"], "Kabataş", 95),
    ("16:30", "Büyükada", ["Büyükada","Heybeliada","Bostancı"], "Bostancı", 45),
    ("18:00", "Büyükada", ["Büyükada","Heybeliada","Burgazada","Kınalıada","Kadıköy","Kabataş"], "Kabataş", 95),
    ("20:00", "Büyükada", ["Büyükada","Heybeliada","Burgazada","Kınalıada","Bostancı"], "Bostancı", 50),
    ("21:00", "Büyükada", ["Büyükada","Heybeliada","Burgazada","Kınalıada","Kadıköy","Kabataş"], "Kabataş", 95),
    ("22:00", "Büyükada", ["Büyükada","Heybeliada","Bostancı"], "Bostancı", 45),
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
    """
    Canlı scrape denemesi.
    Bu fonksiyon gerçek HTML'i gördükten sonra rafine edilecek.
    Şu anki versiyonu sadece sayfanın yüklenip yüklenmediğini kontrol eder
    ve içinde 'adalar' geçen anchor'lardaki saatleri toplar — bu
    muhtemelen yetersiz olacak ve fallback'e dönülecek.
    """
    seferler: List[Sefer] = []
    for r in ROTALAR:
        try:
            html = fetch(r["url"])
            soup = BeautifulSoup(html, "html.parser")
            # Gözlemlenmesi gereken: tablo / liste yapısı, hangi class'larda saatler var?
            # Şu an placeholder — sadece sayfada Adalar geçiyor mu kontrol et
            if "adalar" not in soup.get_text(" ", strip=True).lower():
                print(f"[SH] Beklenen içerik bulunamadı: {r['url']}", file=sys.stderr)
                continue
            # TODO: gerçek tablo parse'ı buraya gelecek
            # Şimdilik fallback'e bırak — boş liste döndür
        except Exception as e:
            print(f"[SH] Hata {r['url']}: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
    return seferler


def scrape() -> List[Sefer]:
    """Ana giriş noktası. Önce canlı scrape dene, başarısızsa fallback'e geç."""
    seferler = _scrape_canli()
    if seferler:
        print(f"[SH] Canlı scrape başarılı: {len(seferler)} sefer", file=sys.stderr)
        return seferler
    print("[SH] Canlı scrape veri vermedi, fallback kullanılıyor", file=sys.stderr)
    return _fallback_seferler()


if __name__ == "__main__":
    import json
    seferler = scrape()
    print(json.dumps([s.as_dict() for s in seferler], ensure_ascii=False, indent=2))
