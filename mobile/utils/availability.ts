/**
 * Personel müsaitlik durumu.
 *
 * Backend `crew_members.availability` alanı şu kodları kullanır:
 * available | on_board | on_leave | not_available. Ekranlar daha önce
 * "AVAILABLE_NOW" gibi var olmayan bir kod beklediği için gerçek personel
 * "Tanımlanmamış" görünüyordu; eşleme tek yerde toplandı.
 */

export type BadgeVariant = 'success' | 'warning' | 'info' | 'danger' | 'neutral';

const MAP: Record<string, { key: string; variant: BadgeVariant }> = {
  AVAILABLE: { key: 'profile.availableNow', variant: 'success' },
  AVAILABLE_NOW: { key: 'profile.availableNow', variant: 'success' },
  AVAILABLE_SOON: { key: 'profile.availableSoon', variant: 'warning' },
  ON_BOARD: { key: 'profile.activeDuty', variant: 'info' },
  EMPLOYED: { key: 'profile.activeDuty', variant: 'info' },
  ON_LEAVE: { key: 'profile.onLeave', variant: 'warning' },
  NOT_AVAILABLE: { key: 'profile.notAvailable', variant: 'neutral' },
  LOOKING: { key: 'profile.jobSeeking', variant: 'success' },
};

export function availabilityBadge(
  t: (key: string) => string,
  raw?: string | null,
): { label: string; variant: BadgeVariant } {
  const code = (raw || '').trim().toUpperCase().replace(/[\s-]+/g, '_');
  const match = MAP[code];
  if (!match) return { label: t('profile.notDefined'), variant: 'neutral' };
  return { label: t(match.key), variant: match.variant };
}
