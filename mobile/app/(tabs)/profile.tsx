import React, { useCallback, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import { useTheme } from '../../hooks/useTheme';
import { useAuth } from '../../context/AuthContext';
import Header from '../../components/ui/Header';
import Card from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import { crewAPI } from '../../services/api';
import { useI18n } from '../../context/I18nContext';
import { showAlert, showConfirm } from '../../utils/dialogs';
import { documentTypeLabel } from '../../utils/documentTypes';
import { availabilityBadge } from '../../utils/availability';
import { SUPPORTED_LANGUAGES, SupportedLanguage } from '../../i18n/types';

export default function ProfileScreen() {
  const router = useRouter();
  const { colors, CREWINTEL } = useTheme();
  const { user, logout } = useAuth();
  const { t, language, changeLanguage } = useI18n();
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [contact, setContact] = useState({ phone: '', email: '' });
  const [savingContact, setSavingContact] = useState(false);

  const loadProfile = async () => {
    try {
      const data = await crewAPI.meFull();
      setProfile(data);
      setContact({ phone: data?.phone || '', email: data?.email || '' });
    } catch (error) {
      console.log('Profile load error:', error);
    } finally {
      setLoading(false);
    }
  };

  /** Personel kendi telefon/e-posta bilgisini güncelleyebilir (portal ucu). */
  const saveContact = async () => {
    setSavingContact(true);
    try {
      const updated = await crewAPI.updateProfile({
        phone: contact.phone || undefined,
        email: contact.email || undefined,
      });
      setProfile((prev: any) => ({ ...prev, ...(updated || {}) }));
      showAlert(t('common.success'), t('profile.contactUpdated'));
    } catch (error: any) {
      showAlert(t('common.error'), error?.message || t('errors.unknown'));
    } finally {
      setSavingContact(false);
    }
  };

  useFocusEffect(
    useCallback(() => {
      if (user) loadProfile();
    }, [user?.id]),
  );

  const handleLogout = () => {
    showConfirm(
      t('auth.logout'),
      t('auth.logoutConfirm'),
      async () => {
        await logout();
        router.replace('/login');
      },
      t('auth.logout'),
      t('common.cancel'),
    );
  };

  const notDefined = t('profile.notDefined');

  const getInfoItems = () => {
    if (!profile) return [];
    return [
      { label: t('profile.position'), value: profile.position || notDefined },
      { label: t('profile.nationality'), value: profile.nationality || notDefined },
      { label: t('profile.telephone'), value: profile.phone || notDefined },
      { label: t('profile.email'), value: profile.email || user?.email },
      { label: t('profile.dateOfBirth'), value: profile.date_of_birth || notDefined },
      { label: t('profile.address'), value: profile.address || notDefined },
    ];
  };

  /**
   * Backend `availability` alanını "available" / "available_soon" /
   * "employed" gibi küçük harfli gönderir; api.ts bunu büyük harfe çevirir.
   * Eski eşleme yalnızca "AVAILABLE_NOW" beklediği için müsait personel bile
   * "Tanımlanmamış" görünüyordu.
   */
  const getAvailabilityLabel = () => availabilityBadge(t, profile?.availability_status);

  /** Belge rozeti: tarih varsa "geçerli" demek yanlıştı; geçmiş tarih de
   * "Geçerli" görünüyordu. Bugünle karşılaştırılır. */
  const documentBadge = (doc: any) => {
    if (!doc.expiry_date) return { label: t('profile.noDate'), variant: 'neutral' as const };
    const days = Math.ceil((new Date(doc.expiry_date).getTime() - Date.now()) / 86_400_000);
    if (days < 0) return { label: t('profile.expired'), variant: 'danger' as const };
    if (days <= 30) return { label: t('profile.expiringSoon'), variant: 'warning' as const };
    return { label: t('profile.valid'), variant: 'success' as const };
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <Header
        title={t('profile.title')}
        rightAction={
          <TouchableOpacity onPress={handleLogout}>
            <Text style={styles.logoutText}>{t('auth.logout')}</Text>
          </TouchableOpacity>
        }
      />

      <ScrollView contentContainerStyle={styles.content}>
        {/* Profile Header */}
        <Card variant="elevated" style={styles.profileCard}>
          <View style={styles.avatarRow}>
            <View style={[styles.avatar, { backgroundColor: CREWINTEL.orange }]}>
              <Text style={styles.avatarText}>
                {(user?.full_name || user?.email || 'U')[0].toUpperCase()}
              </Text>
            </View>
            <View style={styles.nameContainer}>
              <Text style={[styles.name, { color: colors.text }]}>
                {user?.full_name || 'Kullanıcı'}
              </Text>
              <Text style={[styles.email, { color: colors.textSecondary }]}>
                {user?.email}
              </Text>
              <Badge text={getAvailabilityLabel().label} variant={getAvailabilityLabel().variant} />
            </View>
          </View>
        </Card>

        {/* Personal Info */}
        <Card style={styles.section}>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('profile.personalInfo')}</Text>
          {getInfoItems().map((item, idx) => (
            <View key={idx} style={[styles.infoRow, { borderBottomColor: colors.border }]}>
              <Text style={[styles.infoLabel, { color: colors.textSecondary }]}>{item.label}</Text>
              <Text style={[styles.infoValue, { color: colors.text }]}>{item.value}</Text>
            </View>
          ))}
        </Card>

        {/* Maritime Info */}
        {profile?.rank && (
          <Card style={styles.section}>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('profile.maritimeInfo')}</Text>
            <View style={[styles.infoRow, { borderBottomColor: colors.border }]}>
              <Text style={[styles.infoLabel, { color: colors.textSecondary }]}>Rank</Text>
              <Text style={[styles.infoValue, { color: colors.text }]}>{profile.rank}</Text>
            </View>
            {profile.coc && (
              <View style={[styles.infoRow, { borderBottomColor: colors.border }]}>
                <Text style={[styles.infoLabel, { color: colors.textSecondary }]}>COC</Text>
                <Text style={[styles.infoValue, { color: colors.text }]}>{profile.coc}</Text>
              </View>
            )}
            {profile.sea_service_years && (
              <View style={[styles.infoRow, { borderBottomColor: colors.border }]}>
                <Text style={[styles.infoLabel, { color: colors.textSecondary }]}>{t('profile.seaService')}</Text>
                <Text style={[styles.infoValue, { color: colors.text }]}>
                  {profile.sea_service_years} {t('profile.years')}
                </Text>
              </View>
            )}
          </Card>
        )}

        {/* Documents */}
        <Card style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('profile.documents')}</Text>
            <Badge text={`${profile?.documents?.length || 0}`} variant="info" />
          </View>
          {profile?.documents?.slice(0, 5).map((doc: any, idx: number) => {
            const badge = documentBadge(doc);
            return (
              <View key={idx} style={[styles.docItem, { borderBottomColor: colors.border }]}>
                <Text style={[styles.docType, { color: colors.text }]}>{documentTypeLabel(t, doc.document_type)}</Text>
                <Badge text={badge.label} variant={badge.variant} size="sm" />
              </View>
            );
          })}
        </Card>

        {/* Preferences */}
        <Card style={styles.section}>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('profile.preferences')}</Text>
          <View style={[styles.infoRow, { borderBottomColor: colors.border }]}>
            <Text style={[styles.infoLabel, { color: colors.textSecondary }]}>{t('profile.preferredRank')}</Text>
            <Text style={[styles.infoValue, { color: colors.text }]}>
              {profile?.preferred_rank || notDefined}
            </Text>
          </View>
          <View style={[styles.infoRow, { borderBottomColor: colors.border }]}>
            <Text style={[styles.infoLabel, { color: colors.textSecondary }]}>{t('profile.preferredVessel')}</Text>
            <Text style={[styles.infoValue, { color: colors.text }]}>
              {profile?.preferred_vessel_type || notDefined}
            </Text>
          </View>
          <View style={[styles.infoRow, { borderBottomColor: colors.border }]}>
            <Text style={[styles.infoLabel, { color: colors.textSecondary }]}>{t('profile.jobStatus')}</Text>
            <Badge
              text={profile?.job_seeking ? t('profile.jobSeeking') : t('profile.jobPassive')}
              variant={profile?.job_seeking ? 'success' : 'neutral'}
            />
          </View>
        </Card>

        {/* İletişim bilgisi güncelleme — personel kendi telefon/e-postasını düzeltir */}
        <Card style={styles.section}>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('profile.contactTitle')}</Text>
          <Input
            label={t('profile.telephone')}
            value={contact.phone}
            onChangeText={(phone) => setContact((prev) => ({ ...prev, phone }))}
            placeholder="+90 5xx xxx xx xx"
            keyboardType="phone-pad"
          />
          <Input
            label={t('profile.email')}
            value={contact.email}
            onChangeText={(email) => setContact((prev) => ({ ...prev, email }))}
            placeholder="ornek@email.com"
            keyboardType="email-address"
            autoCapitalize="none"
          />
          <Button
            title={savingContact ? t('common.loading') : t('common.save')}
            onPress={saveContact}
            loading={savingContact}
            disabled={savingContact}
          />
        </Card>

        {/* Dil seçimi — Rusça/Arapça personel için */}
        <Card style={styles.section}>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('profile.language')}</Text>
          <View style={styles.languageRow}>
            {(SUPPORTED_LANGUAGES ?? []).map((option) => {
              const active = language === option.code;
              return (
                <TouchableOpacity
                  key={option.code}
                  onPress={() => changeLanguage(option.code as SupportedLanguage)}
                  style={[
                    styles.languageChip,
                    {
                      borderColor: active ? CREWINTEL.orange : colors.border,
                      backgroundColor: active ? '#FFF7ED' : 'transparent',
                    },
                  ]}
                >
                  <Text style={{ fontSize: 13, color: colors.text }}>
                    {option.flag} {option.nativeName}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </Card>

        {/* Logout */}
        <View style={styles.logoutSection}>
          <Button
            title={t('auth.logout')}
            onPress={handleLogout}
            variant="danger"
            style={styles.logoutButton}
          />
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    padding: 16,
  },
  logoutText: {
    color: '#FF3B30',
    fontSize: 14,
    fontWeight: '600',
  },
  profileCard: {
    marginTop: -20,
    marginBottom: 16,
  },
  avatarRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatar: {
    width: 64,
    height: 64,
    borderRadius: 32,
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: {
    color: '#FFFFFF',
    fontSize: 24,
    fontWeight: '700',
  },
  nameContainer: {
    marginLeft: 16,
    flex: 1,
  },
  name: {
    fontSize: 20,
    fontWeight: '700',
  },
  email: {
    fontSize: 14,
    marginBottom: 6,
  },
  section: {
    marginBottom: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 12,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 1,
  },
  infoLabel: {
    fontSize: 14,
  },
  infoValue: {
    fontSize: 14,
    fontWeight: '600',
    flex: 1,
    textAlign: 'right',
    marginLeft: 16,
  },
  docItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
  },
  docType: {
    fontSize: 14,
    fontWeight: '600',
  },
  languageRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  languageChip: {
    borderWidth: 1,
    borderRadius: 999,
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  logoutSection: {
    marginTop: 20,
    marginBottom: 40,
  },
  logoutButton: {
    width: '100%',
  },
});
