import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { useTheme } from '../hooks/useTheme';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';
import Button from '../components/ui/Button';

export default function PendingApprovalScreen() {
  const router = useRouter();
  const { colors, CREWINTEL } = useTheme();
  const { logout } = useAuth();
  const { t } = useI18n();

  const handleLogout = async () => {
    await logout();
    router.replace('/login');
  };

  return (
    <View style={[styles.container, { backgroundColor: CREWINTEL.navy }]}>
      <View style={styles.content}>
        <View style={[styles.iconContainer, { backgroundColor: '#FF950020' }]}>
          <Text style={styles.icon}>⏳</Text>
        </View>

        <Text style={styles.title}>{t('auth.pendingApproval')}</Text>

        <Text style={styles.description}>
          {t('auth.pendingDescription')}
        </Text>

        <View style={[styles.infoBox, { backgroundColor: colors.card }]}>
          <Text style={[styles.infoTitle, { color: colors.text }]}>{t('common.confirm')}</Text>
          <Text style={[styles.infoText, { color: colors.textSecondary }]}>
            {t('auth.pendingSteps')}
          </Text>
        </View>

        <Button
          title={t('auth.logout')}
          onPress={handleLogout}
          variant="ghost"
          style={styles.logoutButton}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  iconContainer: {
    width: 100,
    height: 100,
    borderRadius: 50,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
  },
  icon: {
    fontSize: 48,
  },
  title: {
    color: '#FFFFFF',
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 12,
    textAlign: 'center',
  },
  description: {
    color: 'rgba(255,255,255,0.7)',
    fontSize: 15,
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 32,
  },
  infoBox: {
    width: '100%',
    borderRadius: 12,
    padding: 20,
    marginBottom: 32,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 12,
  },
  infoText: {
    fontSize: 14,
    lineHeight: 22,
  },
  logoutButton: {
    width: '100%',
  },
});
