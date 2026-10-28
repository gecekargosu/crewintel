import React from 'react';
import { View, Text, StyleSheet, ViewStyle } from 'react-native';
import { useTheme } from '../../hooks/useTheme';

interface BadgeProps {
  text: string;
  variant?: 'success' | 'warning' | 'danger' | 'info' | 'neutral';
  size?: 'sm' | 'md';
  style?: ViewStyle;
}

export default function Badge({ text, variant = 'neutral', size = 'sm', style }: BadgeProps) {
  const { colors } = useTheme();

  const getBgColor = () => {
    switch (variant) {
      case 'success': return '#34C75920';
      case 'warning': return '#FF950020';
      case 'danger': return '#FF3B3020';
      case 'info': return '#5AC8FA20';
      default: return colors.grey200;
    }
  };

  const getTextColor = () => {
    switch (variant) {
      case 'success': return '#34C759';
      case 'warning': return '#FF9500';
      case 'danger': return '#FF3B30';
      case 'info': return '#5AC8FA';
      default: return colors.grey600;
    }
  };

  return (
    <View
      style={[
        styles.badge,
        {
          backgroundColor: getBgColor(),
          height: size === 'sm' ? 22 : 28,
          paddingHorizontal: size === 'sm' ? 8 : 12,
        },
        style,
      ]}
    >
      <Text
        style={[
          styles.text,
          {
            color: getTextColor(),
            fontSize: size === 'sm' ? 11 : 13,
          },
        ]}
      >
        {text}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    borderRadius: 6,
    alignSelf: 'flex-start',
    justifyContent: 'center',
  },
  text: {
    fontWeight: '600',
  },
});
