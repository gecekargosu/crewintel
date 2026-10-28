# DIŞ ENTEGRASYONLAR

## WhatsApp Business API — ALTYAPI HAZIR (CONFIGURATION REQUIRED)

Kullanıcı token/Phone ID'yi **Ayarlar → Bildirim Ayarları**'ndan girecek; kod değişikliği gerekmez.

| Öğe | Durum |
|---|---|
| Kuyruk tablosu (whatsapp_messages) + retry + duplicate koruması | ✅ |
| Graph API send_text (v21.0, httpx) | ✅ |
| Webhook verify (GET /api/webhooks/whatsapp — Meta `hub.*` parametreleri) | ✅ canlı doğrulandı |
| Webhook receive (POST — mesaj alımı, loglama) | ✅ |
| Telefon normalizasyonu (+90 5XX → 905XX) | ✅ |
| Token DB'de masked, frontend'e/loglara yazılmaz | ✅ |
| Meta template mesaj gereksinimi (toplu gönderim) | ⚠️ kuyruk hazır; şablon ID eşlemesi ileride |
| WhatsApp'tan belge alma → personel eşleşme → pending_approval | 🔜 sonraki faz (webhook altyapısı hazır) |
| Gerçek gönderim | ❌ token yok — sahte başarı üretilmez (publication `queued`) |

**Meta panelinde webhook adresi:** `https://{PUBLIC_BACKEND}/api/webhooks/whatsapp`
Verify token: Ayarlar'dan girilen `whatsapp_webhook_verify_token`.

## SMTP E-posta

- Kuyruk hazır (`send-bulk` / `send-one`).
- SMTP ayarı girilmeden mesajlar `pending` kalır, crash olmaz.
- Ayar girilince gerçek gönderim başlar.

## Instagram / Facebook

- **CONFIGURATION REQUIRED:** `instagram_access_token`/`page_id` ve
  `facebook_access_token`/`page_id` ayarları tanımlı değil.
- Yayın kanalı seçilirse `skipped` + açıklayıcı hata döner (sahte başarı yok).
- Meta Graph API üzerinden otomatik paylaşım için bu tokenların girilmesi gerekir.

## Public Erişim (Cloudflare Quick Tunnel)

- Frontend: `https://want-recently-schema-tuner.trycloudflare.com`
- Backend:  `https://centered-compression-sci-font.trycloudflare.com`
- ⚠️ TryCloudflare URL'leri **geçicidir** (tünel prosesi kapanırsa link değişir).
  Eski `suspension-niagara-...` linki bu yüzden ölmüştür (tünel kapanmış, DNS çözülmüyor).
- Kalıcı çözüm: domain + Cloudflare Named Tunnel veya nginx + Let's Encrypt (kullanıcı onayı bekler).
