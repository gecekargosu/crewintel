import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useTheme } from '../hooks/useTheme';
import { authAPI } from '../services/api';
import { useI18n } from '../context/I18nContext';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';

export default function RegisterScreen() {
  const router = useRouter();
  const { colors, CREWINTEL } = useTheme();

  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const { t } = useI18n();
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleRegister = async () => {
    if (!firstName || !lastName || !email || !phone || !password) {
      setError(t('validation.required'));
      return;
    }

    // Backend telefonu zorunlu tutuyor (min 7 karakter). Formda istege bagli
    // gorunuyordu; bos gonderim "Field required" gibi belirsiz bir 422
    // hatasiyla sonuclaniyordu.
    if (phone.replace(/\D/g, '').length < 7) {
      setError(t('validation.invalidPhone'));
      return;
    }

    if (password !== passwordConfirm) {
      setError(t('validation.passwordMismatch'));
      return;
    }

    if (password.length < 8) {
      setError(t('validation.passwordTooShort'));
      return;
    }

    setLoading(true);
    setError('');

    try {
      await authAPI.register({
        email,
        password,
        first_name: firstName,
        last_name: lastName,
        phone,
      });
      setSuccess(true);
    } catch (err: any) {
      setError(err.message || t('errors.unknown'));
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <View style={[styles.container, { backgroundColor: CREWINTEL.navy }]}>
        <View style={styles.successCard}>
          <View style={[styles.successIcon, { backgroundColor: '#34C75920' }]}>
            <Text style={styles.successEmoji}>✓</Text>
          </View>
          <Text style={styles.successTitle}>{t('common.success')}!</Text>
          <Text style={styles.successText}>
            {t('auth.pendingDescription')}
          </Text>
          <Button
            title={t('auth.backToLogin')}
            onPress={() => router.replace('/login')}
            variant="secondary"
            style={styles.successButton}
          />
        </View>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={[styles.container, { backgroundColor: CREWINTEL.navy }]}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        {/* Back Button */}
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Text style={styles.backText}>← Geri</Text>
        </TouchableOpacity>

        {/* Header */}
        <View style={styles.headerSection}>
          <Text style={styles.headerTitle}>{t('auth.registerTitle')}</Text>
          <Text style={styles.headerSubtitle}>
            {t('auth.registerTitle')}
          </Text>
        </View>

        {/* Register Form */}
        <View style={[styles.formCard, { backgroundColor: colors.card }]}>
          {error ? (
            <View style={[styles.errorBox, { backgroundColor: '#FF3B3015', borderColor: '#FF3B3030' }]}>
              <Text style={styles.errorText}>{error}</Text>
            </View>
          ) : null}

          <View style={styles.row}>
            <View style={styles.halfInput}>
              <Input
                label={`${t('auth.firstName')} *`}
                value={firstName}
                onChangeText={setFirstName}
                placeholder="Adınız"
                autoCapitalize="words"
              />
            </View>
            <View style={styles.halfInput}>
              <Input
                label={`${t('auth.lastName')} *`}
                value={lastName}
                onChangeText={setLastName}
                placeholder="Soyadınız"
                autoCapitalize="words"
              />
            </View>
          </View>

          <Input
            label={`${t('auth.email')} *`}
            value={email}
            onChangeText={setEmail}
            placeholder="ornek@email.com"
            keyboardType="email-address"
            autoCapitalize="none"
          />

          <Input
            label={`${t('auth.phone')} *`}
            value={phone}
            onChangeText={setPhone}
            placeholder="+90 5XX XXX XXXX"
            keyboardType="phone-pad"
          />

          <Input
            label={`${t('auth.password')} *`}
            value={password}
            onChangeText={setPassword}
            placeholder="En az 8 karakter"
            secureTextEntry
          />

          <Input
            label={`${t('auth.passwordConfirm')} *`}
            value={passwordConfirm}
            onChangeText={setPasswordConfirm}
            placeholder="Şifrenizi tekrar girin"
            secureTextEntry
          />

          <Button
            title={loading ? t('auth.registerLoading') : t('auth.registerButton')}
            onPress={handleRegister}
            loading={loading}
            disabled={loading}
            style={styles.registerButton}
          />

          <TouchableOpacity
            onPress={() => router.back()}
            style={styles.loginLink}
          >
            <Text style={[styles.loginText, { color: colors.textSecondary }]}>
              {t('auth.hasAccount')}{' '}
            </Text>
            <Text style={[styles.loginTextBold, { color: colors.tint }]}>
              {t('auth.loginLink')}
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 24,
    paddingVertical: 40,
  },
  backButton: {
    marginBottom: 20,
  },
  backText: {
    color: '#FFFFFF',
    fontSize: 16,
  },
  headerSection: {
    marginBottom: 24,
  },
  headerTitle: {
    color: '#FFFFFF',
    fontSize: 28,
    fontWeight: '800',
  },
  headerSubtitle: {
    color: 'rgba(255,255,255,0.6)',
    fontSize: 14,
    marginTop: 4,
  },
  formCard: {
    borderRadius: 16,
    padding: 24,
  },
  row: {
    flexDirection: 'row',
    gap: 12,
  },
  halfInput: {
    flex: 1,
  },
  errorBox: {
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    marginBottom: 16,
  },
  errorText: {
    color: '#FF3B30',
    fontSize: 13,
    textAlign: 'center',
  },
  registerButton: {
    marginTop: 8,
  },
  loginLink: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 20,
  },
  loginText: {
    fontSize: 14,
  },
  loginTextBold: {
    fontSize: 14,
    fontWeight: '700',
  },
  successCard: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  successIcon: {
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
  },
  successEmoji: {
    fontSize: 36,
    color: '#34C759',
    fontWeight: '700',
  },
  successTitle: {
    color: '#FFFFFF',
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 12,
    textAlign: 'center',
  },
  successText: {
    color: 'rgba(255,255,255,0.7)',
    fontSize: 15,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 32,
  },
  successButton: {
    width: '100%',
  },
});
