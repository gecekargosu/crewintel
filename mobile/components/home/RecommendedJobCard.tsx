import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useTheme } from '../../hooks/useTheme';
import { useI18n } from '../../context/I18nContext';
import { formatDuration } from '../../utils/format';
import Badge from '../ui/Badge';

interface Job {
  id: number;
  title: string;
  vessel_type?: string;
  location?: string;
  salary_min?: number;
  salary_max?: number;
  salary_currency?: string;
  contract_duration?: number | string;
  match_score?: number;
  status?: string;
}

interface RecommendedJobCardProps {
  jobs: Job[];
  onViewAll?: () => void;
  onJobPress?: (job: Job) => void;
}

export default function RecommendedJobCard({ jobs, onViewAll, onJobPress }: RecommendedJobCardProps) {
  const { colors, CREWINTEL } = useTheme();
  const { t } = useI18n();

  if (!jobs || jobs.length === 0) {
    return (
      <View style={[styles.container, { backgroundColor: colors.card }]}>
        <View style={styles.header}>
          <Text style={[styles.title, { color: colors.text }]}>{t('home.recommendedJobs')}</Text>
        </View>
        <Text style={[styles.emptyText, { color: colors.textSecondary }]}>
          {t('home.noJobsHint')}
        </Text>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: colors.card }]}>
      <View style={styles.header}>
        <Text style={[styles.title, { color: colors.text }]}>{t('home.recommendedJobs')}</Text>
        <TouchableOpacity onPress={onViewAll}>
          <Text style={[styles.seeAll, { color: colors.tint }]}>{t('home.seeAll')}</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.jobList}>
        {jobs.slice(0, 3).map((job) => (
          <TouchableOpacity
            key={job.id}
            style={[styles.jobCard, { borderColor: colors.border }]}
            onPress={() => onJobPress?.(job)}
            activeOpacity={0.7}
          >
            <View style={styles.jobHeader}>
              <Text style={[styles.jobTitle, { color: colors.text }]} numberOfLines={1}>
                {job.title}
              </Text>
              {job.match_score && (
                <Badge text={`%${job.match_score}`} variant="success" size="sm" />
              )}
            </View>

            {job.vessel_type && (
              <Text style={[styles.jobVessel, { color: colors.textSecondary }]}>
                🚢 {job.vessel_type}
              </Text>
            )}

            <View style={styles.jobDetails}>
              {job.location && (
                <Text style={[styles.jobDetail, { color: colors.textSecondary }]}>
                  📍 {job.location}
                </Text>
              )}
              {job.salary_min && (
                <Text style={[styles.jobSalary, { color: CREWINTEL.orange }]}>
                  💰 {job.salary_min.toLocaleString()}
                  {job.salary_max ? ` - ${job.salary_max.toLocaleString()}` : ''}
                  {' '}{job.salary_currency || 'USD'}
                </Text>
              )}
            </View>

            {job.contract_duration && (
              <Text style={[styles.jobDuration, { color: colors.textSecondary }]}>
                📅 {formatDuration(job.contract_duration, t('common.months'))}
              </Text>
            )}
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginHorizontal: 16,
    marginTop: 16,
    borderRadius: 14,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 14,
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
  },
  seeAll: {
    fontSize: 13,
    fontWeight: '600',
  },
  emptyText: {
    fontSize: 14,
    textAlign: 'center',
    paddingVertical: 20,
  },
  jobList: {
    gap: 12,
  },
  jobCard: {
    borderWidth: 1,
    borderRadius: 12,
    padding: 14,
  },
  jobHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  jobTitle: {
    fontSize: 15,
    fontWeight: '700',
    flex: 1,
    marginRight: 8,
  },
  jobVessel: {
    fontSize: 13,
    marginBottom: 8,
  },
  jobDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  jobDetail: {
    fontSize: 12,
  },
  jobSalary: {
    fontSize: 13,
    fontWeight: '700',
  },
  jobDuration: {
    fontSize: 12,
    marginTop: 4,
  },
});
