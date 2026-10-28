import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useTheme } from '../../hooks/useTheme';
import { useAuth } from '../../context/AuthContext';
import { useI18n } from '../../context/I18nContext';
import Header from '../../components/ui/Header';
import Card from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import HeroBanner from '../../components/home/HeroBanner';
import HomeStats from '../../components/home/HomeStats';
import DocumentAlertCard from '../../components/home/DocumentAlertCard';
import RecommendedJobCard from '../../components/home/RecommendedJobCard';
import QuickActionGrid from '../../components/home/QuickActionGrid';
import { crewAPI, jobsAPI, notificationsAPI } from '../../services/api';

export default function HomeScreen() {
  const router = useRouter();
  const { colors, CREWINTEL } = useTheme();
  const { user } = useAuth();
  const { t } = useI18n();
  const [profile, setProfile] = useState<any>(null);
  const [jobs, setJobs] = useState<any[]>([]);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    try {
      const [profileRes, jobsRes, notifRes] = await Promise.allSettled([
        crewAPI.meFull(),
        jobsAPI.list(),
        notificationsAPI.list(),
      ]);

      if (profileRes.status === 'fulfilled') {
        setProfile(profileRes.value);
      }
      if (jobsRes.status === 'fulfilled') {
        const jobsData = jobsRes.value;
        setJobs(Array.isArray(jobsData) ? jobsData.slice(0, 3) : []);
      }
      if (notifRes.status === 'fulfilled') {
        const notifData = notifRes.value;
        setNotifications(Array.isArray(notifData) ? notifData.slice(0, 5) : []);
      }
    } catch (error) {
      console.log('Home load error:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  // Calculate document expiry alerts
  const expiringDocs = profile?.documents?.filter((d: any) => {
    if (!d.expiry_date) return false;
    const days = Math.ceil((new Date(d.expiry_date).getTime() - Date.now()) / (1000 * 60 * 60 * 24));
    return days <= 30 && days > 0;
  }) || [];

  // Stats data
  const statsData = [
    { value: profile?.documents?.length || 0, label: t('home.documents'), icon: '📄' },
    { value: profile?.contracts?.length || 0, label: t('home.contracts'), icon: '📋' },
    { value: notifications.filter(n => !n.read).length, label: t('home.notifications'), icon: '🔔' },
  ];

  // Quick actions with navigation
  const quickActions = [
    { icon: '💼', label: t('nav.jobs'), onPress: () => router.push('/(tabs)/jobs') },
    { icon: '📄', label: t('profile.documents'), onPress: () => router.push('/(tabs)/profile') },
    { icon: '📋', label: t('nav.applications'), onPress: () => router.push('/(tabs)/applications') },
    { icon: '💬', label: t('nav.messages'), onPress: () => router.push('/(tabs)/messages') },
  ];

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={CREWINTEL.orange} />
        }
        showsVerticalScrollIndicator={false}
      >
        {/* Hero Banner */}
        <HeroBanner
          userName={user?.full_name || user?.email?.split('@')[0] || t('home.user')}
          availabilityStatus={profile?.availability_status}
          documentCount={profile?.documents?.length || 0}
          contractCount={profile?.contracts?.length || 0}
          onCtaPress={() => router.push('/(tabs)/jobs')}
        />

        {/* Stats */}
        <HomeStats stats={statsData} />

        {/* Document Alerts */}
        {expiringDocs.length > 0 && (
          <DocumentAlertCard
            documents={expiringDocs}
            onPress={() => router.push('/(tabs)/profile')}
          />
        )}

        {/* Recommended Jobs */}
        <RecommendedJobCard
          jobs={jobs}
          onViewAll={() => router.push('/(tabs)/jobs')}
          onJobPress={(job) => router.push(`/job/${job.id}`)}
        />

        {/* Quick Actions */}
        <QuickActionGrid actions={quickActions} />

        {/* Recent Notifications */}
        {notifications.length > 0 && (
          <Card style={styles.sectionCard}>
            <View style={styles.sectionHeader}>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('home.recentNotifications')}</Text>
              <TouchableOpacity onPress={() => router.push('/(tabs)/messages')}>
                <Text style={[styles.seeAll, { color: colors.tint }]}>{t('home.seeAll')}</Text>
              </TouchableOpacity>
            </View>
            {notifications.map((notif, idx) => (
              <View key={idx} style={[styles.notifItem, { borderBottomColor: colors.border }]}>
                <Text style={[styles.notifText, { color: colors.text }]} numberOfLines={2}>
                  {notif.title || notif.message}
                </Text>
                {!notif.read && (
                  <View style={[styles.unreadDot, { backgroundColor: CREWINTEL.orange }]} />
                )}
              </View>
            ))}
          </Card>
        )}

        <View style={{ height: 20 }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
  },
  sectionCard: {
    marginHorizontal: 16,
    marginTop: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
  },
  seeAll: {
    fontSize: 13,
    fontWeight: '600',
  },
  notifItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
  },
  notifText: {
    flex: 1,
    fontSize: 13,
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginLeft: 8,
  },
});
