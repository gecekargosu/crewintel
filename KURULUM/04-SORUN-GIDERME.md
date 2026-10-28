# 4. Adım — Sorun Giderme (Sorunlar ve Cevapları)

Bu dosyada **en sık karşılaşılan** sorunlar ve çözümleri var. Önce buradaki
başlığa bak, yoksa en altta "Başka bir sorun" kısmını oku.

> Her şeyden önce iki şeyi dene:
> 1. Bilgisayarı yeniden başlat.
> 2. `KURULUM\baslat.bat` dosyasına çift tıkla ve 2 dakika bekle.

---

## "Docker bulunamadı" / `'docker' is not recognized`

- Docker Desktop kurulu değil ya da kurulumdan sonra bilgisayar yeniden
  başlatılmamış.
- Docker Desktop'ı kur → bilgisayarı yeniden başlat → Başlat menüsünden
  **Docker Desktop**'ı aç → balina ikonu yeşile dönene kadar bekle → tekrar dene.

## "Docker Desktop kapalı görünüyor"

- Balina ikonu sağ alttaki gizli simgelerde olabilir; üzerine tıkla →
  **Start**. "Engine running" yazana kadar bekle.
- Bilgisayar açıldığında Docker kendiliğinden açılsın istersen: Docker Desktop →
  **Settings** → **General** → **Start Docker Desktop when you sign in**
  işaretle.

## Docker açılıyor ama "WSL update is required" diyor

- Ekranda verilen bağlantıdan `wsl_update_x64.msi` indir, kur, yeniden başlat.
- Ya da Komut İstemi'nde (yönetici) şu komutu çalıştır: `wsl --update`

## "port is already allocated" / port hatası (5173, 8000 veya 5433 dolu)

Başka bir program o portu kullanıyor (ör. başka bir Docker projesi, Skype, yerel
PostgreSQL).

1. `KURULUM\sorun-raporu.bat` çalıştır → `sorun-raporu.txt` içindeki **PORTLAR**
   bölümüne bak; hangi PID'in tuttuğunu görürsün.
2. O programı kapat (ya da bilgisayarı yeniden başlat).
3. `baslat.bat` ile tekrar dene.

## Tarayıcı açılıyor ama sayfa boş / "bağlantı kurulamadı"

- İlk kurulumda arayüz derlenmesi **5–15 dakika** sürebilir. Bekle.
- Kontrol: `KURULUM` klasöründe `cmd` aç → `docker compose ps`
  Üç satırın da `running` olması gerekir. Değilse `sorun-raporu.bat` çalıştır.

## Giriş yapamıyorum: "E-posta veya şifre hatalı"

- `.env` dosyasındaki `ADMIN_EMAIL` / `ADMIN_PASSWORD` değerlerini kontrol et
  (Not Defteri ile aç). Başında/sonunda boşluk olmasın.
- Yönetici hesabı **sadece ilk kurulumda** oluşturulur. Sonradan `.env`'deki
  şifreyi değiştirmek mevcut şifreyi değiştirmez; bunun için aşağıdaki
  "Şifremi unuttum" bölümünü kullan.

## Şifremi unuttum

`KURULUM` klasöründe `cmd` penceresi aç ve sırayla çalıştır:

```
docker compose exec -T backend python -c "from app.db.database import SessionLocal; from app.models.user import User; from app.core.security import hash_password; db=SessionLocal(); u=db.query(User).filter(User.role=='admin').first(); u.password_hash=hash_password('YeniSifre123!'); db.commit(); print('Yeni sifre: YeniSifre123!')"
```

Sonra `YeniSifre123!` ile gir ve **Ayarlar → Şifre Değiştir** ile kendi
şifreni belirle.

## "Çok fazla hatalı giriş denemesi" (5 dakika bekle diyor)

Güvenlik kilidi. **5 dakika** bekle, sonra tekrar dene. Ya da programı
`durdur.bat` + `baslat.bat` ile yeniden başlat (kilit sıfırlanır).

