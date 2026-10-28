import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { useTheme } from '../../hooks/useTheme';
import { useAuth } from '../../context/AuthContext';
import Header from '../../components/ui/Header';
import { messagesAPI } from '../../services/api';
import { useI18n } from '../../context/I18nContext';

export default function ConversationScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams();
  const { colors, CREWINTEL } = useTheme();
  const { user } = useAuth();
  const { t } = useI18n();
  const [messages, setMessages] = useState<any[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const flatListRef = useRef<FlatList>(null);

  const loadMessages = async () => {
    try {
      const data = await messagesAPI.messages(Number(id));
      // API katmanı mesaj dizisini zaten eski→yeni sırada döndürür.
      setMessages(Array.isArray(data) ? data : []);
    } catch (error) {
      console.log('Messages load error:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMessages();
  }, [id]);

  const handleSend = async () => {
    if (!newMessage.trim() || sending) return;

    setSending(true);
    try {
      const sent = await messagesAPI.send(Number(id), newMessage.trim());
      setMessages((prev) => [...prev, sent]);
      setNewMessage('');
    } catch (error: any) {
      console.log('Send error:', error);
    } finally {
      setSending(false);
    }
  };

  const renderMessage = ({ item }: { item: any }) => {
    const isMine =
      item.sender_user_id === user?.id || item.sender_user_id === user?.crew_member_id;
    return (
      <View style={[styles.messageBubble, isMine ? styles.myMessage : styles.otherMessage]}>
        <Text style={[styles.messageText, isMine ? styles.myMessageText : styles.otherMessageText]}>
          {item.body || item.text || item.content}
        </Text>
        <Text style={[styles.messageTime, isMine ? styles.myMessageTime : styles.otherMessageTime]}>
          {item.created_at ? new Date(item.created_at).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' }) : ''}
        </Text>
      </View>
    );
  };

  return (
    <KeyboardAvoidingView
      style={[styles.container, { backgroundColor: colors.background }]}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={0}
    >
      <Header title={t('messages.conversation')} showBack onBack={() => router.back()} />

      <FlatList
        ref={flatListRef}
        data={messages}
        renderItem={renderMessage}
        keyExtractor={(item) => item.id?.toString() || Math.random().toString()}
        contentContainerStyle={styles.messageList}
        inverted={false}
        ListEmptyComponent={
          !loading ? (
            <View style={styles.emptyContainer}>
              <Text style={[styles.emptyText, { color: colors.textSecondary }]}>
                {t('messages.noMessages')}
              </Text>
            </View>
          ) : null
        }
      />

      <View style={[styles.inputContainer, { backgroundColor: colors.card, borderTopColor: colors.border }]}>
        <TextInput
          style={[styles.input, { color: colors.text, backgroundColor: colors.grey100 }]}
          value={newMessage}
          onChangeText={setNewMessage}
          placeholder={t('messages.typePlaceholder')}
          placeholderTextColor={colors.grey400}
          multiline
          maxLength={1000}
        />
        <TouchableOpacity
          style={[
            styles.sendButton,
            { backgroundColor: newMessage.trim() ? CREWINTEL.orange : colors.grey300 },
          ]}
          onPress={handleSend}
          disabled={!newMessage.trim() || sending}
        >
          <Text style={styles.sendIcon}>↑</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  messageList: {
    padding: 16,
    flexGrow: 1,
  },
  messageBubble: {
    maxWidth: '80%',
    padding: 12,
    borderRadius: 16,
    marginBottom: 8,
  },
  myMessage: {
    alignSelf: 'flex-end',
    backgroundColor: '#E8731A',
    borderBottomRightRadius: 4,
  },
  otherMessage: {
    alignSelf: 'flex-start',
    backgroundColor: '#F5F5F7',
    borderBottomLeftRadius: 4,
  },
  messageText: {
    fontSize: 15,
    lineHeight: 20,
  },
  myMessageText: {
    color: '#FFFFFF',
  },
  otherMessageText: {
    color: '#0A1628',
  },
  messageTime: {
    fontSize: 10,
    marginTop: 4,
    alignSelf: 'flex-end',
  },
  myMessageTime: {
    color: 'rgba(255,255,255,0.7)',
  },
  otherMessageTime: {
    color: '#8E8E93',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    fontSize: 14,
    textAlign: 'center',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: 12,
    borderTopWidth: 1,
  },
  input: {
    flex: 1,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 15,
    maxHeight: 100,
  },
  sendButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 8,
  },
  sendIcon: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '700',
  },
});
