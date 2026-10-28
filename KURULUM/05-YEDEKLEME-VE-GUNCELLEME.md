# 5. Adım — Yedekleme, Geri Yükleme ve Güncelleme

Verilerin değerli. **Ayda bir** (ya da her büyük değişiklikten önce) yedek al.
Yedek iki parçadan oluşur: **veritabanı** ve **belgeler**.

---

## Yedek almak

### 1) Veritabanı yedeği

`CREWINTEL` klasöründe `cmd` penceresi aç (klasörün adres çubuğuna `cmd` yazıp
Enter'a bas) ve şu komutu çalıştır:

```
docker compose exec -T postgres pg_dump -U crewintel crewintel > yedek_veritabani.sql
```

- Komut bittiğinde klasörde `yedek_veritabani.sql` dosyası oluşur.
- Dosyayı tarih ekleyerek sakla: `yedek_veritabani_2026-10-28.sql`

### 2) Belge yedeği

`storage` klasörünün tamamını kopyala (sağ tık → Kopyala → yedek klasörüne
yapıştır). İçinde yüklediğin tüm PDF/resim belgeler var.

### 3) Ayar yedeği

`.env` dosyasını da kopyala (içinde şifreler var — kimseyle paylaşma).

**Öneri:** Bu üçünü bir klasöre koy, klasörü tarihle adlandır
(`CREWINTEL_YEDEK_2026-10-28`) ve harici diske / bulut sürücüsüne kopyala.

---

## Geri yükleme (veri kaybı olduysa)

1. Programı durdur: `KURULUM\durdur.bat`
2. Programı başlat: `KURULUM\baslat.bat` (veritabanı ayağa kalksın)
3. `CREWINTEL` klasöründe `cmd` aç ve çalıştır:

```
docker compose exec -T postgres psql -U crewintel -d crewintel -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker compose exec -T postgres psql -U crewintel -d crewintel < yedek_veritabani.sql
```

4. `storage` klasörünü eski yedeğin ile değiştir.
5. `durdur.bat` + `baslat.bat` ile yeniden başlat, tarayıcıda kontrol et.

> Geri yükleme **mevcut veriyi siler** ve yedekteki hâline döndürür. Emin
> değilsen önce mevcut verinin yedeğini al.

---

## Güncelleme (yeni sürüm geldiğinde)

### GitHub'dan indirdiysen

1. Yeni sürümün ZIP'ini indir, ayrı bir klasöre çıkart.
2. Eski klasöründen **`.env`** dosyasını ve **`storage`** klasörünü yeni klasöre
   kopyala.
3. Önce yedek al (yukarıdaki adımlar).
4. Yeni klasörde `KURULUM\kur.bat` çalıştır.
5. Tarayıcıda `http://localhost:5173` → giriş → verilerin yerinde mi kontrol et.

> Eski klasörü **silme**; yeni sürüm sorun çıkarırsa ona geri dönebilirsin.

### Git ile takip ediyorsan

```
git pull
docker compose up -d --build
```

---

## Otomatik yedek (isteğe bağlı, ileri seviye)

Windows **Görev Zamanlayıcı** ile her gün 23:00'te yedek alabilirsin:

1. Bir `yedek.bat` dosyası oluştur:

   ```
   @echo off
   cd /d "C:\CREWINTEL"
   docker compose exec -T postgres pg_dump -U crewintel crewintel > "D:\YEDEK\veritabani_%DATE:~-4%-%DATE:~3,2%-%DATE:~0,2%.sql"
   ```

2. Görev Zamanlayıcı → **Temel Görev Oluştur** → Günlük → 23:00 →
   **Program başlat** → `yedek.bat`.
3. `D:\YEDEK` klasörünü önceden oluştur.

Bir sonraki dosya: **`06-MOBIL-UYGULAMA.md`**
