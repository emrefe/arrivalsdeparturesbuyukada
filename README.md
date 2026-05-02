# Büyükada Saatleri

Büyükada'ya gelen ve Büyükada'dan giden tüm vapur ve motor seferleri tek listede — kronolojik sıralı, sonraki 3 saat penceresinde.

Veri kaynakları: Şehir Hatları, Mavi Marmara, Prens Tur.

---

## Bu klasörde ne var

```
buyukada-saatleri/
├── index.html              ← Web sayfası (tek dosya, tarayıcıda direkt açılır)
├── data/
│   └── seferler.json       ← Tüm seferlerin veritabanı
├── scrapers/               ← Veriyi üreten Python scriptleri
│   ├── common.py           ← Ortak yardımcılar (veri modeli, iskele isim normalizasyonu)
│   ├── sehirhatlari.py     ← Şehir Hatları scraper
│   ├── mavimarmara.py      ← Mavi Marmara scraper
│   ├── prenstur.py         ← Prens Tur scraper
│   ├── run_all.py          ← Hepsini çalıştırıp seferler.json'a yazan script
│   └── requirements.txt    ← Python bağımlılıkları
├── .github/workflows/
│   └── scrape.yml          ← Günde 1 kere otomatik scrape (GitHub Actions)
└── README.md               ← Bu dosya
```

## Nasıl çalışıyor

1. Her gün GitHub Actions üç scraper'ı çalıştırır.
2. Üç sitedeki seferler `data/seferler.json` dosyasında birleştirilir.
3. `index.html` bu JSON'u okuyup şu anki saatten itibaren 3 saatlik pencerede sıralı gösterir.
4. Sayfa GitHub Pages'te yayınlanır — ücretsiz.

Önemli: **Şu an scraper'lar fallback (elden derlenmiş) tarifeyle çalışıyor.** Yani kabaca doğru ama gerçek-zamanlı değil. Gerçek scrape'i ilk GitHub Actions çalıştırmasında loglardan görüp rafine edeceğiz.

---

## Adım adım yayına alma

Aşağıdaki tüm adımlar tarayıcıdan yapılabilir, terminal/komut satırı GEREKMEZ.

### 1. GitHub hesabı

Hesabın yoksa: https://github.com/signup — bedava hesap aç. Kullanıcı adı seç, e-posta doğrula. 1 dakika sürer.

### 2. Yeni repository oluştur

1. GitHub'a giriş yap.
2. Sağ üstteki **+** butonuna tıkla → **New repository**.
3. Repository name: `buyukada-saatleri` (istediğin başka bir isim de olabilir).
4. Public seçili olsun.
5. **Add a README file** kutusunu **işaretleme** (zaten kendi README'miz var).
6. **Create repository** butonuna bas.

### 3. Dosyaları yükle

1. Yeni açılan boş repo sayfasında **uploading an existing file** linkine tıkla.
2. Bu klasörün içindeki tüm dosyaları (index.html, data/, scrapers/, .github/, README.md) seç ve sürükle-bırak ile yükle.
   - **Önemli:** klasör yapısının korunması lazım. Eğer GitHub klasörleri yüklemezse, her klasör için ayrı ayrı upload yapman gerekir.
3. En altta commit message'a bir şey yaz (`ilk yükleme` gibi) ve **Commit changes** bas.

### 4. GitHub Actions'ı çalıştır

Dosyalar yüklendikten sonra:
1. Repo'da üst tarafta **Actions** sekmesine tıkla.
2. **Sefer Saatlerini Güncelle** workflow'unu seç.
3. Sağdan **Run workflow** → **Run workflow** bas.
4. Bir-iki dakika bekle. Yeşil tik gelirse `data/seferler.json` güncellendi demektir.

Eğer kırmızı X görürsen, içine gir, log'lara bak — bana mesajı yapıştır, ben düzeltirim.

### 5. GitHub Pages'i aç

1. Repo'da **Settings** sekmesine tıkla.
2. Sol menüden **Pages**.
3. **Source** kısmında **Deploy from a branch** seçili olsun.
4. **Branch** olarak `main`, klasör olarak `/ (root)` seç. **Save** bas.
5. Bir-iki dakika sonra üstte yeşil bir kutuda site adresin görünür: `https://kullanici-adin.github.io/buyukada-saatleri/`

Bu adres senin projendir. Tarayıcıdan aç, çalıştığını gör.

### 6. (İsteğe bağlı) Kendi alan adını bağla

İstersen `buyukadasaatleri.com` gibi bir alan adı alıp buraya bağlayabilirsin (~12 USD/yıl).
- Namecheap, Cloudflare gibi bir registrar'dan domain al.
- GitHub Pages **Settings → Pages → Custom domain** kısmına yaz.
- Registrar tarafında DNS'te bir CNAME kaydı eklersin (GitHub yönergeleri sayfada gösterir).

Bunu sonraya bırakabiliriz. İlk önce GitHub Pages adresinde çalışsın, beğenirsen domain bağlarız.

---

## Veri akışı (özet)

```
Günde 1 kere (Türkiye 04:00):
  GitHub Actions → run_all.py → 3 scraper → data/seferler.json (commit)

Her ziyaretçi:
  index.html → fetch(seferler.json) → şimdi+3 saat filtresi → liste
```

Sayfa kendi kendine 30 saniyede bir tazelenip "şu an"ı ve "X dk sonra" değerlerini günceller. Ana veri günde 1 kere değişir.

---

## Lokalde test (opsiyonel — sadece Python kuruluysa)

```bash
cd scrapers
pip install -r requirements.txt
python run_all.py
# data/seferler.json güncellenir.
# Sonra ana klasörde index.html'i tarayıcıda aç.
```

Lokalde fetch güvenlik kısıtlaması yüzünden direkt dosya açınca JSON yüklenmeyebilir.
Bu durumda klasörde basit bir HTTP server çalıştır:
```bash
python -m http.server 8000
# tarayıcıdan: http://localhost:8000
```

---

## Yapılacaklar / İyileştirmeler

- [ ] Şehir Hatları için gerçek HTML parse'ı (şu an fallback)
- [ ] Mavi Marmara için ara durakları (Heybeli) parse'tan çıkarmak
- [ ] Prens Tur için gerçek tablo parse'ı
- [ ] Hafta içi / hafta sonu / yaz tarifesi ayrımı
- [ ] Bilet fiyatları
- [ ] Sefer iptali / aksaklık bilgisi (Şehir Hatları "duyurular" sayfasından)
- [ ] PWA / offline destek
- [ ] Tema (açık/koyu) manuel seçim

## Lisans

İstediğin gibi kullan. Sefer saatleri verisi ilgili operatörlere aittir, bu proje sadece bunları derler.
