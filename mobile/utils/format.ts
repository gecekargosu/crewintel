/** Sözleşme süresi gibi serbest metin alanlarını tutarlı gösterir. */

/**
 * Backend süre alanı bazen sadece sayı ("6"), bazen birimle birlikte
 * ("6 ay") gelir. Sayıysa birim eklenir; metin zaten birim içeriyorsa
 * "6 ay ay" gibi tekrar oluşmaz.
 */
export function formatDuration(value?: number | string | null, unit = 'ay'): string {
  if (value === null || value === undefined || value === '') return '';
  const text = String(value).trim();
  return /^\d+([.,]\d+)?$/.test(text) ? `${text} ${unit}` : text;
}
