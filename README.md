
# Enfeksiyon Hasta Takip Uygulaması

PyQt5 ile geliştirilen, pediatrik/erişkin enfeksiyon vakalarında **hasta kartı**, **mikrobiyoloji sonuçları**, **ilaç kullanımı**, **laboratuvar değerleri** ve ayrıntılı **klinik anket (klinik gözlem)** kaydı tutmaya yarayan masaüstü uygulaması.

Veriler yerel **SQLite** veritabanında (`hastatakip.db`) saklanır; ilk çalıştırmada otomatik oluşur.

---

## 🚀 Hızlı Başlangıç (Windows – tek dosya EXE)

**İndir:** [enf_hts.exe](https://github.com/SelinElifGur/enfeksiyon/releases/latest/download/enfeksiyon.exe)

!!! İndirme açılmazsa, depo içindeki `dist/enfeksiyon.exe` yolundan da indirebilirsiniz.

1. Dosyayı indirin ve **çift tıklayın**.  
2. Windows SmartScreen uyarısı çıkarsa: **"Ek Bilgi” → “Yine de çalıştır”**.  
3. Veriler, uygulama klasöründeki `hastatakip.db` dosyasında tutulur. **Yedeklemek** için bu dosyayı kopyalamanız yeterli.

---

## ⭐ Başlıca Özellikler

- **Hasta Yönetimi:** Ekle / güncelle / sil, TC–Ad–Soyad ile arama  
- **Detay Penceresi**
  - **Mikrobiyoloji:** Kültür örneği, bakteri, üreme tarihi
  - **Antibiyogram:** Antibiyotik–sonuç takibi
  - **İlaçlar:** Ad, başlangıç–bitiş tarihleri, dozaj
  - **Laboratuvar:** CRP, lökosit, nötrofil, PCT, biyokimya vb.
  - **Anket:** Kapsamlı öykü & muayene formu + serbest metin **Klinik Gözlem** alanı
- **Kolay Yedekleme:** Tek dosyalı SQLite veritabanı (`hastatakip.db`)

---

## 🔒 Veri & Gizlilik

- Tüm veriler **yalnızca yerel makinenizdeki** `hastatakip.db` dosyasında saklanır.  
- Kurumsal kullanımda dosyayı **düzenli yedeklemeniz** önerilir.

---

## 🧪 Kaynaktan Çalıştırma

Depoyu klonlayıp Python ile çalıştırmak için:

```bash
git clone https://github.com/SelinElifGur/enfeksiyon.git
cd enfeksiyon
python enfeksiyon.py
```
---

## Geri Bildirim & Katkı

Hata bildirimi ve öneriler için Issues sekmesini kullanabilirsiniz. 




