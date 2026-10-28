import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useTheme } from '../../hooks/useTheme';
import { useI18n } from '../../context/I18nContext';

interface Action {
  icon: string;
  label: string;
  onPress: () => void;
}

interface QuickActionGridProps {
  actions?: Action[];
}

export default function QuickActionGrid({ actions }: QuickActionGridProps) {
  const { colors, CREWINTEL } = useTheme();
  const { t } = useI18n();

  const defaultActions: Action[] = actions || [
    { icon: '💼', label: t('nav.jobs'), onPress: () => {} },
    { icon: '📄', label: t('profile.documents'), onPress: () => {} },
    { icon: '📋', label: t('nav.applications'), onPress: () => {} },
    { icon: '💬', label: t('nav.messages'), onPress: () => {} },
  ];

  return (
    <View style={[styles.container, { backgroundColor: colors.card }]}>
      <Text style={[styles.title, { color: colors.text }]}>{t('home.quickActions')}</Text>
      <View style={styles.grid}>
        {defaultActions.map((action, index) => (
          <TouchableOpacity
            key={index}
            style={[styles.actionButton, { backgroundColor: colors.grey100 }]}
            onPress={action.onPress}
            activeOpacity={0.7}
          >
            <View style={[styles.iconContainer, { backgroundColor: `${CREWINTEL.orange}15` }]}>
              <Text style={styles.icon}>{action.icon}</Text>
            </View>
            <Text style={[styles.label, { color: colors.text }]} numberOfLines={1}>
              {action.label}
            </Text>
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
  title: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 14,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  actionButton: {
    width: '48%',
    alignItems: 'center',
    padding: 14,
    borderRadius: 12,
  },
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  icon: {
    fontSize: 24,
  },
  label: {
    fontSize: 13,
    fontWeight: '600',
    textAlign: 'center',
  },
});
