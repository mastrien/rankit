"use client";

import Image from "next/image";
import Link from "next/link";
import SmoothButton from "@/components/smoothui/smooth-button";
import type { UserSummary } from "@/lib/profile-api";

export interface FollowSuggestionsCardProps {
  readonly suggestions: readonly UserSummary[];
  readonly onFollowSuggestion: (username: string) => void;
}

/** Card listing 2-hop social follow suggestions for the authenticated viewer. */
export function FollowSuggestionsCard({
  suggestions,
  onFollowSuggestion,
}: FollowSuggestionsCardProps) {
  if (suggestions.length === 0) {
    return null;
  }

  return (
    <aside className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6">
      <h2 className="text-base font-semibold text-white">Sugestões para seguir</h2>
      <p className="mt-1 text-xs text-zinc-400">
        Pessoas conectadas a este perfil que você ainda não segue.
      </p>
      <ul className="mt-4 grid gap-3 sm:grid-cols-2">
        {suggestions.map((person) => (
          <li
            className="flex items-center justify-between gap-3 rounded-xl border border-zinc-800 bg-zinc-950/70 p-3"
            key={person.id}
          >
            <Link className="flex items-center gap-3" href={`/profile/${person.username}`}>
              <Image
                alt={person.display_name}
                className="h-10 w-10 rounded-full object-cover"
                height={40}
                src={`/assets/icons/${person.icon_id}.png`}
                width={40}
              />
              <div>
                <p className="text-sm font-medium text-white">{person.display_name}</p>
                <p className="text-xs text-zinc-400">@{person.username}</p>
              </div>
            </Link>
            <SmoothButton
              color="accent"
              onClick={() => onFollowSuggestion(person.username)}
              size="xs"
              variant="soft"
            >
              Seguir
            </SmoothButton>
          </li>
        ))}
      </ul>
    </aside>
  );
}
