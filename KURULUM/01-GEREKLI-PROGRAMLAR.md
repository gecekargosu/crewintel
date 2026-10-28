# 1. Adım — İndirilmesi Gereken Programlar

Aşağıdaki programları **sırayla** kur. Kurulum sırasında "İleri / Next" demen
yeterli; ayarları değiştirmene gerek yok.

## Zorunlu programlar

### 1) Docker Desktop (programın çalışması için gerekli)

Docker, programın veritabanını ve sunucusunu senin bilgisayarında çalıştırır.

- İndirme adresi: <https://www.docker.com/products/docker-desktop/>
- Sayfada **"Download for Windows"** (Windows için indir) düğmesine bas.
- İnen dosya (ör. `Docker Desktop Installer.exe`) çift tıkla.
- Kurulumda **"Use WSL 2 instead of Hyper-V"** seçeneği işaretli kalsın.
- Kurulum bitince **"Close and restart"** (kapat ve yeniden başlat) de.
- Bilgisayar açılınca Docker Desktop'ı **başlat** (Başlat menüsünden).
- Alt görev çubuğunda **balina ikonu** görünmeli. İlk açılışta lisans sözleşmesi
  ve "sign in" ekranı çıkabilir: **"Skip" / "Continue without signing in"**
  diyerek geçebilirsin. Ücretsiz sürüm bu program için yeterlidir.

> Docker Desktop'ın çalışması için bilgisayarda **Hyper-V / WSL2** açık olmalı.
> Kurulum sana "WSL update is required" derse, ekranda çıkan bağlantıdan
> `wsl_update_x64.msi` dosyasını indirip kur, bilgisayarı yeniden başlat.

### 2) Google Chrome veya Microsoft Edge (tarayıcı)

Program tarayıcıda açılır. Windows'ta Edge zaten yüklüdür; Chrome tercih edersen:
<https://www.google.com/chrome/>

## İsteğe bağlı programlar

### 3) Git (projeyi GitHub'dan indirmek için)

Git, projeyi GitHub'dan indirmeni ve güncellemeni sağlar. GitHub'dan **ZIP**
olarak indireceksen buna gerek yok.

- İndirme adresi: <https://git-scm.com/download/win>
- Kurulumda tüm ayarlar varsayılan kalabilir.

### 4) Node.js (yalnızca mobil uygulamayı çalıştıracaksan)

- İndirme adresi: <https://nodejs.org/> → **LTS** sürümü.
- Masaüstü programı Node.js olmadan da çalışır.

### 5) Notepad++ (isteğe bağlı, dosya düzenlemek için)

`.env` gibi ayar dosyalarını düzenlemek kolaylaşır: <https://notepad-plus-plus.org/>

## Disk ve sistem gereksinimleri

| Gereksinim | En az | Önerilen |
|---|---|---|
| İşletim sistemi | Windows 10 (64 bit) | Windows 11 |
| RAM | 8 GB | 16 GB |
| Boş disk alanı | 10 GB | 20 GB |
| İşlemci | 2 çekirdek | 4 çekirdek |

## Kontrol

Kurulumdan sonra şunları kontrol et:

1. Başlat menüsüne `cmd` yaz, **Komut İstemi**'ni aç.
2. Şu komutu yaz ve Enter'a bas:

   ```
   docker --version
   ```

3. `Docker version 27.x.x` gibi bir satır görüyorsan tamam.
4. `'docker' is not recognized` yazıyorsa Docker kurulmamış veya bilgisayarı
   yeniden başlatmamışsın demektir.

Bir sonraki dosya: **`02-KURULUM-ADIM-ADIM.md`**
