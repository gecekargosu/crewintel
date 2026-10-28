import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, StatusBar } from 'react-native';
import { useTheme } from '../../hooks/useTheme';

interface HeaderProps {
  title: string;
  subtitle?: string;
  showBack?: boolean;
  onBack?: () => void;
  rightAction?: React.ReactNode;
}

export default function Header({ title, subtitle, showBack = false, onBack, rightAction }: HeaderProps) {
  const { colors, CREWINTEL } = useTheme();

  return (
    <View style={[styles.header, { backgroundColor: CREWINTEL.navy }]}>
      <StatusBar barStyle="light-content" backgroundColor={CREWINTEL.navy} />
      <View style={styles.content}>
        {showBack ? (
          <TouchableOpacity onPress={onBack} style={styles.backButton}>
            <Text style={styles.backArrow}>←</Text>
          </TouchableOpacity>
        ) : (
          <View style={styles.spacer} />
        )}
        <View style={styles.titleContainer}>
          <Text style={styles.title} numberOfLines={1}>{title}</Text>
          {subtitle && <Text style={styles.subtitle} numberOfLines={1}>{subtitle}</Text>}
        </View>
        {rightAction ? rightAction : <View style={styles.spacer} />}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    paddingTop: 50,
    paddingBottom: 16,
    paddingHorizontal: 16,
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  backArrow: {
    color: '#FFFFFF',
    fontSize: 20,
  },
  titleContainer: {
    flex: 1,
    alignItems: 'center',
  },
  title: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '700',
  },
  subtitle: {
    color: 'rgba(255,255,255,0.7)',
    fontSize: 12,
    marginTop: 2,
  },
  spacer: {
    width: 40,
  },
});
