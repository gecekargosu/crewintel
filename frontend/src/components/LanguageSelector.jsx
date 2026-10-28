import { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { ChevronDown, Globe } from 'lucide-react';

const languages = [
  { code: 'tr', label: 'Türkçe', flag: '🇹🇷' },
  { code: 'en', label: 'English', flag: '🇬🇧' },
  { code: 'ru', label: 'Русский', flag: '🇷🇺' },
  { code: 'ar', label: 'العربية', flag: '🇸🇦' },
];

export default function LanguageSelector() {
  const { i18n } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  const currentLang = languages.find(l => l.code === i18n.language) || languages[0];

  const handleChange = (code) => {
    i18n.changeLanguage(code);
    localStorage.setItem('crewintel_language', code);
    if (code === 'ar') {
      document.documentElement.dir = 'rtl';
      document.documentElement.lang = 'ar';
    } else {
      document.documentElement.dir = 'ltr';
      document.documentElement.lang = code;
    }
    setIsOpen(false);
  };

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div ref={dropdownRef} style={{ position: 'relative', display: 'inline-block' }}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: 'flex', alignItems: 'center', gap: '6px',
          padding: '6px 12px', background: 'rgba(255,255,255,0.1)',
          border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px',
          color: '#fff', cursor: 'pointer', fontSize: '13px',
          transition: 'all 0.2s',
        }}
        title="Dil Seçimi"
      >
        <Globe size={14} />
        <span>{currentLang.flag}</span>
        <ChevronDown size={12} style={{ transform: isOpen ? 'rotate(180deg)' : 'rotate(0)', transition: 'transform 0.2s' }} />
      </button>
      {isOpen && (
        <div style={{
          position: 'absolute', top: '100%', right: 0, marginTop: '4px',
          background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
          zIndex: 1000, minWidth: '140px', overflow: 'hidden',
        }}>
          {languages.map(lang => (
            <button
              key={lang.code}
              onClick={() => handleChange(lang.code)}
              style={{
                display: 'flex', alignItems: 'center', gap: '8px',
                width: '100%', padding: '10px 14px',
                background: lang.code === i18n.language ? 'rgba(234,88,12,0.2)' : 'transparent',
                border: 'none', color: '#fff', cursor: 'pointer',
                fontSize: '13px', textAlign: 'left',
                transition: 'background 0.2s',
              }}
              onMouseEnter={e => e.target.style.background = 'rgba(234,88,12,0.15)'}
              onMouseLeave={e => e.target.style.background = lang.code === i18n.language ? 'rgba(234,88,12,0.2)' : 'transparent'}
            >
              <span style={{ fontSize: '16px' }}>{lang.flag}</span>
              <span>{lang.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
