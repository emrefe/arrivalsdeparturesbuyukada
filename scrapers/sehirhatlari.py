"""
Şehir Hatları (sehirhatlari.istanbul) — canlı sayfa scraper'ı.

Eski versiyon PDF'ten elle çevrilmiş kış tarifesiydi ve yaz/kış geçişinde
manuel güncelleme gerektiriyordu. Bu versiyon canlı web sayfalarını
scrape eder — 29 Haziran → 6 Eylül yaz tarifesi ile geçtiğinde otomatik
olarak yeni tarifeyi alır.

Kaynak: Büyükada'ya bağlı 6 hat sayfası
  1. Bostancı-Adalar Ring (770)
  2. Kabataş-Adalar (177)
  3. Adalar-Beşiktaş (769)
  4. Maltepe-Büyükada-Heybeliada-Burgazada-Kınalıada (2020)
  5. Büyükada-Sedef Adası (895)
  6. Tuzla-Pendik-Büyükada (3373)

Her sayfada 2-4 tablo var (yönler × gün-tipleri):
  - "HAFTA İÇİ VE CUMARTESİ GÜNLERİ"
  - "SADECE PAZAR VE TATİL GÜNLERİ"

Bugünün gününe göre uygun tabloyu seçer.
"""
from __future__ import annotations
import sys
import datetime as dt
import re
from typing import List, Optional, Dict, Any

from common import Sefer

OPERATOR = "Şehir Hatları"
OPERATOR_KOD = "SH"
BASE_URL = "https://sehirhatlari.istanbul"

# Büyükada'ya bağlı tüm hatlar — sefer-arama üzerinden otomatik keşfedildi
ROUTES = [
    "https://sehirhatlari.istanbul/tr/seferler/ic-hatlar/adalar-hatlari/bostanci-adalar-ring-hatti-770",
    "https://sehirhatlari.istanbul/tr/seferler/ic-hatlar/adalar-hatlari/kabatasadalar-177",
    "https://sehirhatlari.istanbul/tr/seferler/ic-hatlar/adalar-hatlari/adalar-besiktas-769",
    "https://sehirhatlari.istanbul/tr/seferler/ic-hatlar/adalar-hatlari/maltepe-buyukada-heybeliada-burgazada-kinaliada-hatti-2020",
    "https://sehirhatlari.istanbul/tr/seferler/ic-hatlar/adalar-hatlari/buyukada-sedef-adasi-hatti-895",
    "https://sehirhatlari.istanbul/tr/seferler/ic-hatlar/adalar-hatlari/tuzla-pendik-buyukada-hatti-3373",
]


# ---------------------------------------------------------------------------
# Fetch (requests → playwright fallback)
# ---------------------------------------------------------------------------

def _fetch(url: str) -> Optional[str]:
    """
    SH sayfasını çek.
    SH sitesi data-center IP'lerini 403'lüyor. curl_cffi ile Chrome TLS
    fingerprint'i taklit ederek geçebiliyoruz. Yerel geliştirmede requests
    de çalışır.
    """
    # 1) curl_cffi (Chrome fingerprint) — Actions runner için ana yöntem
    try:
        from curl_cffi import requests as cffi_requests
        r = cffi_requests.get(url, timeout=30, impersonate="chrome120")
        if r.status_code == 200 and "<table" in r.text.lower():
            return r.text
        print(f"[SH] curl_cffi HTTP {r.status_code} — {url}", file=sys.stderr)
    except ImportError:
        pass  # curl_cffi yok, requests dene
    except Exception as e:
        print(f"[SH] curl_cffi hata {url}: {e}", file=sys.stderr)

    # 2) Klasik requests — lokal fallback
    try:
        import requests
        r = requests.get(url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9",
        })
        if r.ok and "<table" in r.text.lower():
            return r.text
        print(f"[SH] requests HTTP {r.status_code} — {url}", file=sys.stderr)
    except Exception as e:
        print(f"[SH] requests hata {url}: {e}", file=sys.stderr)

    return None


# ---------------------------------------------------------------------------
# HTML parsing
# ---------------------------------------------------------------------------

