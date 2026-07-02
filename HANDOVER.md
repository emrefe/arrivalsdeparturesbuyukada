# KÖŞK Büyükada — Handover Dokümanı

> Kişisel hesaptan **KÖŞK team** hesabına devir notu. Bu dokümanı okuyan kişi (veya gelecekteki sen) sıfırdan projeye sahip çıkabilir.

**Son güncelleme:** 2026-05-03
**Devreden:** Emre Efabrika (emre@efabrika.com)
**Devralan:** KÖŞK Team
**İletişim:** hello@kosk.istanbul

---

## 1. Proje Nedir?

Büyükada (Adalar) ziyaretçileri için açık erişimli, dilden bağımsız bir dijital hizmet seti. KÖŞK markası altında 4 ayrı sayfadan oluşan tek bir statik web uygulaması.

| Sayfa | Dosya | İçerik |
|---|---|---|
| **SEFERLER** | `index.html` | Şehir Hatları + Mavi Marmara + Prens Tur vapur saatleri (gün bazında, "şimdi sonrası") |
| **TUR** | `tur.html` | Başlangıç saati + ilgi alanlarına göre ada içi yürüyüş/bus turu üretici |
| **ETKİNLİKLER** | `whatson.html` | Adalar etkinlik takvimi (konser, sergi, atölye, sinema) |
| **OTOBÜSLER** | `ulasim.html` | Ada içi 4 elektrikli İETT hattı (BA-1 / BA-2 / BA-3 / BA-4) |

**Tasarım dili:** Solari split-flap estetiği · IBM Plex Mono · siyah-beyaz minimal · 6 dil (TR, EN, RU, AR, DE, FR) · light/dark theme · Open-Meteo hava durumu mini-bar.

---

## 2. Teknoloji Stack

