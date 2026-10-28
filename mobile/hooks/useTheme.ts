import { useColorScheme } from 'react-native';
import Colors from '../constants/Colors';

export function useTheme() {
  // useColorScheme 'light' | 'dark' | null döner; bilinmeyen/null değerlerde
  // karanlık tema kullanılır (Colors'ta yalnızca bu iki palet var).
  const scheme = useColorScheme();
  const colorScheme: 'light' | 'dark' = scheme === 'light' ? 'light' : 'dark';
  const colors = Colors[colorScheme];
  const CREWINTEL = Colors.CREWINTEL;

  return {
    colors,
    CREWINTEL,
    isDark: colorScheme === 'dark',
  };
}