def _parse_page(html: str) -> List[Dict[str, Any]]:
    """
    Sayfadan tabloları çıkar. Her tablo bir dict:
      { "gun_tipi": "hafta_ici_cmt" | "pazar",
        "iskeleler": [...],
        "seferler": [[...]] }
    """
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 3:
            continue

        # 1. satır başlık: "HAFTA İÇİ VE CUMARTESİ GÜNLERİ" veya "PAZAR VE TATİL GÜNLERİ"
        cap = re.sub(r"\s+", " ", rows[0].get_text(" ", strip=True)).upper()
        if "PAZAR" in cap:
            gun_tipi = "pazar"
        elif "HAFTA" in cap or "CUMARTESİ" in cap:
            gun_tipi = "hafta_ici_cmt"
        else:
            gun_tipi = "hafta_ici_cmt"

        # 2. satır iskele adları
        iskele_cells = rows[1].find_all(["td", "th"])
        iskeleler = [c.get_text(strip=True) for c in iskele_cells]
        # Kalan satırlar sefer saatleri
        sefer_rows: List[List[str]] = []
        for r in rows[2:]:
            cells = [c.get_text(strip=True) for c in r.find_all(["td", "th"])]
            if not cells:
                continue
            # "Kalkış" / "Varış" başlık satırı
            if any(x.lower() in ("kalkış", "varış") for x in cells[:2]):
                continue
            if all(c == "-" or c == "" for c in cells):
                continue
            sefer_rows.append(cells)

        if iskeleler and sefer_rows:
            out.append({"gun_tipi": gun_tipi, "iskeleler": iskeleler, "seferler": sefer_rows})
    return out


# ---------------------------------------------------------------------------
# Sefer üretimi
# ---------------------------------------------------------------------------

def _dk_farki(s1: str, s2: str) -> int:
    """HH:MM iki saat arası dakika farkı (gece geçişi destekler)."""
    try:
        h1, m1 = map(int, s1.split(":"))
        h2, m2 = map(int, s2.split(":"))
    except Exception:
        return 30
    fark = (h2 * 60 + m2) - (h1 * 60 + m1)
    if fark < 0:
        fark += 24 * 60
    return fark


def _seferleri_uret(tables: List[Dict[str, Any]], is_pazar_tatil: bool) -> List[Sefer]:
    """
    Verilen tablolardan Büyükada'ya ilişkin Sefer nesneleri üret.
    Bugünün gün tipine göre (pazar/tatil vs değil) uygun tabloları seç.
    """
    hedef_gun = "pazar" if is_pazar_tatil else "hafta_ici_cmt"
    out: List[Sefer] = []
    for t in tables:
        if t["gun_tipi"] != hedef_gun:
            continue
        iskeleler = t["iskeleler"]
        if "Büyükada" not in iskeleler:
            continue
        bua_idx = iskeleler.index("Büyükada")

        for sefer in t["seferler"]:
            n = min(len(sefer), len(iskeleler))
            if bua_idx >= n:
                continue
            bua_saat = sefer[bua_idx]
            if bua_saat == "-" or not re.match(r"^\d{1,2}:\d{2}$", bua_saat):
                continue

            # ---- Büyükada'ya GELİŞ ----
            kalkis_idx = None
            for i in range(bua_idx):
                if i < n and sefer[i] not in ("-", ""):
                    kalkis_idx = i
                    break
            if kalkis_idx is not None:
                kalkis_saat = sefer[kalkis_idx]
                rota = [iskeleler[i] for i in range(kalkis_idx, bua_idx + 1)
                        if i < n and sefer[i] not in ("-", "")]
                sure = _dk_farki(kalkis_saat, bua_saat)
                out.append(Sefer(
                    kalkis_saati=kalkis_saat,
                    operator=OPERATOR,
                    operator_kod=OPERATOR_KOD,
                    kalkis_iskelesi=iskeleler[kalkis_idx],
                    varis_iskelesi="Büyükada",
                    yon="buyukadaya",
                    rota=rota,
                    direkt=(len(rota) == 2),
                    tahmini_sure_dk=sure,
                    notlar=None,
                ))

            # ---- Büyükada'dan GİDİŞ ----
            son_idx = None
            for i in range(len(iskeleler) - 1, bua_idx, -1):
                if i < n and sefer[i] not in ("-", ""):
                    son_idx = i
                    break
            if son_idx is not None:
                varis_saat = sefer[son_idx]
                rota = [iskeleler[i] for i in range(bua_idx, son_idx + 1)
                        if i < n and sefer[i] not in ("-", "")]
                sure = _dk_farki(bua_saat, varis_saat)
                out.append(Sefer(
                    kalkis_saati=bua_saat,
                    operator=OPERATOR,
                    operator_kod=OPERATOR_KOD,
                    kalkis_iskelesi="Büyükada",
                    varis_iskelesi=iskeleler[son_idx],
                    yon="buyukadadan",
                    rota=rota,
                    direkt=(len(rota) == 2),
                    tahmini_sure_dk=sure,
                    notlar=None,
                ))
    return out


