import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import tr from './locales/tr';
import en from './locales/en';
import ru from './locales/ru';
import ar from './locales/ar';

const savedLang = localStorage.getItem('crewintel_language');
const browserLang = navigator.language.split('-')[0];
const supportedLangs = ['tr', 'en', 'ru', 'ar'];

let defaultLang = 'tr';
if (savedLang && supportedLangs.includes(savedLang)) {
  defaultLang = savedLang;
} else if (supportedLangs.includes(browserLang)) {
  defaultLang = browserLang;
}

i18n
  .use(initReactI18next)
  .init({
    resources: {
      tr: { translation: tr },
      en: { translation: en },
      ru: { translation: ru },
      ar: { translation: ar },
    },
    lng: defaultLang,
    fallbackLng: 'tr',
    interpolation: {
      escapeValue: false,
    },
    react: {
      useSuspense: false,
    },
  });

// RTL desteği
const rtlLanguages = ['ar'];
const applyDirection = (lng: string) => {
  const dir = rtlLanguages.includes(lng) ? 'rtl' : 'ltr';
  document.documentElement.dir = dir;
  document.documentElement.lang = lng;
  if (dir === 'rtl') {
    document.body.classList.add('rtl');
    document.body.classList.remove('ltr');
  } else {
    document.body.classList.add('ltr');
    document.body.classList.remove('rtl');
  }
};

// İlk yüklemede uygula
applyDirection(defaultLang);

// Dil değişikliğinde uygula
i18n.on('languageChanged', (lng) => {
  applyDirection(lng);
});

export default i18n;
