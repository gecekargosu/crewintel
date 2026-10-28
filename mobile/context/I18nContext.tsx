import React, { createContext, useContext, useEffect, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { SupportedLanguage, DEFAULT_LANGUAGE } from '../i18n/types';
import { setLanguage as setI18nLanguage, t as translate, isRTL } from '../i18n/config';

const LANGUAGE_STORAGE_KEY = '@crewintl_language';

interface I18nContextType {
  language: SupportedLanguage;
  changeLanguage: (lang: SupportedLanguage) => Promise<void>;
  t: (key: string, params?: Record<string, string | number>) => string;
  isRTL: boolean;
  isReady: boolean;
}

const I18nContext = createContext<I18nContextType>({
  language: DEFAULT_LANGUAGE,
  changeLanguage: async () => {},
  t: (key) => key,
  isRTL: false,
  isReady: false,
});

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguage] = useState<SupportedLanguage>(DEFAULT_LANGUAGE);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    loadLanguage();
  }, []);

  const loadLanguage = async () => {
    try {
      const saved = await AsyncStorage.getItem(LANGUAGE_STORAGE_KEY);
      if (saved && ['tr', 'en', 'ru', 'ar'].includes(saved)) {
        setLanguage(saved as SupportedLanguage);
        setI18nLanguage(saved as SupportedLanguage);
      }
    } catch (error) {
      console.log('Failed to load language:', error);
    } finally {
      setIsReady(true);
    }
  };

  const changeLanguage = async (lang: SupportedLanguage) => {
    try {
      await AsyncStorage.setItem(LANGUAGE_STORAGE_KEY, lang);
      setLanguage(lang);
      setI18nLanguage(lang);
    } catch (error) {
      console.log('Failed to save language:', error);
    }
  };

  const t = (key: string, params?: Record<string, string | number>) => {
    return translate(key, params);
  };

  return (
    <I18nContext.Provider
      value={{
        language,
        changeLanguage,
        t,
        isRTL: isRTL(),
        isReady,
      }}
    >
      {children}
    </I18nContext.Provider>
  );
}

export const useI18n = () => useContext(I18nContext);
