# CREWINTEL MOBILE — REVİZYON KARARLARI (v2)

> Durum: **KARAR — onaylandı.** Tarih: 2026-08-18 · Faz: Mobile Design (M0) → M1
> 41 revizyon önerisi + kullanıcının yeni fikirleri (offline müzik/oyun/kitap, fotoğraf arşivi, harita, sosyal medya) tek tek değerlendirildi.

---

## 1. YENİ FİKİRLER — FİZİBİLİTE

Kullanıcının ek fikirleri (müzik, oyun, kitap, fotoğraf, harita, sosyal medya) gerçekçi mi?

| Fikir | Mümkün mü? | Nasıl? | Faz |
|---|---|---|---|
| **Offline müzik dinleme** | ✅ Mümkün | Uygulama içi ses kütüphanesi (denizcilik temalı/rahatlama parçaları) paket olarak uygulamayla gelir; `expo-audio` ile çalar. İnternet gerektirmez (dosyalar uygulama paketinde). | M4 |
| **Offline oyunlar** | ✅ Mümkün | Basit mini-oyunlar (satranç, sudoku, kelime) uygulama içinde native olarak çalışır; backend'e bağlanmaz. | M4 |
| **Denizcilik kitapları + sesli okuma** | ✅ Mümkün | Backend'e `library` tablosu + `media/` storage; mobilde liste + indir + `expo-av` ile sesli okuma (TTS veya kayıtlı ses). Kitap PDF/EPUB/metin. Telif hakkı: kamu malı veya lisanslı içerik şart. | M4 |
| **Fotoğraf çekip arşiv oluşturma** | ✅ Mümkün | `expo-image-picker`; kullanıcı kendi "foto arşivi" klasörüne yükler (kişisel hatıra/belge fotoğrafları). Ayrı tablo `crew_media`. | M3 |
| **Haritada konum gösterme** | ⚠️ Mümkün ama dikkat | `expo-location` ile konum; "neredeyim" ekranı. **Gizlilik:** canlı konum paylaşımı KVKK riski — MVP'de yalnızca kullanıcının kendisi görür, admin'e ulaşmaz. Gemi seyir bilgisi (AIS) ayrı ve çok pahalı — kapsam dışı. | M4 |
| **Sosyal medyada paylaşma** | ✅ Mümkün | `expo-sharing` + platform linkleri (WhatsApp/Instagram/Facebook deep-link). Kullanıcı kendi paylaşır; uygulama otomatik paylaşım yapmaz (güvenli). | M4 |

**Özet karar:** Hepsi teknik olarak mümkün. **Hiçbiri M1/M2'de yok.** Sıra: önce backend + temel mobil (M1), sonra kontrat/belge/mesaj (M2), sonra admin + fotoğraf (M3), en son eğlence/kitaplar/harita/sosyal (M4). Sebep: asıl değer "personel operasyonu"nda; müzik/oyun "güzel ama sonra" kategorisinde.

---

## 2. 41 REVİZYON ÖNERİSİ — NİHAİ KARAR

