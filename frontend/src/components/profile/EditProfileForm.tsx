"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useEffect, useMemo, useState } from "react";
import { useAuth } from "@/components/auth/AuthProvider";
import SmoothButton from "@/components/smoothui/smooth-button";
import { ApiClient, ApiClientError } from "@/lib/api-client";
import {
  fetchProfilePresets,
  type ProfilePresets,
  updateOwnProfile,
} from "@/lib/profile-api";

export interface EditProfileFormProps {
  readonly apiClient?: ApiClient;
}

const DEFAULT_PRESETS: ProfilePresets = {
  icons: Array.from({ length: 19 }, (_, idx) => idx),
  banners: Array.from({ length: 7 }, (_, idx) => idx),
};

/** Form allowing authenticated users to customize name, bio, preset icon, and banner. */
export function EditProfileForm({ apiClient }: EditProfileFormProps) {
  const client = useMemo(() => apiClient ?? new ApiClient(), [apiClient]);
  const router = useRouter();
  const { user, isLoading: isAuthLoading, refreshUser } = useAuth();
  const [presets, setPresets] = useState<ProfilePresets>(DEFAULT_PRESETS);
  const [displayName, setDisplayName] = useState(user?.display_name ?? "");
  const [bio, setBio] = useState(user?.bio ?? "");
  const [iconId, setIconId] = useState(user?.icon_id ?? 0);
  const [bannerId, setBannerId] = useState(user?.banner_id ?? 0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (user) {
      setDisplayName(user.display_name);
      setBio(user.bio);
      setIconId(user.icon_id);
      setBannerId(user.banner_id);
    }
  }, [user]);

  useEffect(() => {
    let active = true;
    void fetchProfilePresets(client)
      .then((loaded) => {
        if (active) {
          setPresets(loaded);
        }
      })
      .catch(() => {
        // Keep deterministic fallback presets if endpoint fails transiently.
      });
    return () => {
      active = false;
    };
  }, [client]);

  if (isAuthLoading) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-12 text-sm text-zinc-400">Carregando...</div>
    );
  }

  if (!user) {
    return (
      <div className="mx-auto max-w-xl px-4 py-12 text-center">
        <p className="text-zinc-300">Você precisa entrar para editar seu perfil.</p>
        <SmoothButton asChild className="mt-4" color="accent" variant="candy">
          <Link href="/login">Ir para login</Link>
        </SmoothButton>
      </div>
    );
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setIsSaving(true);
    try {
      const updated = await updateOwnProfile(
        { display_name: displayName, bio, icon_id: iconId, banner_id: bannerId },
        client,
      );
      await refreshUser();
      router.push(`/profile/${updated.username}`);
    } catch (error) {
      if (error instanceof ApiClientError) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage("Erro ao atualizar perfil.");
      }
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form
      className="mx-auto max-w-4xl space-y-6 rounded-2xl border border-zinc-800 bg-zinc-900/70 p-6 sm:p-8"
      onSubmit={handleSubmit}
    >
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Editar perfil</h1>
          <p className="text-sm text-zinc-400">Personalize seu nome, bio, ícone e banner.</p>
        </div>
        <SmoothButton color="accent" loading={isSaving} size="lg" type="submit" variant="candy">
          Salvar alterações
        </SmoothButton>
      </div>

      <div className="relative h-36 overflow-hidden rounded-xl border border-zinc-800">
        <Image
          alt="Prévia do banner selecionado"
          className="h-full w-full object-cover"
          height={144}
          src={`/assets/banners/${bannerId}.png`}
          width={960}
        />
        <div className="absolute bottom-3 left-3 flex items-center gap-3 rounded-xl bg-zinc-950/85 px-3 py-2 backdrop-blur-sm">
          <Image
            alt="Prévia do ícone selecionado"
            className="h-12 w-12 rounded-full object-cover"
            height={48}
            src={`/assets/icons/${iconId}.png`}
            width={48}
          />
          <div>
            <p className="text-sm font-semibold text-white">{displayName || user.username}</p>
            <p className="text-xs text-zinc-400">@{user.username}</p>
          </div>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <label className="block text-sm font-medium text-zinc-200" htmlFor="edit-display-name">
            Nome de exibição
          </label>
          <input
            className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3.5 py-2.5 text-sm text-white focus:border-orange-500 focus:outline-none"
            id="edit-display-name"
            maxLength={80}
            name="display_name"
            onChange={(event) => setDisplayName(event.target.value)}
            required
            type="text"
            value={displayName}
          />
        </div>

        <div className="space-y-1.5">
          <label className="block text-sm font-medium text-zinc-200" htmlFor="edit-bio">
            Biografia ({bio.length}/200)
          </label>
          <input
            className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3.5 py-2.5 text-sm text-white focus:border-orange-500 focus:outline-none"
            id="edit-bio"
            maxLength={200}
            name="bio"
            onChange={(event) => setBio(event.target.value)}
            placeholder="Conte o que você gosta de assistir, jogar ou ler"
            type="text"
            value={bio}
          />
        </div>
      </div>

      <fieldset className="space-y-3">
        <legend className="text-sm font-medium text-zinc-200">Escolha seu ícone</legend>
        <div className="grid grid-cols-5 gap-3 sm:grid-cols-10">
          {presets.icons.map((id) => (
            <button
              aria-label={`Ícone ${id}`}
              aria-pressed={iconId === id}
              className={`overflow-hidden rounded-xl border-2 p-0.5 transition ${
                iconId === id ? "border-orange-500 ring-2 ring-orange-500/40" : "border-zinc-800"
              }`}
              key={id}
              onClick={() => setIconId(id)}
              type="button"
            >
              <Image
                alt={`Opção de ícone ${id}`}
                className="h-12 w-full rounded-lg object-cover"
                height={48}
                src={`/assets/icons/${id}.png`}
                width={48}
              />
            </button>
          ))}
        </div>
      </fieldset>

      <fieldset className="space-y-3">
        <legend className="text-sm font-medium text-zinc-200">Escolha seu banner</legend>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {presets.banners.map((id) => (
            <button
              aria-label={`Banner ${id}`}
              aria-pressed={bannerId === id}
              className={`overflow-hidden rounded-xl border-2 p-0.5 transition ${
                bannerId === id ? "border-orange-500 ring-2 ring-orange-500/40" : "border-zinc-800"
              }`}
              key={id}
              onClick={() => setBannerId(id)}
              type="button"
            >
              <Image
                alt={`Opção de banner ${id}`}
                className="h-20 w-full rounded-lg object-cover"
                height={80}
                src={`/assets/banners/${id}.png`}
                width={200}
              />
            </button>
          ))}
        </div>
      </fieldset>

      {errorMessage ? (
        <p className="rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-300" role="alert">
          {errorMessage}
        </p>
      ) : null}
    </form>
  );
}
