import { ApiClient } from "./api-client";

export interface AuthUser {
  readonly id: number;
  readonly username: string;
  readonly display_name: string;
  readonly email: string;
  readonly bio: string;
  readonly icon_id: number;
  readonly banner_id: number;
  readonly created_at: string;
}

export interface RegisterPayload {
  readonly display_name: string;
  readonly username: string;
  readonly email: string;
  readonly password: string;
  readonly password_confirm: string;
}

export interface LoginPayload {
  readonly username: string;
  readonly password: string;
}

function isAuthUser(value: unknown): value is AuthUser {
  if (!value || typeof value !== "object") {
    return false;
  }
  const record = value as Record<string, unknown>;
  return (
    typeof record.id === "number" &&
    typeof record.username === "string" &&
    typeof record.display_name === "string" &&
    typeof record.email === "string"
  );
}

function assertAuthUser(payload: unknown, endpoint: string): AuthUser {
  if (!isAuthUser(payload)) {
    throw new Error(
      `Invalid AuthUser payload from ${endpoint}: ${JSON.stringify(payload)} (expected user object).`,
    );
  }
  return payload;
}

/** Register a new Rankit account and set HttpOnly JWT cookies. */
export async function registerUser(
  payload: RegisterPayload,
  client: ApiClient = new ApiClient(),
): Promise<AuthUser> {
  const response = await client.post<unknown>("/api/v1/auth/register/", payload);
  return assertAuthUser(response, "/api/v1/auth/register/");
}

/** Authenticate an existing Rankit user and set HttpOnly JWT cookies. */
export async function loginUser(
  payload: LoginPayload,
  client: ApiClient = new ApiClient(),
): Promise<AuthUser> {
  const response = await client.post<unknown>("/api/v1/auth/login/", payload);
  return assertAuthUser(response, "/api/v1/auth/login/");
}

/** Renew the access cookie using the HttpOnly refresh cookie. */
export async function refreshSession(client: ApiClient = new ApiClient()): Promise<void> {
  await client.post<unknown>("/api/v1/auth/refresh/");
}

/** Clear HttpOnly JWT cookies on the backend. */
export async function logoutUser(client: ApiClient = new ApiClient()): Promise<void> {
  await client.post<unknown>("/api/v1/auth/logout/");
}

/** Fetch the authenticated user profile from the current cookie session. */
export async function fetchCurrentUser(client: ApiClient = new ApiClient()): Promise<AuthUser> {
  const response = await client.get<unknown>("/api/v1/auth/me/");
  return assertAuthUser(response, "/api/v1/auth/me/");
}
