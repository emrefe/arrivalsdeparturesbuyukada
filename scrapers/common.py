"""
Ortak yardımcılar: veri modeli, iskele ismi normalleştirme, HTTP istemcisi.
Tüm scraper'lar bu modülü kullanır.
"""
from __future__ import annotations
import re
import unicodedata
from dataclasses import dataclass, asdict, field
from typing import List, Optional
import requests

# ---------- HTTP ----------
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

def fetch(url: str, timeout: int = 20) -> str:
    """Bir URL'i GET'le ve metnini döndür. Hata fırlatır."""
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or "utf-8"
    return r.text


# ---------- VERİ MODELİ ----------
@dataclass
class Sefer:
    kalkis_saati: str            # "HH:MM"
    operator: str                # "Şehir Hatları" | "Mavi Marmara" | "Prens Tur"
    operator_kod: str            # "SH" | "MM" | "PT"
    kalkis_iskelesi: str         # standart isim
    varis_iskelesi: str          # standart isim
    yon: str                     # "buyukadaya" | "buyukadadan"
    rota: List[str]              # tüm uğraklar (kalkış ve varış dahil)
    direkt: bool
    tahmini_sure_dk: Optional[int] = None
    notlar: Optional[str] = None

    def as_dict(self):
        return asdict(self)


# ---------- İSKELE İSİM NORMALLEŞTİRME ----------
ISKELE_ESLESMELERI = {
    # Standardize edilmiş isim -> alternatif yazımlar
    "Büyükada":   ["büyükada", "buyukada", "b.ada", "b. ada", "ada"],
    "Heybeliada": ["heybeliada", "heybeli", "heybeli ada"],
    "Burgazada":  ["burgazada", "burgaz", "burgaz ada"],
    "Kınalıada":  ["kınalıada", "kinaliada", "kınalı", "kinali"],
    "Sedef Adası": ["sedef", "sedef adası", "sedef adasi"],
    "Bostancı":   ["bostancı", "bostanci"],
    "Kabataş":    ["kabataş", "kabatas"],
    "Kadıköy":    ["kadıköy", "kadikoy"],
    "Eminönü":    ["eminönü", "eminonu"],
    "Karaköy":    ["karaköy", "karakoy"],
    "Beşiktaş":   ["beşiktaş", "besiktas"],
    "Kartal":     ["kartal"],
    "Maltepe":    ["maltepe"],
    "Pendik":     ["pendik"],
    "Tuzla":      ["tuzla"],
    "Yenikapı":   ["yenikapı", "yenikapi"],
    "Üsküdar":    ["üsküdar", "uskudar"],
}

def _temiz(s: str) -> str:
    """Küçük harf, aksanlı karakterleri sadeleştir, gereksiz boşlukları temizle."""
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s

def normalize_iskele(name: str) -> str:
    """Bir iskele ismini standart hâle getir. Eşleşme bulamazsa girdiyi olduğu gibi (capitalize) döner."""
    t = _temiz(name)
    for std, varyantlar in ISKELE_ESLESMELERI.items():
        if t in varyantlar:
            return std
        # tam eşleşme yoksa, varyantın bir alt-string olup olmadığına bak
        for v in varyantlar:
            if v == t or t == v:
                return std
    # bilinmeyen — orjinali title-case ile döndür
    return name.strip().title()


# ---------- ZAMAN PARSE ----------
SAAT_REGEX = re.compile(r"\b([01]?\d|2[0-3])[:\.]([0-5]\d)\b")

def parse_saatler(metin: str) -> List[str]:
    """Metinden tüm HH:MM (ve HH.MM) saatleri çıkar, normalleştirilmiş 'HH:MM' formatında döndür."""
    out = []
    for m in SAAT_REGEX.finditer(metin):
        h, mn = int(m.group(1)), int(m.group(2))
        out.append(f"{h:02d}:{mn:02d}")
    return out


# ---------- ROTA / YÖN MANTIĞI ----------
def yon_belirle(rota: List[str]) -> str:
    """Rotanın Büyükada'ya mı, yoksa Büyükada'dan mı olduğunu çıkar."""
    rota_norm = [normalize_iskele(x) for x in rota]
    if not rota_norm:
        return "buyukadaya"
    if rota_norm[0] == "Büyükada":
        return "buyukadadan"
    if rota_norm[-1] == "Büyükada":
        return "buyukadaya"
    # Büyükada bir ara durak ise: bu seferi her iki yön için 'arası' kabul edebiliriz, ama
    # şimdilik 'Büyükada içeren ama uçtan uca olmayan' rotaları "buyukadaya" sayacağız.
    if "Büyükada" in rota_norm:
        # daha akıllıca: hangi tarafa daha yakınsa o yön
        idx = rota_norm.index("Büyükada")
        return "buyukadaya" if idx > len(rota_norm) // 2 else "buyukadadan"
    return "buyukadaya"  # default


def direkt_mi(rota: List[str]) -> bool:
    return len([x for x in rota if x.strip()]) <= 2
