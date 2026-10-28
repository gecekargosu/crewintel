import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useTheme } from '../../hooks/useTheme';
import { useI18n } from '../../context/I18nContext';
import Badge from '../ui/Badge';

interface Document {
  document_type: string;
  expiry_date: string;
  days_remaining?: number;
}

interface DocumentAlertCardProps {
  documents: Document[];
  onPress?: () => void;
}

export default function DocumentAlertCard({ documents, onPress }: DocumentAlertCardProps) {
  const { colors, CREWINTEL } = useTheme();
  const { t } = useI18n();

  if (!documents || documents.length === 0) return null;

  const getUrgencyColor = (days: number) => {
    if (days <= 7) return '#FF3B30';
    if (days <= 14) return '#FF9500';
    return '#FF9500';
  };

  const getUrgencyBadge = (days: number) => {
    if (days <= 7) return { text: `${days}d`, variant: 'danger' as const };
    if (days <= 14) return { text: `${days}d`, variant: 'warning' as const };
    return { text: `${days}d`, variant: 'warning' as const };
  };

  return (
    <TouchableOpacity
      style={[styles.container, { backgroundColor: colors.card }]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <View style={[styles.iconContainer, { backgroundColor: '#FF950015' }]}>
            <Text style={styles.icon}>⚠️</Text>
          </View>
          <Text style={[styles.title, { color: colors.text }]}>{t('home.expiringDocuments')}</Text>
        </View>
        <Badge text={`${documents.length}`} variant="warning" size="sm" />
      </View>

      <View style={styles.alertList}>
        {documents.slice(0, 3).map((doc, index) => {
          const days = doc.days_remaining || Math.ceil(
            (new Date(doc.expiry_date).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
          );
          const urgency = getUrgencyBadge(days);
          const color = getUrgencyColor(days);

          return (
            <View key={index} style={[styles.alertItem, { borderBottomColor: colors.border }]}>
              <View style={styles.alertItemLeft}>
                <View style={[styles.urgencyDot, { backgroundColor: color }]} />
                <Text style={[styles.alertText, { color: colors.text }]} numberOfLines={1}>
                  {doc.document_type}
                </Text>
              </View>
              <Badge text={urgency.text} variant={urgency.variant} size="sm" />
            </View>
          );
        })}
      </View>

      {documents.length > 3 && (
        <Text style={[styles.moreText, { color: colors.tint }]}>
          +{documents.length - 3} {t('common.more')}
        </Text>
      )}
    </TouchableOpacity>
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
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  iconContainer: {
    width: 32,
    height: 32,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  icon: {
    fontSize: 16,
  },
  title: {
    fontSize: 15,
    fontWeight: '700',
  },
  alertList: {
    gap: 0,
  },
  alertItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
  },
  alertItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    flex: 1,
  },
  urgencyDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  alertText: {
    fontSize: 14,
    flex: 1,
  },
  moreText: {
    fontSize: 13,
    fontWeight: '600',
    textAlign: 'center',
    marginTop: 12,
  },
});