## Belge yüklenmiyor

| Hata | Sebep / çözüm |
|---|---|
| "Desteklenmeyen dosya türü" | Yalnızca PDF ve TXT kabul edilir. Resim/Word/Excel dosyasını PDF'e çevirip yükle. |
| "Dosya çok büyük" | 25 MB sınırı. PDF'i küçült (ör. ilkonline pdf sıkıştır) veya tara. |
| "Aynı dosya zaten yüklü" | Aynı belge daha önce yüklenmiş. Belgeler listesinden bulabilirsin. |
| Yükleme bitti ama listede yok | Sayfayı yenile (F5). Hâlâ yoksa `sorun-raporu.bat` çalıştır. |

## Belge "onay bekliyor"da kaldı

Personelin kendi yüklediği belgeler yönetici onayı bekler. **Belgeler** ekranında
ilgili satırdaki **Onayla** düğmesine bas.

## Türkçe karakterler bozuk görünüyor (ÅŸ, Ã¼ gibi)

- Tarayıcıda sayfayı yenile. Sorun sürüyorsa belge dosyası UTF-8 değildir;
  Not Defteri → **Farklı Kaydet** → Kodlama: **UTF-8**.
- Excel'den alınan CSV'lerde bu sık görülür.

## Program çok yavaş

- Docker Desktop'a **Settings → Resources** üzerinden en az **4 GB RAM** ver.
- Gereksiz programları kapat.
- İlk açılış her zaman yavaştır; sonraki açılışlar hızlıdır.

## Bilgisayarı kapattım, veriler gitti mi?

Hayır. Veriler `crewintel_crewintel_postgres_data` adlı Docker alanında ve
`storage` klasöründe durur; bilgisayar kapansa da silinmez. Silinmesi için
`sifirdan-kur.bat` çalıştırman gerekir.

> **Önemli:** Bu alanı Docker Desktop → **Volumes** ekranından **elle silme**.
> Silersen tüm veriler gider.

## "Windows protected your PC" uyarısı

`.bat` dosyaları imzasız olduğu için çıkar. **More info** → **Run anyway**.

## Antivirüs `.bat` dosyasını sildi

- Windows Defender → **Virüs ve tehdit koruması** → **Ayarları yönet** →
  **Dışlamalar** → **Dışlama ekle** → `CREWINTEL` klasörünü seç.
- Program internete veri göndermez; dosyalar sadece kendi bilgisayarında
  çalışır.

## Masaüstünde kısayol istiyorum

`baslat.bat` dosyasına sağ tıkla → **Kısayol oluştur** → kısayolu masaüstüne
sürükle → adını **CREWINTEL** yap. Sağ tık → **Özellikler** → **Simge Değiştir**
ile simge seçebilirsin.

---

## Program bir türlü açılmıyor, logda "Can't locate revision" yazıyor

Bu, veritabanının kodda bulunmayan bir sürüm kaydına işaret ettiği anlamına
gelebilir. `CREWINTEL` klasöründe `cmd` aç ve şu komutu çalıştır:

```
docker compose exec -T postgres psql -U crewintel -d crewintel -c "update alembic_version set version_num='20260818_0010';"
docker compose up -d backend
```

Sonra `baslat.bat` ile programı aç. (Bu işlem verileri silmez; yalnızca sürüm
kaydını düzeltir.)

---

## Başka bir sorun varsa

1. `KURULUM\sorun-raporu.bat` dosyasına çift tıkla.
2. Oluşan `sorun-raporu.txt` dosyasını kaydet.
3. O dosyayı, **ne yaparken** hata aldığını bir cümleyle yazarak teknik desteğe
   gönder. (Dosyada şifre yoktur.)

Bir sonraki dosya: **`05-YEDEKLEME-VE-GUNCELLEME.md`**
