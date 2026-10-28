import React, { createContext, useContext, useEffect, useState } from 'react';
import { authAPI, setToken, setUserRole, setUserEmail, clearAuth, getToken } from '../services/api';
import { useI18n } from './I18nContext';

/** Mobil uygulama yalnızca personel portalını (crew) kullanır. */
const MOBILE_ROLE = 'crew';

interface User {
  id: number;
  email: string;
  role: string;
  crew_member_id?: number;
  is_active: boolean;
  full_name?: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: any) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  isLoading: true,
  isAuthenticated: false,
  login: async () => {},
  register: async () => {},
  logout: async () => {},
  refreshUser: async () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { t } = useI18n();

  /**
   * Oturumu doğrular. Yönetici/İK/misafir hesapları mobil uygulamaya
   * alınmaz: portal uçları bu rollerde 403 döndüğü için uygulama tüm
   * ekranlarda boş kalıyordu. Burada anlaşılır bir mesajla giriş engellenir.
   */
  const staffError = () =>
    new Error(`${t('auth.staffOnlyTitle')} — ${t('auth.staffOnlyHint')}`);

  const refreshUser = async () => {
    try {
      const token = await getToken();
      if (!token) {
        setUser(null);
        return;
      }
      const me = await authAPI.me();
      if (me.role !== MOBILE_ROLE) {
        await clearAuth();
        setUser(null);
        throw staffError();
      }
      setUser(me);
      if (me.role) await setUserRole(me.role);
      if (me.email) await setUserEmail(me.email);
    } catch (error) {
      console.log('Auth check failed:', error);
      setUser(null);
      throw error;
    }
  };

  useEffect(() => {
    const initAuth = async () => {
      try {
        const token = await getToken();
        if (token) {
          await refreshUser();
        }
      } catch (error) {
        console.log('Init auth error:', error);
      } finally {
        setIsLoading(false);
      }
    };
    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    const result = await authAPI.login(email, password);
    const role = result?.user?.role;
    if (role && role !== MOBILE_ROLE) {
      // Token hiç saklanmaz: personel olmayan hesap mobilde oturum açamaz.
      throw staffError();
    }
    await setToken(result.access_token);
    try {
      await refreshUser();
    } catch (error) {
      await clearAuth();
      throw error;
    }
  };

  const register = async (data: any) => {
    await authAPI.register(data);
  };

  const logout = async () => {
    await clearAuth();
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
