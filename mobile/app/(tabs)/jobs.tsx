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
import { formatDuration } from '../../utils/format';
import { useI18n } from '../../context/I18nContext';

export default function JobsScreen() {
  const router = useRouter();
  const { colors, CREWINTEL } = useTheme();
  const { t } = useI18n();
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadJobs = async () => {
    try {
      const data = await jobsAPI.list();
      setJobs(Array.isArray(data) ? data : data?.items || []);
    } catch (error) {
      console.log('Jobs load error:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadJobs();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    loadJobs();
  };

  const renderJob = ({ item }: { item: any }) => (
    <TouchableOpacity onPress={() => router.push(`/job/${item.id}`)}>
      <Card variant="elevated" style={styles.jobCard}>
        <View style={styles.jobHeader}>
          <View style={styles.jobTitleRow}>
            <Text style={[styles.jobTitle, { color: colors.text }]} numberOfLines={1}>
              {item.title || 'İş İlanı'}
            </Text>
            {item.match_score && (
              <Badge text={`%${item.match_score}`} variant="success" />
            )}
          </View>
          <Text style={[styles.jobCompany, { color: colors.textSecondary }]}>
            {item.ship_name || item.company_name || item.position || 'CREWINTEL'}
          </Text>
        </View>

        <View style={styles.jobDetails}>
          <View style={styles.jobDetailItem}>
            <Text style={styles.jobDetailIcon}>📍</Text>
            <Text style={[styles.jobDetailText, { color: colors.textSecondary }]}>
              {item.location || 'Worldwide'}
            </Text>
          </View>
          <View style={styles.jobDetailItem}>
            <Text style={styles.jobDetailIcon}>🚢</Text>
            <Text style={[styles.jobDetailText, { color: colors.textSecondary }]}>
              {item.vessel_type || item.position || 'Genel'}
            </Text>
          </View>
          {!!item.salary && (
            <View style={styles.jobDetailItem}>
              <Text style={styles.jobDetailIcon}>💰</Text>
              <Text style={[styles.jobDetailText, { color: colors.textSecondary }]}>
                {item.salary} {item.currency || 'USD'}
              </Text>
            </View>
          )}
        </View>

        {item.contract_duration && (
          <View style={styles.contractInfo}>
            <Text style={[styles.contractText, { color: colors.tint }]}>
              📅 {formatDuration(item.contract_duration, t('common.months'))}
            </Text>
          </View>
        )}

        <View style={styles.jobFooter}>
          {item.application_status ? (
            <Badge text="Başvuruldu" variant="info" />
          ) : (
            <Badge text="Açık" variant="success" />
          )}
          <Text style={[styles.postedText, { color: colors.textSecondary }]}>
            {item.application_deadline
              ? `Son: ${new Date(item.application_deadline).toLocaleDateString('tr-TR')}`
              : ''}
          </Text>
        </View>
      </Card>
    </TouchableOpacity>
  );

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <Header title={t('jobs.title')} subtitle={t('jobs.count', { count: jobs.length })} />

      <FlatList
        data={jobs}
        renderItem={renderJob}
        keyExtractor={(item) => item.id.toString()}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={CREWINTEL.orange} />
        }
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyIcon}>💼</Text>
            <Text style={[styles.emptyTitle, { color: colors.text }]}>{t('jobs.empty')}</Text>
            <Text style={[styles.emptyText, { color: colors.textSecondary }]}>
              {t('jobs.emptyDescription')}
            </Text>
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
  jobCard: {
    marginBottom: 12,
  },
  jobHeader: {
    marginBottom: 12,
  },
  jobTitleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  jobTitle: {
    fontSize: 16,
    fontWeight: '700',
    flex: 1,
    marginRight: 8,
  },
  jobCompany: {
    fontSize: 13,
    marginTop: 4,
  },
  jobDetails: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 10,
  },
  jobDetailItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  jobDetailIcon: {
    fontSize: 12,
  },
  jobDetailText: {
    fontSize: 12,
  },
  contractInfo: {
    marginBottom: 10,
  },
  contractText: {
    fontSize: 13,
    fontWeight: '600',
  },
  jobFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  postedText: {
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
  },
});
