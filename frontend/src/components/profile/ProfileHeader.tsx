"use client";

import Image from "next/image";
import Link from "next/link";
import SmoothButton from "@/components/smoothui/smooth-button";
import type { ProfileDetail } from "@/lib/profile-api";

export interface ProfileHeaderProps {
  readonly profile: ProfileDetail;
  readonly canFollow: boolean;
  readonly isFollowBusy: boolean;
  readonly onToggleFollow: () => void;
  readonly onOpenFollowers: () => void;
  readonly onOpenFollowing: () => void;
}

/** Profile banner, avatar icon, bio, follow counters, and primary action button. */
export function ProfileHeader({
  profile,
  canFollow,
  isFollowBusy,
  onToggleFollow,
  onOpenFollowers,
  onOpenFollowing,
}: ProfileHeaderProps) {
  return (
    <section className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/70 shadow-xl">
      <div className="relative h-44 w-full bg-zinc-800 sm:h-56">
        <Image
          alt={`Banner de ${profile.display_name}`}
          className="h-full w-full object-cover"
          height={224}
          src={`/assets/banners/${profile.banner_id}.png`}
          width={1200}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-zinc-950/90 via-zinc-950/30 to-transparent" />
      </div>

      <div className="relative flex flex-col gap-6 px-6 pb-6 sm:flex-row sm:items-end sm:justify-between">
        <div className="-mt-12 flex flex-col gap-4 sm:flex-row sm:items-end">
          <Image
            alt={`Ícone de ${profile.display_name}`}
            className="h-24 w-24 rounded-2xl border-4 border-zinc-950 bg-zinc-900 object-cover shadow-lg"
            height={96}
            src={`/assets/icons/${profile.icon_id}.png`}
            width={96}
          />
          <div className="space-y-1">
            <h1 className="text-2xl font-bold text-white sm:text-3xl">{profile.display_name}</h1>
            <p className="text-sm text-zinc-400">@{profile.username}</p>
            <p className="max-w-xl pt-1 text-sm text-zinc-300">
              {profile.bio || "Este usuário ainda não escreveu uma biografia."}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          <button
            className="rounded-lg border border-zinc-800 bg-zinc-950/80 px-3.5 py-2 text-left transition-colors hover:border-zinc-700"
            onClick={onOpenFollowers}
            type="button"
          >
            <span className="block text-lg font-semibold text-white">
              {profile.followers_count}
            </span>
            <span className="text-xs text-zinc-400">Seguidores</span>
          </button>

          <button
            className="rounded-lg border border-zinc-800 bg-zinc-950/80 px-3.5 py-2 text-left transition-colors hover:border-zinc-700"
            onClick={onOpenFollowing}
            type="button"
          >
            <span className="block text-lg font-semibold text-white">
              {profile.following_count}
            </span>
            <span className="text-xs text-zinc-400">Seguindo</span>
          </button>

          {profile.is_self ? (
            <SmoothButton asChild color="accent" size="default" variant="candy">
              <Link href="/profile/edit">Editar perfil</Link>
            </SmoothButton>
          ) : canFollow ? (
            <SmoothButton
              color={profile.is_following ? "neutral" : "accent"}
              loading={isFollowBusy}
              onClick={onToggleFollow}
              size="default"
              variant={profile.is_following ? "outline" : "candy"}
            >
              {profile.is_following ? "Seguindo" : "Seguir"}
            </SmoothButton>
          ) : null}
        </div>
      </div>
    </section>
  );
}
