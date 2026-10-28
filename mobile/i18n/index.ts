// CREWINTEL Mobile — i18n Main Export
// Central export for all i18n functionality

export { t, setLanguage, getLanguage, isRTL, getTextDirection, getSupportedLanguages } from './config';
export { SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE } from './types';
export type { SupportedLanguage, LanguageOption } from './types';

// React hook for i18n
import { useState, useCallback, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { SupportedLanguage, DEFAULT_LANGUAGE } from './types';
import { setLanguage as setI18nLanguage, t as translate, isRTL, getLanguage } from './config';

const LANGUAGE_STORAGE_KEY = '@crewintl_language';

export function useI18n() {
  const [language, setLangState] = useState<SupportedLanguage>(DEFAULT_LANGUAGE);
  const [isReady, setIsReady] = useState(false);

  // Load saved language on mount
  useEffect(() => {
    loadLanguage();
  }, []);

  const loadLanguage = async () => {
    try {
      const saved = await AsyncStorage.getItem(LANGUAGE_STORAGE_KEY);
      if (saved && ['tr', 'en', 'ru', 'ar'].includes(saved)) {
        setLangState(saved as SupportedLanguage);
        setI18nLanguage(saved as SupportedLanguage);
      }
    } catch (error) {
      console.log('Failed to load language:', error);
    } finally {
      setIsReady(true);
    }
  };

  const changeLanguage = useCallback(async (lang: SupportedLanguage) => {
    try {
      await AsyncStorage.setItem(LANGUAGE_STORAGE_KEY, lang);
      setLangState(lang);
      setI18nLanguage(lang);
    } catch (error) {
      console.log('Failed to save language:', error);
    }
  }, []);

  const t = useCallback(
    (key: string, params?: Record<string, string | number>) => {
      return translate(key, params);
    },
    [language]
  );

  return {
    language,
    changeLanguage,
    t,
    isRTL: isRTL(),
    isReady,
  };
}
