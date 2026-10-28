/** Sunucudan gelen belge tipi kodlarını ekranda okunur ada çevirir. */

const KEYS: Record<string, string> = {
  passport: 'documentsTab.typePassport',
  seaman_book: 'documentsTab.typeSeamanBook',
  stcw: 'documentsTab.typeStcw',
  goc: 'documentsTab.typeGoc',
  medical: 'documentsTab.typeMedical',
  contract: 'documentsTab.typeContract',
  cv: 'documentsTab.typeCv',
  other: 'documentsTab.typeOther',
};

export function documentTypeLabel(
  t: (key: string) => string,
  documentType?: string | null,
): string {
  if (!documentType) return t('documentsTab.typeOther');
  const key = KEYS[documentType.toLowerCase()];
  if (key) return t(key);
  // Bilinmeyen tip: alt çizgileri boşluğa çevirip ilk harfleri büyüt.
  return documentType
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}
