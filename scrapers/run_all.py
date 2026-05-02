"""
Tüm scraper'ları çalıştır, sonuçları birleştir, data/seferler.json dosyasına yaz.

Bu script GitHub Actions tarafından her gün otomatik çalıştırılır.
Lokalde de çalıştırılabilir:
    cd scrapers
    pip install -r requirements.txt
    python run_all.py
"""
from __future__ import annotations
import json
import sys
import datetime as dt
from pathlib import Path
from typing import List, Dict, Any

# Aynı klasördeki scraper modüllerini import et
import sehirhatlari
import mavimarmara
import prenstur
from common import Sefer

ISTANBUL_TZ = dt.timezone(dt.timedelta(hours=3))


def collect() -> Dict[str, Any]:
    seferler: List[Sefer] = []
    kaynaklar: Dict[str, Dict[str, Any]] = {}

    for ad, modul in [
        ("sehirhatlari", sehirhatlari),
        ("mavimarmara", mavimarmara),
        ("prenstur",     prenstur),
    ]:
        try:
            s = modul.scrape()
            seferler.extend(s)
            kaynaklar[ad] = {
                "site": getattr(modul, "BASE_URL", None) or f"https://{ad}.net",
                "son_guncel": dt.datetime.now(ISTANBUL_TZ).isoformat(timespec="seconds"),
                "durum": "ok" if s else "bos",
                "sefer_sayisi": len(s),
            }
            print(f"[{ad}] -> {len(s)} sefer", file=sys.stderr)
        except Exception as e:
            print(f"[{ad}] HATA: {e}", file=sys.stderr)
            kaynaklar[ad] = {
                "site": f"https://{ad}.net",
                "son_guncel": dt.datetime.now(ISTANBUL_TZ).isoformat(timespec="seconds"),
                "durum": f"hata: {e}",
                "sefer_sayisi": 0,
            }

    # Saate göre sırala
    seferler.sort(key=lambda s: s.kalkis_saati)

    now = dt.datetime.now(ISTANBUL_TZ)
    return {
        "updated_at": now.isoformat(timespec="seconds"),
        "tarih_yerel": now.strftime("%d.%m.%Y"),
        "kaynaklar": kaynaklar,
        "seferler": [s.as_dict() for s in seferler],
    }


def main():
    data = collect()
    out_path = Path(__file__).resolve().parent.parent / "data" / "seferler.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n✓ {len(data['seferler'])} sefer yazıldı -> {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
