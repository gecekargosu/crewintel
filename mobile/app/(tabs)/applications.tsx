import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useTheme } from '../../hooks/useTheme';
import Header from '../../components/ui/Header';
import Card from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import { jobsAPI } from '../../services/api';
import { useI18n } from '../../context/I18nContext';

export default function ApplicationsScreen() {
  const router = useRouter();
  const { colors, CREWINTEL } = useTheme();
  const { t } = useI18n();
  const [applications, setApplications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadApplications = async () => {
    try {
      const data = await jobsAPI.myApplications();
      setApplications(Array.isArray(data) ? data : []);
    } catch (error) {
      console.log('Applications load error:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadApplications();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    loadApplications();
  };

  const getStatusVariant = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'approved':
      case 'shortlisted':
        return 'success';
      case 'pending':
      case 'under_review':
        return 'warning';
      case 'rejected':
        return 'danger';
      default:
        return 'neutral';
    }
  };

  const getStatusText = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'approved':
        return 'Onaylandı';
      case 'shortlisted':
        return 'Seçildi';
      case 'pending':
        return 'Beklemede';
      case 'under_review':
        return 'İnceleniyor';
      case 'rejected':
        return 'Reddedildi';
      default:
        return status || 'Bilinmiyor';
    }
  };

  const renderApplication = ({ item }: { item: any }) => (
    <Card variant="elevated" style={styles.appCard}>
      <View style={styles.appHeader}>
        <Text style={[styles.appTitle, { color: colors.text }]} numberOfLines={1}>
          {item.job?.title || item.title || 'İş İlanı'}
        </Text>
        <Badge
          text={getStatusText(item.status)}
          variant={getStatusVariant(item.status)}
        />
      </View>

      <Text style={[styles.appCompany, { color: colors.textSecondary }]}>
        {item.ship_name || item.position || item.job?.company_name || 'CREWINTEL'}
      </Text>

      {item.match_score && (
        <View style={styles.matchInfo}>
          <Text style={[styles.matchLabel, { color: colors.textSecondary }]}>Uygunluk:</Text>
          <Badge text={`%${item.match_score}`} variant="success" />
        </View>
      )}

      <View style={styles.appFooter}>
        <Text style={[styles.dateText, { color: colors.textSecondary }]}>
          Başvuru: {item.created_at || item.applied_at
            ? new Date(item.created_at || item.applied_at).toLocaleDateString('tr-TR')
            : ''}
        </Text>
        {item.applied_from && (
          <Badge text={item.applied_from} variant="info" size="sm" />
        )}
      </View>
    </Card>
  );

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <Header title={t('applications.title')} subtitle={t('applications.count', { count: applications.length })} />

      <FlatList
        data={applications}
        renderItem={renderApplication}
        keyExtractor={(item) => item.id.toString()}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={CREWINTEL.orange} />
        }
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyIcon}>📋</Text>
            <Text style={[styles.emptyTitle, { color: colors.text }]}>{t('applications.empty')}</Text>
            <Text style={[styles.emptyText, { color: colors.textSecondary }]}>
              {t('applications.emptyDescription')}
            </Text>
            <TouchableOpacity
              style={[styles.browseButton, { backgroundColor: CREWINTEL.orange }]}
              onPress={() => router.push('/(tabs)/jobs')}
            >
              <Text style={styles.browseButtonText}>{t('applications.browseJobs')}</Text>
            </TouchableOpacity>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  list: {
    padding: 16,
  },
  appCard: {
    marginBottom: 12,
  },
  appHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  appTitle: {
    fontSize: 16,
    fontWeight: '700',
    flex: 1,
    marginRight: 8,
  },
  appCompany: {
    fontSize: 13,
    marginBottom: 8,
  },
  matchInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 8,
  },
  matchLabel: {
    fontSize: 12,
  },
  appFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  dateText: {
    fontSize: 12,
  },
  empty: {
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    marginBottom: 20,
  },
  browseButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 10,
  },
  browseButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
});
