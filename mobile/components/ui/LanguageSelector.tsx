import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Modal } from 'react-native';
import { useTheme } from '../../hooks/useTheme';
import { SupportedLanguage } from '../../i18n/types';

interface LanguageOption {
  code: SupportedLanguage;
  name: string;
  nativeName: string;
  flag: string;
}

interface LanguageSelectorProps {
  visible: boolean;
  currentLanguage: SupportedLanguage;
  onSelect: (lang: SupportedLanguage) => void;
  onClose: () => void;
}

const LANGUAGES: LanguageOption[] = [
  { code: 'tr', name: 'Turkish', nativeName: 'Türkçe', flag: '🇹🇷' },
  { code: 'en', name: 'English', nativeName: 'English', flag: '🇬🇧' },
  { code: 'ru', name: 'Russian', nativeName: 'Русский', flag: '🇷🇺' },
  { code: 'ar', name: 'Arabic', nativeName: 'العربية', flag: '🇸🇦' },
];

export default function LanguageSelector({
  visible,
  currentLanguage,
  onSelect,
  onClose,
}: LanguageSelectorProps) {
  const { colors } = useTheme();

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <TouchableOpacity
        style={styles.overlay}
        activeOpacity={1}
        onPress={onClose}
      >
        <View style={[styles.container, { backgroundColor: colors.card }]}>
          <Text style={[styles.title, { color: colors.text }]}>Dil Seçin</Text>
          
          {LANGUAGES.map((lang) => (
            <TouchableOpacity
              key={lang.code}
              style={[
                styles.option,
                { borderBottomColor: colors.border },
                currentLanguage === lang.code && { backgroundColor: colors.grey100 },
              ]}
              onPress={() => {
                onSelect(lang.code);
                onClose();
              }}
            >
              <Text style={styles.flag}>{lang.flag}</Text>
              <View style={styles.langInfo}>
                <Text style={[styles.langName, { color: colors.text }]}>{lang.nativeName}</Text>
                <Text style={[styles.langEnglish, { color: colors.textSecondary }]}>{lang.name}</Text>
              </View>
              {currentLanguage === lang.code && (
                <Text style={styles.checkmark}>✓</Text>
              )}
            </TouchableOpacity>
          ))}

          <TouchableOpacity
            style={[styles.closeButton, { borderTopColor: colors.border }]}
            onPress={onClose}
          >
            <Text style={[styles.closeText, { color: colors.tint }]}>Kapat</Text>
          </TouchableOpacity>
        </View>
      </TouchableOpacity>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  container: {
    width: '100%',
    maxWidth: 320,
    borderRadius: 16,
    overflow: 'hidden',
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    textAlign: 'center',
    padding: 20,
    paddingBottom: 12,
  },
  option: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
  },
  flag: {
    fontSize: 28,
    marginRight: 14,
  },
  langInfo: {
    flex: 1,
  },
  langName: {
    fontSize: 16,
    fontWeight: '600',
  },
  langEnglish: {
    fontSize: 13,
    marginTop: 2,
  },
  checkmark: {
    fontSize: 18,
    color: '#E8731A',
    fontWeight: '700',
    marginLeft: 8,
  },
  closeButton: {
    padding: 16,
    borderTopWidth: 1,
    alignItems: 'center',
  },
  closeText: {
    fontSize: 16,
    fontWeight: '600',
  },
});
