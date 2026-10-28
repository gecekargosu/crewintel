import { Alert, Platform } from 'react-native';

/**
 * Platformdan bağımsız bilgi/onay pencereleri.
 *
 * React Native Web'de `Alert.alert` sessizce hiçbir şey yapmaz; bu yüzden
 * tarayıcıda (masaüstü denemesi, web build) "belge yüklendi" bildirimi ve
 * "çıkış yap" onayı görünmüyor, hatta çıkış yapılamıyordu. Web'de tarayıcının
 * kendi `alert`/`confirm` pencereleri kullanılır.
 */

function combine(title: string, message?: string): string {
  return [title, message].filter(Boolean).join('\n\n');
}

export function showAlert(title: string, message?: string): void {
  if (Platform.OS === 'web') {
    // eslint-disable-next-line no-alert
    window.alert(combine(title, message));
    return;
  }
  Alert.alert(title, message);
}

export function showConfirm(
  title: string,
  message: string,
  onConfirm: () => void,
  confirmLabel: string,
  cancelLabel: string,
): void {
  if (Platform.OS === 'web') {
    // eslint-disable-next-line no-alert
    if (window.confirm(combine(title, message))) onConfirm();
    return;
  }
  Alert.alert(title, message, [
    { text: cancelLabel, style: 'cancel' },
    { text: confirmLabel, style: 'destructive', onPress: onConfirm },
  ]);
}
