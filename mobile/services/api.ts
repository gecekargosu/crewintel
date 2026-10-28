import * as SecureStore from 'expo-secure-store';

// API kökü. Fiziksel cihaz/emülatör için EXPO_PUBLIC_API_URL ile LAN adresi
// verilebilir (ör. http://192.168.1.20:8000); varsayılan yerel geliştirme.
const API_BASE = (process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/+$/, '');

// Token management
export async function getToken(): Promise<string | null> {
  return SecureStore.getItemAsync('auth_token');
}

export async function setToken(token: string): Promise<void> {
  await SecureStore.setItemAsync('auth_token', token);
}

export async function removeToken(): Promise<void> {
  await SecureStore.deleteItemAsync('auth_token');
}

export async function getUserRole(): Promise<string | null> {
  return SecureStore.getItemAsync('user_role');
}

export async function setUserRole(role: string): Promise<void> {
  await SecureStore.setItemAsync('user_role', role);
}

export async function getUserEmail(): Promise<string | null> {
  return SecureStore.getItemAsync('user_email');
}

export async function setUserEmail(email: string): Promise<void> {
  await SecureStore.setItemAsync('user_email', email);
}

export async function clearAuth(): Promise<void> {
  await SecureStore.deleteItemAsync('auth_token');
  await SecureStore.deleteItemAsync('user_role');
  await SecureStore.deleteItemAsync('user_email');
  await SecureStore.deleteItemAsync('user_name');
  await SecureStore.deleteItemAsync('user_id');
}

function buildQuery(params?: Record<string, string | number | boolean | undefined>): string {
  if (!params) return '';
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      search.append(key, String(value));
    }
  });
  const query = search.toString();
  return query ? `?${query}` : '';
}

// Generic API call
async function apiCall(
  method: string,
  path: string,
  body?: any,
  requireAuth: boolean = true
): Promise<any> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (requireAuth) {
    const token = await getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  const config: RequestInit = {
    method,
    headers,
  };

  if (body && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
    config.body = JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE}${path}`, config);

  if (response.status === 401) {
    await clearAuth();
    throw new Error('Oturumunuz sona erdi. Lütfen tekrar giriş yapın.');
  }

  if (response.status === 403) {
    throw new Error('Bu işlem için yetkiniz yok.');
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const detail = errorData.detail;
    const message = typeof detail === 'string'
      ? detail
      : Array.isArray(detail) && detail[0]?.msg
        ? detail[0].msg
        : `İşlem başarısız (${response.status})`;
    throw new Error(message);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

// Auth endpoints
export const authAPI = {
  login: (email: string, password: string) =>
    apiCall('POST', '/api/auth/login', { email, password }, false),

  register: (data: any) =>
    apiCall('POST', '/api/auth/register', data, false),

  me: () => apiCall('GET', '/api/auth/me'),
};

// Crew/Profile endpoints (personel portalı)
export const crewAPI = {
  me: () => apiCall('GET', '/api/portal/me'),

  /**
   * /api/portal/me/full yanıtı { profile, documents, contract, vessel, ... }
   * şeklinde iç içedir. Ekranlar düz alan beklediği için profil alanları
   * köke taşınır; documents/contract/vessel/eligibility kökte kalır.
   */
  meFull: async () => {
    const data = await apiCall('GET', '/api/portal/me/full');
    if (!data) return null;
    return {
      ...(data.profile || {}),
      full_name: [data.profile?.first_name, data.profile?.last_name]
        .filter(Boolean)
        .join(' ')
        .trim() || null,
      // Ekranların kullandığı ek adlar
      availability_status: (data.profile?.availability || '').toUpperCase(),
      documents: data.documents || [],
      contract: data.contract || null,
      contracts: data.contract ? [data.contract] : [],
      vessel: data.vessel || null,
      eligibility: data.eligibility || null,
      required_types: data.required_types || [],
    };
  },

  // Portal yalnızca iletişim bilgisi güncellemesine izin verir.
  updateProfile: (data: { phone?: string; email?: string }) =>
    apiCall('PUT', '/api/portal/contact', data),

  updatePreferences: (data: any) =>
    apiCall('PUT', '/api/portal/preferences', data),

  setJobSeeking: (jobSeeking: boolean) =>
    apiCall('PATCH', '/api/portal/job-seeking', { job_seeking: jobSeeking }),
};

// Documents endpoints
export const documentsAPI = {
  myDocuments: () => apiCall('GET', '/api/portal/documents'),

  upload: async (formData: FormData) => {
    const token = await getToken();
    const response = await fetch(`${API_BASE}/api/portal/documents`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    });
    if (response.status === 401) {
      await clearAuth();
      throw new Error('Oturumunuz sona erdi. Lütfen tekrar giriş yapın.');
    }
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(typeof err.detail === 'string' ? err.detail : 'Yükleme başarısız');
    }
    return response.json();
  },
};

// Jobs endpoints (personel portalı uçları)
export const jobsAPI = {
  list: (params?: Record<string, string>) =>
    apiCall('GET', `/api/portal/jobs${buildQuery(params || {})}`),

  get: (id: number) => apiCall('GET', `/api/portal/jobs/${id}`),

  apply: (jobId: number) => apiCall('POST', `/api/portal/jobs/${jobId}/apply`),

  recommended: () => apiCall('GET', '/api/portal/jobs/recommended'),

  myApplications: () => apiCall('GET', '/api/portal/applications'),
};

// Contracts endpoints
export const contractsAPI = {
  myContracts: () => apiCall('GET', '/api/portal/contracts/me'),
};

// Vessel endpoints
export const vesselAPI = {
  myVessel: () => apiCall('GET', '/api/portal/vessel/me'),
};

// Messages endpoints
export const messagesAPI = {
  // Backend konuşma kaydı `other_user` altında isim döner; liste ekranı düz
  // `participant_name` beklediği için burada normalize edilir.
  conversations: async () => {
    const data = await apiCall('GET', '/api/messages/conversations');
    if (!Array.isArray(data)) return [];
    return data.map((conversation: any) => ({
      ...conversation,
      participant_name: conversation.other_user?.full_name || conversation.subject || 'Kullanıcı',
      last_message_time: conversation.last_message_at || conversation.created_at,
    }));
  },

  // Backend { conversation, messages } döner; ekranlar dizi bekler.
  messages: async (conversationId: number) => {
    const data = await apiCall('GET', `/api/messages/conversations/${conversationId}`);
    if (Array.isArray(data)) return data;
    return data?.messages || [];
  },

  send: (conversationId: number, text: string, kind: string = 'chat') =>
    apiCall('POST', `/api/messages/conversations/${conversationId}`, { body: text, kind }),

  markRead: (messageId: number) =>
    apiCall('PATCH', `/api/messages/${messageId}/read`),

  // Backend konuşma oluştururken `crew_user_id` bekler.
  createConversation: (crewUserId: number, subject?: string) =>
    apiCall('POST', '/api/messages/conversations', { crew_user_id: crewUserId, subject }),
};

// Notifications endpoints (personel portalı)
export const notificationsAPI = {
  list: () => apiCall('GET', '/api/portal/notifications'),

  markRead: (id: number) => apiCall('POST', `/api/portal/notifications/${id}/read`),
};

// Device endpoints
export const deviceAPI = {
  register: (data: { platform: string; push_token: string; device_name?: string }) =>
    apiCall('POST', '/api/devices', data),
};
