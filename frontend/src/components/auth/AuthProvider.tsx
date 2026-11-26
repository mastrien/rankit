"use client";

import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { ApiClient, ApiClientError } from "@/lib/api-client";
import {
  type AuthUser,
  fetchCurrentUser,
  type LoginPayload,
  loginUser,
  logoutUser,
  refreshSession,
  type RegisterPayload,
  registerUser,
} from "@/lib/auth-api";

export interface AuthContextValue {
  readonly user: AuthUser | null;
  readonly isLoading: boolean;
  readonly login: (payload: LoginPayload) => Promise<AuthUser>;
  readonly register: (payload: RegisterPayload) => Promise<AuthUser>;
  readonly logout: () => Promise<void>;
  readonly refreshUser: () => Promise<AuthUser | null>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export interface AuthProviderProps {
  readonly children: ReactNode;
  readonly apiClient?: ApiClient;
  readonly initialUser?: AuthUser | null;
  readonly skipInitialFetch?: boolean;
}

/** Provide cookie-backed authentication state and actions across the React tree. */
export function AuthProvider({
  children,
  apiClient,
  initialUser = null,
  skipInitialFetch = false,
}: AuthProviderProps) {
  const client = useMemo(() => apiClient ?? new ApiClient(), [apiClient]);
  const [user, setUser] = useState<AuthUser | null>(initialUser);
  const [isLoading, setIsLoading] = useState<boolean>(!skipInitialFetch && initialUser === null);
  const sessionVersionRef = useRef(0);

  const applyUserIfCurrent = useCallback((version: number, nextUser: AuthUser | null): boolean => {
    if (version !== sessionVersionRef.current) {
      return false;
    }
    setUser(nextUser);
    return true;
  }, []);

  const refreshUser = useCallback(async (): Promise<AuthUser | null> => {
    const version = ++sessionVersionRef.current;
    try {
      const current = await fetchCurrentUser(client);
      applyUserIfCurrent(version, current);
      return current;
    } catch (error) {
      if (error instanceof ApiClientError && error.status === 401) {
        try {
          await refreshSession(client);
          const retried = await fetchCurrentUser(client);
          applyUserIfCurrent(version, retried);
          return retried;
        } catch {
          applyUserIfCurrent(version, null);
          return null;
        }
      }
      applyUserIfCurrent(version, null);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [applyUserIfCurrent, client]);

  useEffect(() => {
    if (skipInitialFetch || initialUser !== null) {
      return;
    }
    void refreshUser();
  }, [initialUser, refreshUser, skipInitialFetch]);

  const login = useCallback(
    async (payload: LoginPayload): Promise<AuthUser> => {
      const authenticated = await loginUser(payload, client);
      sessionVersionRef.current += 1;
      setUser(authenticated);
      return authenticated;
    },
    [client],
  );

  const register = useCallback(
    async (payload: RegisterPayload): Promise<AuthUser> => {
      const created = await registerUser(payload, client);
      sessionVersionRef.current += 1;
      setUser(created);
      return created;
    },
    [client],
  );

  const logout = useCallback(async (): Promise<void> => {
    sessionVersionRef.current += 1;
    try {
      await logoutUser(client);
    } catch {
      // Always clear local session state even if the network/backend logout fails.
    } finally {
      setUser(null);
    }
  }, [client]);

  const value = useMemo<AuthContextValue>(
    () => ({ user, isLoading, login, register, logout, refreshUser }),
    [user, isLoading, login, register, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/** Read authentication state; throws if used outside AuthProvider. */
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used inside an <AuthProvider>.");
  }
  return ctx;
}