| Katman | Teknoloji | Neden |
|---|---|---|
| Frontend | Vanilla HTML/CSS/JS — framework yok | GitHub Pages'te zero-build, hızlı yükleme |
| Hosting | GitHub Pages (statik) | Ücretsiz, custom domain destekler |
| Otomasyon | GitHub Actions (cron) | Vapur saatleri günlük scrape edilir |
| Scraping | Python · BeautifulSoup · Playwright · pdfplumber | Cloudflare bypass için Playwright kullanılıyor |
| Veri | JSON dosyaları (`data/*.json`) | Statik, indekslenebilir, kolay diff |
| Hava durumu | [Open-Meteo](https://open-meteo.com) public API | API key gerekmiyor |
| Font | Google Fonts (IBM Plex Mono + Plex Sans Arabic) | CDN |

**Önemli:** Hiçbir backend yok, hiçbir veritabanı yok. Tüm veri JSON'larda. Sıfır maliyet.

---

## 3. Dosya Yapısı

```
buyukada-saatleri/
├── index.html              # SEFERLER — vapur saatleri
├── tur.html                # TUR — gün planlayıcı
├── whatson.html            # ETKİNLİKLER
├── ulasim.html             # OTOBÜSLER
├── HANDOVER.md             # ← bu dosya
├── README.md
├── data/
│   ├── seferler.json       # vapur saatleri (3 operatör)
│   ├── places.json         # Büyükada POI veritabanı (tur planlayıcı için)
│   ├── events.json         # etkinlikler
│   └── ulasim.json         # 4 BA otobüs hattı
├── scrapers/
│   ├── sehir_hatlari.py    # PDF parser
│   ├── mavi_marmara.py     # web scraper
│   ├── prens_tur.py        # Cloudflare-arkası scraper (Playwright)
│   └── merge.py            # 3 kaynaktan tek seferler.json üretir
└── .github/workflows/
    └── scrape-daily.yml    # cron: her sabah 04:00 UTC
```

---

## 4. Mevcut Durum (Mayıs 2026)

### ✅ Tamamlanmış işler
- 4 sayfa tam fonksiyonel, mobil + masaüstü responsive.
- 6 dil tam çevrili (TR, EN, RU, AR, DE, FR — Arapça RTL dahil).
- Light/dark theme + sistem teması auto-detect.
- Hava durumu mini bar tüm sayfalarda (Open-Meteo, sessionStorage cache, 1 saat).
- Solari "flap" load animasyonu + per-row cascade.
- Tur planlayıcı: zone bazlı proximity + uzun yürüyüşlerde otobüs önerisi + tur sonu için dönüş vapuru önerisi.
- GitHub Actions günlük scrape pipeline'ı kurulu.
- Tüm sayfalar arası tutarlı masthead: `BÜYÜKADA` brand + hava durumu + tema/dil + nav.

### ⚠️ Bilinen sınırlamalar / dikkat noktaları
- **Şehir Hatları PDF formatı değişirse:** `scrapers/sehir_hatlari.py` kırılabilir. PDF kaynağı: `https://www.sehirhatlari.istanbul/tarifeler` (yaz/kış tarifesi yılda 2 kez değişir).
- **Cloudflare bypass:** Prens Tur sitesi Cloudflare arkasında. Sandbox/lokal Playwright bazen başarısız olur; GitHub Actions runner'larda sorunsuz çalışır.
- **Etkinlik verisi:** `events.json` şu anda manuel besleniyor. adalar.bel.tr için scraper opsiyonel (eklenmeli).
- **Otobüs saatleri:** İETT'nin BA hatları için kararlı bir API yok; `data/ulasim.json` manuel kürasyon (yaz/kış aralıkları değişebilir).

---

## 5. Devir Adımları (KÖŞK Team Account'a Geçiş)

Aşağıdakileri sırayla yap. Her adımda repo erişimi, deploy ve otomasyon kesintisiz devam etmeli.

### Adım 1 — GitHub Repo Transfer

1. Eski hesapta repo ayarlarına git: **Settings → General → Transfer ownership**.
2. Yeni team hesabının adını gir (örn: `kosk-istanbul`).
3. Yeni hesapta repo görünür olunca, eski hesaptaki collaborator'ları yeniden davet et (eğer varsa).
4. Transfer sonrası **Settings → Pages**'i kontrol et — branch ve folder ayarı (`main` / `/ (root)`) korunmuş olmalı. Custom domain varsa DNS ayarı bozulmadığını doğrula.

### Adım 2 — GitHub Actions Yeniden Etkinleştirme

Repo transfer edildiğinde Actions varsayılan olarak **disabled** gelir.

1. Yeni repo'da **Actions** sekmesine git.
2. "I understand my workflows, go ahead and enable them" tıkla.
3. **Settings → Actions → General → Workflow permissions**'da `Read and write permissions` seç (scraper PR/commit atabilsin diye).
4. `.github/workflows/scrape-daily.yml`'i manuel "Run workflow" ile bir kez çalıştır — green olduğunu gör.

### Adım 3 — GitHub Pages Yeniden Konfigüre

1. **Settings → Pages**'e git.
2. Source: `Deploy from a branch`, Branch: `main`, Folder: `/ (root)`.
3. Custom domain: KÖŞK'ün kullanacağı domain (örn `ada.kosk.istanbul`). DNS:
   - `CNAME` kaydı: `ada.kosk.istanbul` → `kosk-istanbul.github.io`
   - HTTPS: GitHub otomatik Let's Encrypt sertifikası verir (24 saat sürebilir).
4. Repo köküne `CNAME` dosyası ekle, içeriği custom domain (tek satır).

### Adım 4 — Secrets / Credentials

Şu an **kullanılan secret yok** — Open-Meteo API key gerektirmiyor, scraping'de auth yok. Yine de:

- Eğer ilerde Instagram/etkinlik scraper'ı eklenecekse: **Settings → Secrets and variables → Actions** altına eklenir.
- `events.json` için bir CMS bağlanacaksa (Sanity, Contentful, Notion DB) API token'ları buraya gider.

### Adım 5 — Cowork Team Account Setup

Bu projede iş Cowork üzerinden yürütülmüştü. Team account'a taşırken:

1. KÖŞK team Cowork hesabında bu projenin klasörünü local olarak aç.
2. Eski hesapta varsa şunları team account'a kur:
   - **GitHub MCP connector** (repo işlemleri için)
   - **Slack/Notion connector** (etkinlik takibi için, opsiyonel)
3. `~/Library/Application Support/Claude/...` altındaki session geçmişi taşınmaz — yeni hesapta sıfırdan başlar. Bu doküman + repo, devamlılık için yeterli.

### Adım 6 — Domain & Marka

- **hello@kosk.istanbul** mail adresi team'e devredilmeli (Google Workspace / iCloud Custom Domain üzerinden).
- Footer'lardaki "KÜRATÖRLÜK · KÖŞK BÜYÜKADA" zaten brand'i KÖŞK'e bağlı tutuyor — değişiklik gerekmez.
- Sosyal: Instagram `@kosk.istanbul` ve `@adalaretkinlikler` referansları varsa team account'tan yönetilmeli.

---

## 6. Geliştirme Akışı

### Local geliştirme

```bash
git clone git@github.com:kosk-istanbul/buyukada-saatleri.git
cd buyukada-saatleri
# Hiç build adımı yok — sadece statik dosyaları aç:
python3 -m http.server 8000
# → http://localhost:8000
```

### Veri güncelleme

Vapur saatleri otomatik (GitHub Actions günlük). Manuel müdahale:

```bash
cd scrapers
pip install -r requirements.txt   # bs4, requests, playwright, pdfplumber
playwright install chromium
python sehir_hatlari.py
python mavi_marmara.py
python prens_tur.py
python merge.py
# → ../data/seferler.json güncellenir
git add data/seferler.json && git commit -m "data: refresh ferries"
git push
```

Etkinlik ekleme: `data/events.json` dosyasını editle, push et. Pages otomatik deploy.

### Yeni dil ekleme

Her HTML dosyasındaki `I18N` objesine yeni dil bloğu eklemen yeterli. Tüm 4 dosyada **aynı key seti** kullanılmalı.

---

## 7. Yol Haritası / Backlog

Devamı için fikirler (zorunlu değil):

- [ ] adalar.bel.tr için etkinlik scraper'ı (events.json otomatik güncelleme)
- [ ] PWA / offline (vapur saatleri internetsiz görüntülenebilsin)
- [ ] Push notification (son seferden önce uyarı)
- [ ] Toplu rezervasyon entegrasyonu (Heybeliada, Burgazada hatları)
- [ ] Plaj doluluk / deniz suyu sıcaklığı widget'ı
- [ ] Tur planlayıcıdan PDF export

---

## 8. Hızlı Referans

| Şey | Yer |
|---|---|
| Site URL'i | `https://kosk-istanbul.github.io/buyukada-saatleri/` (veya custom domain) |
| Repo | `github.com/kosk-istanbul/buyukada-saatleri` |
| İletişim | `hello@kosk.istanbul` |
| Hava API | `https://api.open-meteo.com` (key yok) |
| Vapur kaynakları | `sehirhatlari.istanbul`, `mavimarmara.com.tr`, `prenstur.com.tr` |
| Etkinlik kaynakları | `adalar.bel.tr`, `adalarkulturdernegi.org`, `@adalaretkinlikler` |
| Otobüs kaynakları | `iett.istanbul`, `adalaragidelim.com`, Moovit |

---

## 9. Hızlı Sanity Check

Devir tamamlandıktan sonra şunları doğrula:

1. `https://kosk-istanbul.github.io/buyukada-saatleri/` açılıyor mu?
2. SEFERLER sayfasında bugünün saatleri görünüyor mu? (Boş değilse Actions çalışıyor.)
3. Tema değiştirici çalışıyor mu? (Light/dark)
4. Dil değiştirici çalışıyor mu? (En az TR ↔ EN)
5. TUR sayfasında "Plan oluştur" butonu plan döndürüyor mu?
6. ETKİNLİKLER ve OTOBÜSLER sayfaları yükleniyor mu?
7. GitHub Actions'ın son `scrape-daily` run'ı yeşil mi?

7'si de ✅ ise devir tamam.

---

*Bu doküman repo'ya `HANDOVER.md` olarak çekilmelidir. İlerde ekibe katılan herkes ilk bunu okumalı.*
