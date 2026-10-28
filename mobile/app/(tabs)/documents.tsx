import React, { useCallback, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import { useFocusEffect } from 'expo-router';

import { useTheme } from '../../hooks/useTheme';
import { useI18n } from '../../context/I18nContext';
import Header from '../../components/ui/Header';
import Card from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import { documentsAPI } from '../../services/api';
import { showAlert } from '../../utils/dialogs';
import { documentTypeLabel } from '../../utils/documentTypes';

/** Sunucu PDF/TXT/DOCX/XLSX ve resimleri kabul eder; resimler OCR ile okunur. */
const PICKER_TYPES = [
  'application/pdf',
  'text/plain',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'image/*',
];

type BadgeVariant = 'success' | 'warning' | 'danger' | 'info' | 'neutral';

function statusOf(doc: any, t: (key: string) => string): { label: string; variant: BadgeVariant } {
  const status = doc.status || doc.match_status || '';
  switch (status) {
    case 'expired':
      return { label: t('documentsTab.statusExpired'), variant: 'danger' };
    case 'urgent':
      return { label: t('documentsTab.statusUrgent'), variant: 'danger' };
    case 'approaching':
      return { label: t('documentsTab.statusApproaching'), variant: 'warning' };
    case 'valid':
      return { label: t('documentsTab.statusValid'), variant: 'success' };
    case 'pending_approval':
      return { label: t('documentsTab.statusPendingApproval'), variant: 'info' };
    case 'pending':
      return { label: t('documentsTab.statusPending'), variant: 'info' };
    case 'processing':
      return { label: t('documentsTab.statusProcessing'), variant: 'info' };
    case 'no_date':
      return { label: t('documentsTab.statusNoDate'), variant: 'neutral' };
    default:
      return { label: status || t('documentsTab.statusUnknown'), variant: 'neutral' };
  }
}

export default function DocumentsScreen() {
  const { colors, CREWINTEL } = useTheme();
  const { t } = useI18n();
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await documentsAPI.myDocuments();
      setDocuments(Array.isArray(data) ? data : []);
      setError(null);
    } catch (err: any) {
      setError(err?.message || t('documentsTab.loadError'));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [t]);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  const pickAndUpload = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: PICKER_TYPES,
        multiple: true,
        copyToCacheDirectory: true,
      });
      if (result.canceled || !result.assets?.length) return;

      setUploading(true);
      for (const asset of result.assets) {
        const formData = new FormData();
        formData.append('file', {
          uri: asset.uri,
          name: asset.name || 'document.pdf',
          type: asset.mimeType || 'application/octet-stream',
        } as any);
        await documentsAPI.upload(formData);
      }
      await load();
      showAlert(t('documentsTab.uploadDone'), t('documentsTab.uploadDoneHint'));
    } catch (err: any) {
      showAlert(t('common.error'), err?.message || t('documentsTab.uploadError'));
    } finally {
      setUploading(false);
    }
  };

  const openDocument = (doc: any) => {
    const status = statusOf(doc, t);
    showAlert(
      documentTypeLabel(t, doc.document_type),
      [
        doc.issue_date ? `${t('documentsTab.issueDate')}: ${doc.issue_date}` : null,
        doc.expiry_date ? `${t('documentsTab.expiryDate')}: ${doc.expiry_date}` : null,
        `${t('documentsTab.status')}: ${status.label}`,
        doc.original_filename ? `📄 ${doc.original_filename}` : null,
      ]
        .filter(Boolean)
        .join('\n')
    );
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <Header title={t('documentsTab.title')} subtitle={t('documentsTab.subtitle')} />

      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
      >
        <Card variant="elevated" style={styles.uploadCard}>
          <Text style={[styles.uploadTitle, { color: colors.text }]}>{t('documentsTab.uploadTitle')}</Text>
          <Text style={[styles.uploadHint, { color: colors.textSecondary }]}>
            {t('documentsTab.uploadHint')}
          </Text>
          <TouchableOpacity
            style={[styles.uploadButton, uploading && { opacity: 0.6 }]}
            onPress={pickAndUpload}
            disabled={uploading}
          >
            {uploading ? (
              <ActivityIndicator color="#FFFFFF" />
            ) : (
              <Text style={styles.uploadButtonText}>📎 {t('documentsTab.uploadButton')}</Text>
            )}
          </TouchableOpacity>
        </Card>

        {error && (
          <Card style={{ borderLeftWidth: 4, borderLeftColor: '#FF3B30' }}>
            <Text style={{ color: '#FF3B30' }}>{error}</Text>
          </Card>
        )}

        {loading && (
          <View style={styles.center}>
            <ActivityIndicator color={CREWINTEL.orange} />
            <Text style={{ color: colors.textSecondary, marginTop: 8 }}>{t('common.loading')}</Text>
          </View>
        )}

        {!loading && documents.length === 0 && !error && (
          <Card>
            <Text style={{ color: colors.textSecondary, textAlign: 'center' }}>{t('documentsTab.empty')}</Text>
          </Card>
        )}

        {documents.map((doc) => {
          const status = statusOf(doc, t);
          return (
            <TouchableOpacity key={doc.id} onPress={() => openDocument(doc)} activeOpacity={0.8}>
              <Card style={styles.docCard}>
                <View style={styles.docRow}>
                  <View style={{ flex: 1 }}>
                    <Text style={[styles.docType, { color: colors.text }]}>
                      {documentTypeLabel(t, doc.document_type)}
                    </Text>
                    {doc.original_filename ? (
                      <Text style={[styles.docFile, { color: colors.textSecondary }]} numberOfLines={1}>
                        {doc.original_filename}
                      </Text>
                    ) : null}
                    {doc.expiry_date ? (
                      <Text style={[styles.docDate, { color: colors.textSecondary }]}>
                        {t('documentsTab.expiryDate')}: {doc.expiry_date}
                      </Text>
                    ) : null}
                  </View>
                  <Badge text={status.label} variant={status.variant} />
                </View>
              </Card>
            </TouchableOpacity>
          );
        })}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: 16, paddingBottom: 40 },
  uploadCard: { marginBottom: 16 },
  uploadTitle: { fontSize: 16, fontWeight: '700', marginBottom: 6 },
  uploadHint: { fontSize: 13, marginBottom: 12, lineHeight: 18 },
  uploadButton: {
    backgroundColor: '#EA580C',
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: 'center',
  },
  uploadButtonText: { color: '#FFFFFF', fontWeight: '700', fontSize: 15 },
  center: { alignItems: 'center', paddingVertical: 24 },
  docCard: { marginBottom: 10 },
  docRow: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  docType: { fontSize: 15, fontWeight: '700' },
  docFile: { fontSize: 12, marginTop: 2 },
  docDate: { fontSize: 12, marginTop: 2 },
});
