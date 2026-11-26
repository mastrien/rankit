import { ApiClient } from "./api-client";

export interface UserSummary {
  readonly id: number;
  readonly username: string;
  readonly display_name: string;
  readonly icon_id: number;
}

export interface ProfileDetail {
  readonly id: number;
  readonly username: string;
  readonly display_name: string;
  readonly bio: string;
  readonly icon_id: number;
  readonly banner_id: number;
  readonly followers_count: number;
  readonly following_count: number;
  readonly is_following: boolean;
  readonly is_self: boolean;
  readonly created_at: string;
}

export interface ProfilePresets {
  readonly icons: readonly number[];
  readonly banners: readonly number[];
}

export interface UpdateProfilePayload {
  readonly display_name: string;
  readonly bio: string;
  readonly icon_id: number;
  readonly banner_id: number;
}

function isUserSummary(value: unknown): value is UserSummary {
  if (!value || typeof value !== "object") {
    return false;
  }
  const record = value as Record<string, unknown>;
  return (
    typeof record.id === "number" &&
    typeof record.username === "string" &&
    typeof record.display_name === "string" &&
    typeof record.icon_id === "number"
  );
}

function isProfileDetail(value: unknown): value is ProfileDetail {
  if (!value || typeof value !== "object") {
    return false;
  }
  const record = value as Record<string, unknown>;
  return (
    typeof record.id === "number" &&
    typeof record.username === "string" &&
    typeof record.display_name === "string" &&
    typeof record.bio === "string" &&
    typeof record.icon_id === "number" &&
    typeof record.banner_id === "number" &&
    typeof record.followers_count === "number" &&
    typeof record.following_count === "number" &&
    typeof record.is_following === "boolean" &&
    typeof record.is_self === "boolean"
  );
}

function assertProfileDetail(payload: unknown, endpoint: string): ProfileDetail {
  if (!isProfileDetail(payload)) {
    throw new Error(
      `Invalid ProfileDetail payload from ${endpoint}: ${JSON.stringify(payload)} (expected profile object).`,
    );
  }
  return payload;
}

function assertUserSummaryList(payload: unknown, endpoint: string): UserSummary[] {
  if (!Array.isArray(payload) || !payload.every(isUserSummary)) {
    throw new Error(
      `Invalid UserSummary[] payload from ${endpoint}: ${JSON.stringify(payload)} (expected user summary array).`,
    );
  }
  return payload;
}

function isProfilePresets(value: unknown): value is ProfilePresets {
  if (!value || typeof value !== "object") {
    return false;
  }
  const record = value as Record<string, unknown>;
  return (
    Array.isArray(record.icons) &&
    record.icons.every((item) => typeof item === "number") &&
    Array.isArray(record.banners) &&
    record.banners.every((item) => typeof item === "number")
  );
}

/** Fetch public profile detail for username. */
export async function fetchProfile(
  username: string,
  client: ApiClient = new ApiClient(),
): Promise<ProfileDetail> {
  const endpoint = `/api/v1/profiles/${encodeURIComponent(username)}/`;
  const payload = await client.get<unknown>(endpoint);
  return assertProfileDetail(payload, endpoint);
}

/** Fetch available preset icon and banner IDs. */
export async function fetchProfilePresets(
  client: ApiClient = new ApiClient(),
): Promise<ProfilePresets> {
  const endpoint = "/api/v1/profiles/presets/";
  const payload = await client.get<unknown>(endpoint);
  if (!isProfilePresets(payload)) {
    throw new Error(
      `Invalid ProfilePresets payload from ${endpoint}: ${JSON.stringify(payload)} (expected {icons, banners}).`,
    );
  }
  return payload;
}

/** Update the authenticated user's profile customization fields. */
export async function updateOwnProfile(
  payload: UpdateProfilePayload,
  client: ApiClient = new ApiClient(),
): Promise<ProfileDetail> {
  const endpoint = "/api/v1/profiles/me/";
  const response = await client.patch<unknown>(endpoint, payload);
  return assertProfileDetail(response, endpoint);
}

/** Follow target username as the authenticated user. */
export async function followUser(
  username: string,
  client: ApiClient = new ApiClient(),
): Promise<void> {
  await client.post<unknown>(`/api/v1/profiles/${encodeURIComponent(username)}/follow/`);
}

/** Unfollow target username as the authenticated user. */
export async function unfollowUser(
  username: string,
  client: ApiClient = new ApiClient(),
): Promise<void> {
  await client.delete<unknown>(`/api/v1/profiles/${encodeURIComponent(username)}/follow/`);
}

/** Fetch followers of target username. */
export async function fetchFollowers(
  username: string,
  client: ApiClient = new ApiClient(),
): Promise<UserSummary[]> {
  const endpoint = `/api/v1/profiles/${encodeURIComponent(username)}/followers/`;
  const payload = await client.get<unknown>(endpoint);
  return assertUserSummaryList(payload, endpoint);
}

/** Fetch accounts followed by target username. */
export async function fetchFollowing(
  username: string,
  client: ApiClient = new ApiClient(),
): Promise<UserSummary[]> {
  const endpoint = `/api/v1/profiles/${encodeURIComponent(username)}/following/`;
  const payload = await client.get<unknown>(endpoint);
  return assertUserSummaryList(payload, endpoint);
}

/** Fetch 2-hop follow suggestions relative to target username. */
export async function fetchFollowSuggestions(
  username: string,
  client: ApiClient = new ApiClient(),
): Promise<UserSummary[]> {
  const endpoint = `/api/v1/profiles/${encodeURIComponent(username)}/suggestions/`;
  const payload = await client.get<unknown>(endpoint);
  return assertUserSummaryList(payload, endpoint);
}
