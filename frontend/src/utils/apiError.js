import i18n from "../i18n";

/**
 * Sunucu hatasını kullanıcıya gösterilecek metne çevirir.
 *
 * Backend'in `detail` mesajları yalnızca Türkçe üretilir. Arayüz başka bir
 * dilde kullanılıyorsa kullanıcıya ham Türkçe metin göstermek yerine
 * çevrilmiş genel mesaj (fallbackKey) döndürülür. Teknik ayrıntı konsola
 * yazılır, böylece geliştirme sırasında kaybolmaz.
 */
export function apiErrorMessage(error, t, fallbackKey = "errors.generic") {
  const detail = error?.response?.data?.detail;

  if (typeof detail === "string" && detail.trim() && i18n.language === "tr") {
    return detail;
  }

  if (error?.response?.status === undefined) {
    return t("errors.network");
  }

  return t(fallbackKey);
}
