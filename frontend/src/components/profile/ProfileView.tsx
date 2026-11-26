"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "@/components/auth/AuthProvider";
import { FollowListModal } from "@/components/profile/FollowListModal";
import { FollowSuggestionsCard } from "@/components/profile/FollowSuggestionsCard";
import { ProfileHeader } from "@/components/profile/ProfileHeader";
import { ApiClient, ApiClientError } from "@/lib/api-client";
import {
  fetchFollowers,
  fetchFollowing,
  fetchFollowSuggestions,
  fetchProfile,
  followUser,
  type ProfileDetail,
  unfollowUser,
  type UserSummary,
} from "@/lib/profile-api";

export interface ProfileViewProps {
  readonly username: string;
  readonly apiClient?: ApiClient;
}

/** Interactive public profile view with follow toggles, lists, and 2-hop suggestions. */
export function ProfileView({ username, apiClient }: ProfileViewProps) {
  const client = useMemo(() => apiClient ?? new ApiClient(), [apiClient]);
  const { user: viewer } = useAuth();
  const [profile, setProfile] = useState<ProfileDetail | null>(null);
  const [suggestions, setSuggestions] = useState<UserSummary[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isFollowBusy, setIsFollowBusy] = useState(false);
  const [modalTitle, setModalTitle] = useState("");
  const [modalUsers, setModalUsers] = useState<UserSummary[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const loadProfile = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const detail = await fetchProfile(username, client);
      setProfile(detail);
      if (viewer && !detail.is_self) {
        const items = await fetchFollowSuggestions(username, client);
        setSuggestions(items);
      } else {
        setSuggestions([]);
      }
    } catch (error) {
      if (error instanceof ApiClientError && error.status === 404) {
        setErrorMessage("Perfil não encontrado.");
      } else {
        setErrorMessage("Não foi possível carregar este perfil.");
      }
      setProfile(null);
    } finally {
      setIsLoading(false);
    }
  }, [client, username, viewer]);

  useEffect(() => {
    void loadProfile();
  }, [loadProfile]);

  async function handleToggleFollow() {
    if (!profile) {
      return;
    }
    setIsFollowBusy(true);
    try {
      if (profile.is_following) {
        await unfollowUser(profile.username, client);
      } else {
        await followUser(profile.username, client);
      }
      await loadProfile();
    } finally {
      setIsFollowBusy(false);
    }
  }

  async function handleFollowSuggestion(targetUsername: string) {
    await followUser(targetUsername, client);
    setSuggestions((prev) => prev.filter((item) => item.username !== targetUsername));
  }

  async function openFollowList(kind: "followers" | "following") {
    if (!profile) {
      return;
    }
    const items =
      kind === "followers"
        ? await fetchFollowers(profile.username, client)
        : await fetchFollowing(profile.username, client);
    setModalTitle(kind === "followers" ? "Seguidores" : "Seguindo");
    setModalUsers(items);
    setIsModalOpen(true);
  }

  if (isLoading) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-12 text-sm text-zinc-400">
        Carregando perfil...
      </div>
    );
  }

  if (errorMessage || !profile) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-12">
        <p className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 text-zinc-300" role="alert">
          {errorMessage ?? "Perfil não encontrado."}
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-10">
      <ProfileHeader
        canFollow={viewer !== null && !profile.is_self}
        isFollowBusy={isFollowBusy}
        onOpenFollowers={() => void openFollowList("followers")}
        onOpenFollowing={() => void openFollowList("following")}
        onToggleFollow={() => void handleToggleFollow()}
        profile={profile}
      />

      <FollowSuggestionsCard
        onFollowSuggestion={(target) => void handleFollowSuggestion(target)}
        suggestions={suggestions}
      />

      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6">
        <h2 className="text-lg font-semibold text-white">Diário e avaliações</h2>
        <p className="mt-1 text-sm text-zinc-400">
          O catálogo de mídias vistas e reviews aparecerá aqui na próxima etapa.
        </p>
      </section>

      <FollowListModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={modalTitle}
        users={modalUsers}
      />
    </div>
  );
}
