import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useTheme } from '../../hooks/useTheme';
import { useAuth } from '../../context/AuthContext';
import Header from '../../components/ui/Header';
import Card from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import { crewAPI } from '../../services/api';
import { useI18n } from '../../context/I18nContext';

export default function ProfileScreen() {
  const router = useRouter();
  const { colors, CREWINTEL } = useTheme();
  const { user, logout } = useAuth();
  const { t } = useI18n();
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const loadProfile = async () => {
    try {
      const data = await crewAPI.meFull();
      setProfile(data);
    } catch (error) {
      console.log('Profile load error:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProfile();
  }, []);

  const handleLogout = async () => {
    Alert.alert(
      t('auth.logout'),
      t('auth.logoutConfirm'),
      [
        { text: 'İptal', style: 'cancel' },
        {
          text: 'Çıkış Yap',
          style: 'destructive',
          onPress: async () => {
            await logout();
            router.replace('/login');
          },
        },
      ]
    );
  };

  const getInfoItems = () => {
    if (!profile) return [];
    return [
      { label: 'Pozisyon', value: profile.position || 'Tanımlanmamış' },
      { label: 'Uyruk', value: profile.nationality || 'Tanımlanmamış' },
      { label: 'Telefon', value: profile.phone || 'Tanımlanmamış' },
      { label: 'E-posta', value: profile.email || user?.email },
      { label: 'Doğum Tarihi', value: profile.date_of_birth || 'Tanımlanmamış' },
      { label: 'Adres', value: profile.address || 'Tanımlanmamış' },
    ];
  };

  const getAvailabilityLabel = () => {
    switch (profile?.availability_status) {
      case 'AVAILABLE_NOW': return { label: 'Müsait', variant: 'success' as const };
      case 'AVAILABLE_SOON': return { label: 'Yakında Müsait', variant: 'warning' as const };
      case 'CURRENTLY_EMPLOYED': return { label: 'Aktif Görevde', variant: 'info' as const };
      case 'LOOKING': return { label: 'İş Arıyor', variant: 'success' as const };
      default: return { label: 'Tanımlanmamış', variant: 'neutral' as const };
    }
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
                <Text style={[styles.infoValue, { color: colors.text }]}>{profile.sea_service_years} yıl</Text>
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
          {profile?.documents?.slice(0, 3).map((doc: any, idx: number) => (
            <View key={idx} style={[styles.docItem, { borderBottomColor: colors.border }]}>
              <Text style={[styles.docType, { color: colors.text }]}>{doc.document_type}</Text>
              <Badge
                text={doc.expiry_date ? 'Geçerli' : 'Tarihsiz'}
                variant={doc.expiry_date ? 'success' : 'neutral'}
                size="sm"
              />
            </View>
          ))}
        </Card>

        {/* Preferences */}
        <Card style={styles.section}>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('profile.preferences')}</Text>
          <View style={[styles.infoRow, { borderBottomColor: colors.border }]}>
            <Text style={[styles.infoLabel, { color: colors.textSecondary }]}>Tercih Edilen Rank</Text>
            <Text style={[styles.infoValue, { color: colors.text }]}>
              {profile?.preferred_rank || 'Tanımlanmamış'}
            </Text>
          </View>
          <View style={[styles.infoRow, { borderBottomColor: colors.border }]}>
            <Text style={[styles.infoLabel, { color: colors.textSecondary }]}>Tercih Edilen Gemi</Text>
            <Text style={[styles.infoValue, { color: colors.text }]}>
              {profile?.preferred_vessel_type || 'Tanımlanmamış'}
            </Text>
          </View>
          <View style={[styles.infoRow, { borderBottomColor: colors.border }]}>
            <Text style={[styles.infoLabel, { color: colors.textSecondary }]}>İş Durumu</Text>
            <Badge
              text={profile?.job_seeking ? 'İş Arıyorum' : 'Pasif'}
              variant={profile?.job_seeking ? 'success' : 'neutral'}
            />
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
  logoutSection: {
    marginTop: 20,
    marginBottom: 40,
  },
  logoutButton: {
    width: '100%',
  },
});
