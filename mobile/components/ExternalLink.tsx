import { Link, type Href } from 'expo-router';
import * as WebBrowser from 'expo-web-browser';
import type { ComponentProps } from 'react';
import { Platform } from 'react-native';

/**
 * Dış bağlantı bileşeni.
 *
 * `href` çalışma zamanında dış URL'dir; expo-router'ın tipli rota birleşimi
 * dış adresleri kabul etmediği için `Href` tipine daraltılıyor (web'de normal
 * bağlantı, telefonda uygulama içi tarayıcı açılır).
 */
export function ExternalLink(props: Omit<ComponentProps<typeof Link>, 'href'> & { href: string }) {
  return (
    <Link
      target="_blank"
      {...props}
      href={props.href as Href}
      onPress={(e) => {
        if (Platform.OS !== 'web') {
          // Prevent the default behavior of linking to the default browser on native.
          e.preventDefault();
          // Open the link in an in-app browser.
          WebBrowser.openBrowserAsync(props.href);
        }
      }}
    />
  );
}
