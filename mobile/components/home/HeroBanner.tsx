import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated, Dimensions, TouchableOpacity } from 'react-native';
import { useTheme } from '../../hooks/useTheme';
import { useI18n } from '../../context/I18nContext';
import Badge from '../ui/Badge';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

// RN tiplerinde her sürümde bulunmayan absoluteFillObject yerine açık tanım.
const ABSOLUTE_FILL = {
  position: 'absolute' as const,
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
};

interface HeroBannerProps {
  userName: string;
  availabilityStatus?: string;
  documentCount?: number;
  contractCount?: number;
  onCtaPress?: () => void;
}

export default function HeroBanner({
  userName,
  availabilityStatus,
  documentCount = 0,
  contractCount = 0,
  onCtaPress,
}: HeroBannerProps) {
  const { colors, CREWINTEL } = useTheme();
  const { t } = useI18n();
  
  // Animation values
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const opacityAnim = useRef(new Animated.Value(0)).current;
  const translateXAnim = useRef(new Animated.Value(20)).current;

  useEffect(() => {
    // Fade in animation
    Animated.timing(opacityAnim, {
      toValue: 1,
      duration: 800,
      useNativeDriver: true,
    }).start();

    // Subtle scale animation for background
    const scaleLoop = Animated.loop(
      Animated.sequence([
        Animated.timing(scaleAnim, {
          toValue: 1.04,
          duration: 8000,
          useNativeDriver: true,
        }),
        Animated.timing(scaleAnim, {
          toValue: 1,
          duration: 8000,
          useNativeDriver: true,
        }),
      ])
    );
    scaleLoop.start();

    // Text slide in
    Animated.timing(translateXAnim, {
      toValue: 0,
      duration: 600,
      useNativeDriver: true,
    }).start();

    return () => {
      scaleLoop.stop();
    };
  }, []);

  const getAvailabilityLabel = () => {
    switch (availabilityStatus) {
      case 'AVAILABLE_NOW': return { label: t('profile.activeDuty'), variant: 'success' as const };
      case 'AVAILABLE_SOON': return { label: 'Yakında Müsait', variant: 'warning' as const };
      case 'CURRENTLY_EMPLOYED': return { label: t('profile.activeDuty'), variant: 'info' as const };
      case 'LOOKING': return { label: t('profile.jobSeeking'), variant: 'success' as const };
      default: return { label: t('profile.notDefined'), variant: 'neutral' as const };
    }
  };

  const availability = getAvailabilityLabel();

  return (
    <View style={styles.container}>
      {/* Animated Background */}
      <Animated.View
        style={[
          styles.background,
          {
            backgroundColor: CREWINTEL.navy,
            transform: [{ scale: scaleAnim }],
          },
        ]}
      >
        {/* Gradient Overlay */}
        <View style={styles.gradientOverlay} />
        
        {/* Maritime Pattern Overlay */}
        <View style={styles.patternOverlay}>
          <View style={styles.wave1} />
          <View style={styles.wave2} />
          <View style={styles.wave3} />
        </View>
      </Animated.View>

      {/* Content */}
      <Animated.View
        style={[
          styles.content,
          {
            opacity: opacityAnim,
            transform: [{ translateX: translateXAnim }],
          },
        ]}
      >
        {/* Greeting */}
        <Text style={styles.greeting}>{t('home.greeting')}, {userName}</Text>

        {/* Hero Title */}
        <Text style={styles.heroTitle}>{t('home.heroTitle')}</Text>

        {/* Hero Subtitle */}
        <Text style={styles.heroSubtitle}>{t('home.heroSubtitle')}</Text>

        {/* Status Row */}
        <View style={styles.statusRow}>
          <Badge text={availability.label} variant={availability.variant} size="md" />
          {documentCount > 0 && (
            <View style={styles.statBadge}>
              <Text style={styles.statBadgeText}>📄 {documentCount}</Text>
            </View>
          )}
          {contractCount > 0 && (
            <View style={styles.statBadge}>
              <Text style={styles.statBadgeText}>📋 {contractCount}</Text>
            </View>
          )}
        </View>

        {/* CTA Button */}
        <TouchableOpacity
          style={[styles.ctaButton, { backgroundColor: CREWINTEL.orange }]}
          onPress={onCtaPress}
          activeOpacity={0.8}
        >
          <Text style={styles.ctaText}>{t('home.heroCta')}</Text>
          <Text style={styles.ctaArrow}>→</Text>
        </TouchableOpacity>
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    height: 340,
    position: 'relative',
    overflow: 'hidden',
  },
  background: {
    ...ABSOLUTE_FILL,
    transform: [{ scale: 1 }],
  },
  gradientOverlay: {
    ...ABSOLUTE_FILL,
    backgroundColor: 'rgba(10, 22, 40, 0.55)',
  },
  patternOverlay: {
    ...ABSOLUTE_FILL,
    overflow: 'hidden',
  },
  wave1: {
    position: 'absolute',
    bottom: 0,
    left: -50,
    right: -50,
    height: 120,
    backgroundColor: 'rgba(232, 115, 26, 0.08)',
    borderRadius: '50%',
    transform: [{ rotate: '-5deg' }],
  },
  wave2: {
    position: 'absolute',
    bottom: -30,
    left: -30,
    right: -30,
    height: 100,
    backgroundColor: 'rgba(232, 115, 26, 0.05)',
    borderRadius: '50%',
    transform: [{ rotate: '3deg' }],
  },
  wave3: {
    position: 'absolute',
    bottom: 10,
    left: 20,
    right: 20,
    height: 60,
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderRadius: '50%',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 24,
    paddingTop: 60,
  },
  greeting: {
    fontSize: 15,
    color: 'rgba(255, 255, 255, 0.7)',
    marginBottom: 8,
  },
  heroTitle: {
    fontSize: 28,
    fontWeight: '800',
    color: '#FFFFFF',
    lineHeight: 34,
    marginBottom: 12,
  },
  heroSubtitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.75)',
    lineHeight: 20,
    marginBottom: 20,
    maxWidth: 320,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 24,
  },
  statBadge: {
    backgroundColor: 'rgba(255, 255, 255, 0.12)',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
  },
  statBadgeText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  ctaButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    paddingHorizontal: 28,
    borderRadius: 12,
    alignSelf: 'flex-start',
    gap: 8,
  },
  ctaText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  ctaArrow: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '600',
  },
});
