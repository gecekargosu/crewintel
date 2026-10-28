// CREWINTEL Mobile — i18n Configuration
// Central translation system with interpolation, fallback, and RTL support

import { SupportedLanguage, DEFAULT_LANGUAGE, Translations } from './types';
import tr from './locales/tr';
import en from './locales/en';
import ru from './locales/ru';
import ar from './locales/ar';

// Translation registry
const translations: Record<SupportedLanguage, Translations> = {
  tr,
  en,
  ru,
  ar,
};

// Current language state (will be managed by context)
let currentLanguage: SupportedLanguage = DEFAULT_LANGUAGE;

// Set current language
export function setLanguage(lang: SupportedLanguage): void {
  currentLanguage = lang;
}

// Get current language
export function getLanguage(): SupportedLanguage {
  return currentLanguage;
}

// Get translation for a key path with interpolation
// Supports: t("auth.loginTitle") or t("home.daysRemaining", { days: 5 })
export function t(key: string, params?: Record<string, string | number>): string {
  const keys = key.split('.');
  let value: any = translations[currentLanguage];

  // Navigate through nested keys
  for (const k of keys) {
    if (value && typeof value === 'object' && k in value) {
      value = value[k];
    } else {
      // Fallback to English, then Turkish, then key itself
      value = getFallbackValue(key);
      break;
    }
  }

  if (typeof value !== 'string') {
    return key; // Return key if value is not a string
  }

  // Interpolation: replace {param} with actual values
  if (params) {
    return Object.entries(params).reduce(
      (str, [paramKey, paramValue]) => str.replace(new RegExp(`\\{${paramKey}\\}`, 'g'), String(paramValue)),
      value
    );
  }

  return value;
}

// Fallback translation lookup
function getFallbackValue(key: string): string {
  const keys = key.split('.');

  // Try English fallback
  let value: any = translations.en;
  for (const k of keys) {
    if (value && typeof value === 'object' && k in value) {
      value = value[k];
    } else {
      value = undefined;
      break;
    }
  }
  if (typeof value === 'string') return value;

  // Try Turkish fallback
  value = translations.tr;
  for (const k of keys) {
    if (value && typeof value === 'object' && k in value) {
      value = value[k];
    } else {
      value = undefined;
      break;
    }
  }
  if (typeof value === 'string') return value;

  return key; // Return key as last resort
}

// Check if current language is RTL
export function isRTL(): boolean {
  return currentLanguage === 'ar';
}

// Get text direction for current language
export function getTextDirection(): 'ltr' | 'rtl' {
  return isRTL() ? 'rtl' : 'ltr';
}

// Get all supported languages
export function getSupportedLanguages() {
  return [
    { code: 'tr' as SupportedLanguage, name: 'Türkçe', flag: '🇹🇷' },
    { code: 'en' as SupportedLanguage, name: 'English', flag: '🇬🇧' },
    { code: 'ru' as SupportedLanguage, name: 'Русский', flag: '🇷🇺' },
    { code: 'ar' as SupportedLanguage, name: 'العربية', flag: '🇸🇦' },
  ];
}
