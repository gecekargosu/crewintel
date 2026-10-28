import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { useTheme } from '../../hooks/useTheme';
import { useI18n } from '../../context/I18nContext';

interface StatItem {
  value: number;
  label: string;
  icon?: string;
}

interface HomeStatsProps {
  stats: StatItem[];
}

export default function HomeStats({ stats }: HomeStatsProps) {
  const { colors, CREWINTEL } = useTheme();
  const { t } = useI18n();
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 500,
      useNativeDriver: true,
    }).start();
  }, []);

  return (
    <Animated.View style={[styles.container, { opacity: fadeAnim }]}>
      {stats.map((stat, index) => (
        <View key={index} style={[styles.statCard, { backgroundColor: colors.card }]}>
          {stat.icon && <Text style={styles.statIcon}>{stat.icon}</Text>}
          <Text style={[styles.statValue, { color: CREWINTEL.orange }]}>{stat.value}</Text>
          <Text style={[styles.statLabel, { color: colors.textSecondary }]}>{stat.label}</Text>
        </View>
      ))}
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    marginTop: 16,
    gap: 10,
  },
  statCard: {
    flex: 1,
    alignItems: 'center',
    padding: 14,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  statIcon: {
    fontSize: 20,
    marginBottom: 6,
  },
  statValue: {
    fontSize: 24,
    fontWeight: '800',
  },
  statLabel: {
    fontSize: 12,
    marginTop: 4,
    textAlign: 'center',
  },
});
