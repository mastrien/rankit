"use client";

import Image from "next/image";
import Link from "next/link";
import SmoothButton from "@/components/smoothui/smooth-button";
import type { UserSummary } from "@/lib/profile-api";

export interface FollowListModalProps {
  readonly title: string;
  readonly isOpen: boolean;
  readonly users: readonly UserSummary[];
  readonly onClose: () => void;
}

/** Accessible modal displaying follower or following user summaries. */
export function FollowListModal({ title, isOpen, users, onClose }: FollowListModalProps) {
  if (!isOpen) {
    return null;
  }

  return (
    <div
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4"
      role="dialog"
    >
      <div className="w-full max-w-md rounded-2xl border border-zinc-800 bg-zinc-900 p-6 shadow-2xl">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
          <h2 className="text-lg font-semibold text-white">{title}</h2>
          <SmoothButton onClick={onClose} size="sm" variant="ghost">
            Fechar
          </SmoothButton>
        </div>

        {users.length === 0 ? (
          <p className="py-6 text-center text-sm text-zinc-400">Nenhum usuário encontrado.</p>
        ) : (
          <ul className="mt-4 max-h-80 space-y-2 overflow-y-auto">
            {users.map((item) => (
              <li key={item.id}>
                <Link
                  className="flex items-center gap-3 rounded-lg border border-zinc-800 bg-zinc-950/60 p-2.5 transition-colors hover:border-zinc-700"
                  href={`/profile/${item.username}`}
                  onClick={onClose}
                >
                  <Image
                    alt={item.display_name}
                    className="h-10 w-10 rounded-full object-cover"
                    height={40}
                    src={`/assets/icons/${item.icon_id}.png`}
                    width={40}
                  />
                  <div>
                    <p className="text-sm font-medium text-white">{item.display_name}</p>
                    <p className="text-xs text-zinc-400">@{item.username}</p>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