# ---------------------------------------------------------------------------
# Ana giriş
# ---------------------------------------------------------------------------

def _load_hardcoded() -> List[Sefer]:
    """
    data/sh_hardcoded.json'dan yaz tarifesi seferlerini yükle.
    Bu dosya sezon başında Chrome üzerinden canlı scrape ile üretilir.
    SH sitesi GitHub Actions IP'lerini 403'lediği için Actions'tan direkt
    scrape mümkün değil — sezon değişince manuel refresh gerek.
    """
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parent.parent / "data" / "sh_hardcoded.json"
    if not path.exists():
        print(f"[SH] hardcoded json yok: {path}", file=sys.stderr)
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=3)))
    is_pazar = (now.weekday() == 6)
    gun_hedef = "pazar" if is_pazar else "hafta_ici_cmt"

    out: List[Sefer] = []
    for s in data.get("seferler", []):
        if s.get("gunTipi") != gun_hedef:
            continue
        out.append(Sefer(
            kalkis_saati=s["kalkis_saati"],
            operator=OPERATOR,
            operator_kod=OPERATOR_KOD,
            kalkis_iskelesi=s["kalkis_iskelesi"],
            varis_iskelesi=s["varis_iskelesi"],
            yon=s["yon"],
            rota=s["rota"],
            direkt=s["direkt"],
            tahmini_sure_dk=s["tahmini_sure_dk"],
            notlar=s.get("notlar"),
        ))
    print(f"[SH] hardcoded'dan {len(out)} sefer yüklendi (gun={gun_hedef}, kaynak={data.get('_meta',{}).get('fetched_at','?')})", file=sys.stderr)
    return out


def scrape() -> List[Sefer]:
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=3)))
    is_pazar = (now.weekday() == 6)

    # 1) Canlı fetch dene (Actions IP 403 alabilir, o zaman fallback)
    all_tables: List[Dict[str, Any]] = []
    for url in ROUTES:
        print(f"[SH] fetch {url}", file=sys.stderr)
        html = _fetch(url)
        if not html:
            print(f"[SH]   skipped (fetch fail)", file=sys.stderr)
            continue
        try:
            tables = _parse_page(html)
            print(f"[SH]   {len(tables)} tablo", file=sys.stderr)
            all_tables.extend(tables)
        except Exception as e:
            print(f"[SH]   parse hatası: {e}", file=sys.stderr)

    seferler = _seferleri_uret(all_tables, is_pazar)
    if seferler:
        print(f"[SH] {len(seferler)} sefer (canli scrape, pazar={is_pazar})", file=sys.stderr)
        return seferler

    # 2) Canlı boş — hardcoded JSON'dan yükle
    print(f"[SH] canli scrape 0 sefer, hardcoded'a düşülüyor", file=sys.stderr)
    return _load_hardcoded()


if __name__ == "__main__":
    import json
    seferler = scrape()
    print(json.dumps([s.as_dict() for s in seferler], ensure_ascii=False, indent=2))