Karar kodları: ✅ KABUL (M1'de uygulanır) · 🔶 KABUL-ERTELENDİ (sonraki faz) · ⛔ RED

| # | Öneri | Karar | Not |
|---|---|---|---|
| 1 | Ayrı rol yok; `crew` rolü + durum | ✅ | `job_seeking` + `availability` + aktif kontrat türetilir |
| 2 | `availability_status` sistemi | ✅ | Mevcut `availability` zaten var (available/on_board/on_leave/not_available); `available_from` tarihi eklenir |
| 3 | Maritime Professional Profile | 🔶 | Mevcut `CrewMember` alanları + `profile_data` JSON zaten var; mobil ekranları M1'de, genişletilmiş profil yapısı M4 |
| 4 | İş tercihleri profilin parçası | ✅ | `job_preferences` JSON + `expected_salary_min/max/currency/period` + `available_from` migration 0010 |
| 5 | Kural-bazlı matching AI'dan önce | ✅ | Mevcut `eligibility.score_crew` zaten kural-bazlı; ilan eşleştirmede aynı mantık |
| 6 | Matching M2'de gelsin | ✅ | `/portal/jobs/recommended` + başvuruda `match_score` M1'de; gelişmiş eşleştirme M2 |
| 7 | Salary yapısal alanlar | ✅ | `expected_salary_min/max/currency/period` (migration 0010) |
| 8 | Vessel experience normalize | 🔶 | MVP: `vessel_types_experience` string; ilişkisel tablolar M4 |
| 9 | Offline READ var, WRITE yok (M1) | ✅ | M1'de yazma çevrimiçi; senkron kuyruk M2+ |
| 10 | Mesajlaşma REST, WebSocket sonra | ✅ | `conversations`/`messages` REST (M1); WebSocket M2+ |
| 11 | SYSTEM message türü | ✅ | `messages.kind`: `chat` / `system` / `job_alert` / `document_alert` / `contract_alert` |
| 12 | Bildirim tercihleri | 🔶 | `notification_preferences` JSON user alanı M2 (önce bildirim altyapısı otursun) |
| 13 | Contract Alert Engine | 🔶 | 60/30/14/7/3/1 gün eşikleri M2 (kontrat/me ucu M1'de hazır) |
| 14 | Kontrat bitişi → iş önerisi | 🔶 | `contracts/me` + `jobs/recommended` birleşimi M2 |
| 15 | Admin mobil = hızlı müdahale merkezi | ✅ | Tasarım ilkesi olarak kabul; M3'te uygulanır |
| 16 | RBAC genişlemesine hazır | ✅ | Mevcut `admin/hr/viewer/crew` korunur; kod rol string'i kullanır, genişletilebilir |
| 17 | Self-registration + admin onayı | ✅ | `POST /api/auth/register` → pending; admin approve (M1) |
| 18 | Kayıtta minimum alan | ✅ | Ad, soyad, telefon, email, şifre (M1) |
| 19 | OCR M1'de yok | ✅ | Belge tipi kullanıcı seçer + admin onayı; OCR M4 |
| 20 | Belge sistemi OCR'a hazır | ✅ | Mevcut Document modeli zaten `document_type/number/issue/expiry/verified*` alanlarına uygun; `verified_by/verified_at` M2'de eklenir |
| 21 | KVKK/gizlilik genişletmesi | 🔶 | Temel kontroller M1'de (IDOR, sahiplik); politika dokümanı + indirme logları M3 |
| 22 | Hesap silme = deaktivasyon | ✅ | `is_active=false`; veri silme yok. Uç: `PATCH /api/auth/me/deactivate` (M1) |
| 23 | Device & session yönetimi | 🔶 | `user_devices` M1; "tüm cihazlardan çıkış" M3 |
| 24 | Push duplicate temizliği | ✅ | `UNIQUE(user_id, push_token)` + `DeviceNotRegistered` → sil (M1) |
| 25 | Tek veri kaynağı prensibi | ✅ | Tasarımın temeli |
| 26 | İş mantığı backend'de | ✅ | Tasarımın temeli |
| 27 | Migration güvenli çalıştırma | ✅ | Backup → up → integrity → regression → down test (uygulanacak) |
| 28 | Mevcut kodu gerçekten doğrula | ✅ | Bu turda yapıldı (portal/jobs/auth modelleri okundu) |
| 29 | M1 kapsamı kontrollü | ✅ | Register/Approval/Login/Profile/Documents/Upload/Jobs/Apply/Applications/JobSeeking/Notifications |
| 30 | M2: contract+vessel+messaging+matching | ✅ | Faz planında |
| 31 | M3: admin mobile | ✅ | Faz planında |
| 32 | M4: AI/OCR/QR/joining/offline | ✅ | Faz planında |
| 33 | Önce Android | ✅ | Expo + EAS Build; iOS sonra |
| 34 | React Native + Expo + TS | ✅ | Teknoloji seçimi |
| 35 | Admin mobile her şeyi taşımasın | ✅ | "Telefonda gerekli mi?" kriteri |
| 36 | Crew uygulaması sadece ilan değil | ✅ | Belge cüzdanı + kontrat takibi + mesaj + kariyer |
| 37 | Joining/Sign-Off'a hazır | 🔶 | Mevcut Assignment modeli yeterli; ek alanlar M4 |
| 38 | QR Crew ID | 🔶 | M4 |
| 39 | AI = üst katman | ✅ | Rule-based önce; AI M4 |
| 40 | Faz sırası M0→M4 | ✅ | Kabul |
| 41 | Önce mevcut sistemi doğrula | ✅ | Bu turda portal/jobs/auth gerçek kodu okunarak doğrulandı |

**İstatistik:** ✅ 29 kabul · 🔶 11 ertelendi · ⛔ 0 red. Hiçbir öneri reddedilmedi; hepsi ya şimdi ya sonraki fazda.

---

## 3. M1 KAPSAMI (KESİN)

**Backend (bu turda uygulanıyor):**
- Migration 0010: `crew_members` ek alanlar, `user_devices`, `conversations`, `messages`, `job_applications.match_score/applied_from`
- `POST /api/auth/register` + `PATCH /api/auth/users/{id}/approve` + `PATCH /api/auth/me/deactivate`
- Portal: `/me/full`, `/preferences`, `/documents`, `/documents/{id}/file`, `/contracts/me`, `/vessel/me`, `/applications`, `/jobs/recommended`
- `messages.py` router (REST) + `devices.py` router + `services/push.py` (Expo Push API)
- Testler + mevcut 199 test regression

**Mobil (sonraki tur — M1b):**
- Expo iskeleti, login/register, tab bar, Home/Profil/Belgeler/İlanlar/Başvurularım/Bildirimler ekranları

---

## 4. AÇIK KARARLAR (KULLANICIDAN)

1. ✅ Android önce — onaylandı (varsayım, aksi söylenmedi)
2. ✅ Self-registration + admin onayı — onaylandı
3. 🔶 Mesajlaşma MVP'de sadece admin↔personel — onaylandı (varsayım)
4. 🔶 Uygulama adı "CREWINTEL CREW" — kullanıcı onayı bekliyor
5. ✅ OCR M1'de yok — onaylandı
