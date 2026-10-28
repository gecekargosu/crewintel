import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { useTheme } from '../../hooks/useTheme';
import Header from '../../components/ui/Header';
import Card from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import { jobsAPI } from '../../services/api';
import { useI18n } from '../../context/I18nContext';
import { formatDuration } from '../../utils/format';
import { showAlert, showConfirm } from '../../utils/dialogs';

export default function JobDetailScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams();
  const { colors, CREWINTEL } = useTheme();
  const { t } = useI18n();
  const [job, setJob] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);
  const [applied, setApplied] = useState(false);

  useEffect(() => {
    loadJob();
  }, [id]);

  const loadJob = async () => {
    try {
      const data = await jobsAPI.get(Number(id));
      setJob(data);
      setApplied(data?.has_applied || false);
    } catch (error) {
      console.log('Job load error:', error);
    } finally {
      setLoading(false);
    }
  };

  const submitApplication = async () => {
    setApplying(true);
    try {
      await jobsAPI.apply(Number(id));
      setApplied(true);
      showAlert(t('common.success'), t('jobs.applied'));
    } catch (error: any) {
      showAlert(t('common.error'), error.message || t('errors.unknown'));
    } finally {
      setApplying(false);
    }
  };

  const handleApply = () => {
    showConfirm(
      t('jobs.confirmApply'),
      t('jobs.confirmApplyMessage'),
      submitApplication,
      t('jobs.apply'),
      t('common.cancel'),
    );
  };

  if (loading) {
    return (
      <View style={[styles.container, { backgroundColor: colors.background }]}>
        <Header title={t('jobs.detail')} showBack onBack={() => router.back()} />
        <View style={styles.loadingContainer}>
          <Text style={[styles.loadingText, { color: colors.textSecondary }]}>{t('common.loading')}</Text>
        </View>
      </View>
    );
  }

  if (!job) {
    return (
      <View style={[styles.container, { backgroundColor: colors.background }]}>
        <Header title={t('jobs.detail')} showBack onBack={() => router.back()} />
        <View style={styles.loadingContainer}>
          <Text style={[styles.loadingText, { color: colors.textSecondary }]}>{t('jobs.empty')}</Text>
        </View>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <Header title={t('jobs.detail')} showBack onBack={() => router.back()} />

      <ScrollView contentContainerStyle={styles.content}>
        {/* Job Title */}
        <Card variant="elevated" style={styles.titleCard}>
          <Text style={[styles.jobTitle, { color: colors.text }]}>
            {job.title || 'İş İlanı'}
          </Text>
          <Text style={[styles.companyName, { color: colors.textSecondary }]}>
            {job.company_name || 'CREWINTEL'}
          </Text>
          {job.match_score && (
            <View style={styles.matchBadge}>
              <Badge text={`Uygunluk: %${job.match_score}`} variant="success" size="md" />
            </View>
          )}
        </Card>

        {/* Details */}
        <Card style={styles.detailsCard}>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('jobs.details')}</Text>

          <View style={styles.detailRow}>              <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>{t('jobs.position')}</Text>
            <Text style={[styles.detailValue, { color: colors.text }]}>{job.position || job.title}</Text>
          </View>

          {job.vessel_type && (
            <View style={styles.detailRow}>
              <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>{t('jobs.vesselType')}</Text>
              <Text style={[styles.detailValue, { color: colors.text }]}>{job.vessel_type}</Text>
            </View>
          )}

          {job.location && (
            <View style={styles.detailRow}>
              <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>{t('jobs.location')}</Text>
              <Text style={[styles.detailValue, { color: colors.text }]}>{job.location}</Text>
            </View>
          )}

          {job.contract_duration && (
            <View style={styles.detailRow}>
              <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>{t('jobs.duration')}</Text>
              <Text style={[styles.detailValue, { color: colors.text }]}>{formatDuration(job.contract_duration, t('common.months'))}</Text>
            </View>
          )}

          {job.salary_min && (
            <View style={styles.detailRow}>
              <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>{t('jobs.salary')}</Text>
              <Text style={[styles.detailValue, { color: colors.tint }]}>
                {job.salary_min} - {job.salary_max} {job.salary_currency || 'USD'}/{job.salary_period || 'monthly'}
              </Text>
            </View>
          )}
        </Card>

        {/* Description */}
        {job.description && (
          <Card style={styles.detailsCard}>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('jobs.description')}</Text>
            <Text style={[styles.descriptionText, { color: colors.textSecondary }]}>
              {job.description}
            </Text>
          </Card>
        )}

        {/* Requirements */}
        {job.requirements && (
          <Card style={styles.detailsCard}>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('jobs.requirements')}</Text>
            <Text style={[styles.descriptionText, { color: colors.textSecondary }]}>
              {job.requirements}
            </Text>
          </Card>
        )}

        {/* Apply Button */}
        <View style={styles.applySection}>
          {applied ? (
            <View style={[styles.appliedBox, { backgroundColor: '#34C75915', borderColor: '#34C75930' }]}>
              <Text style={styles.appliedIcon}>✓</Text>
              <Text style={[styles.appliedText, { color: '#34C759' }]}>{t('jobs.applied')}</Text>
            </View>
          ) : (
            <Button
              title={applying ? t('jobs.applying') : t('jobs.apply')}
              onPress={handleApply}
              loading={applying}
              disabled={applying}
              size="lg"
            />
          )}
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
  },
  titleCard: {
    marginTop: -20,
  },
  jobTitle: {
    fontSize: 22,
    fontWeight: '800',
    marginBottom: 4,
  },
  companyName: {
    fontSize: 15,
    marginBottom: 8,
  },
  matchBadge: {
    marginTop: 8,
  },
  detailsCard: {
    marginTop: 12,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 12,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#E8E8ED20',
  },
  detailLabel: {
    fontSize: 14,
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '600',
  },
  descriptionText: {
    fontSize: 14,
    lineHeight: 22,
  },
  applySection: {
    marginTop: 20,
    marginBottom: 40,
  },
  appliedBox: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    gap: 8,
  },
  appliedIcon: {
    fontSize: 18,
    color: '#34C759',
    fontWeight: '700',
  },
  appliedText: {
    fontSize: 16,
    fontWeight: '700',
  },
});
