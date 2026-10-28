/**
 * Uygulama genelindeki sabitler.
 *
 * API adresi tek bir yerden yönetilir; Docker/yerel kurulum farkı
 * VITE_API_URL ortam değişkeni ile verilir.
 */
export const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

/** Yerel depolamada kullanılan anahtarlar. */
export const STORAGE_KEYS = {
  auth: "crewintel_auth",
  settings: "crewintel_settings",
  language: "crewintel_language",
};
