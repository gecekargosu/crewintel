import { Tabs } from 'expo-router';
import { useTheme } from '../../hooks/useTheme';
import { useAuth } from '../../context/AuthContext';
import { useI18n } from '../../context/I18nContext';
import { Text } from 'react-native';

export default function TabLayout() {
  const { colors, CREWINTEL } = useTheme();
  const { user } = useAuth();
  const { t } = useI18n();

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: CREWINTEL.orange,
        tabBarInactiveTintColor: colors.grey500,
        tabBarStyle: {
          backgroundColor: CREWINTEL.navy,
          borderTopColor: CREWINTEL.navyLight,
          borderTopWidth: 0,
          height: 85,
          paddingBottom: 20,
          paddingTop: 8,
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '600',
        },
        headerStyle: {
          backgroundColor: CREWINTEL.navy,
        },
        headerTintColor: '#FFFFFF',
        headerTitleStyle: {
          fontWeight: '700',
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: t('nav.home'),
          headerTitle: 'CREWINTEL',
          headerShown: false,
          tabBarIcon: ({ color }) => <Text style={{ fontSize: 22, color }}>🏠</Text>,
        }}
      />
      <Tabs.Screen
        name="jobs"
        options={{
          title: t('nav.jobs'),
          headerShown: false,
          tabBarIcon: ({ color }) => <Text style={{ fontSize: 22, color }}>💼</Text>,
        }}
      />
      <Tabs.Screen
        name="applications"
        options={{
          title: t('nav.applications'),
          headerShown: false,
          tabBarIcon: ({ color }) => <Text style={{ fontSize: 22, color }}>📋</Text>,
        }}
      />
      <Tabs.Screen
        name="documents"
        options={{
          title: t('nav.documents'),
          headerShown: false,
          tabBarIcon: ({ color }) => <Text style={{ fontSize: 22, color }}>📄</Text>,
        }}
      />
      <Tabs.Screen
        name="messages"
        options={{
          title: t('nav.messages'),
          headerShown: false,
          tabBarIcon: ({ color }) => <Text style={{ fontSize: 22, color }}>💬</Text>,
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: t('nav.profile'),
          headerShown: false,
          tabBarIcon: ({ color }) => <Text style={{ fontSize: 22, color }}>👤</Text>,
        }}
      />
    </Tabs>
  );
}
