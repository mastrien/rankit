"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { ApiClient, ApiClientError } from "@/lib/api-client";
import { fetchMediaDetail, MEDIA_CATEGORY_LABELS, type MediaDetail } from "@/lib/media-api";

export interface MediaDetailViewProps {
  readonly category: string;
  readonly externalId: string;
  readonly apiClient?: ApiClient;
}

/** Public media detail view displaying metadata cached in PostgreSQL. */
export function MediaDetailView({ category, externalId, apiClient }: MediaDetailViewProps) {
  const client = useMemo(() => apiClient ?? new ApiClient(), [apiClient]);
  const [media, setMedia] = useState<MediaDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setIsLoading(true);
    setErrorMessage(null);
    void fetchMediaDetail(category, externalId, client)
      .then((detail) => {
        if (active) {
          setMedia(detail);
        }
      })
      .catch((error: unknown) => {
        if (!active) {
          return;
        }
        if (error instanceof ApiClientError && error.status === 404) {
          setErrorMessage("Obra não encontrada.");
        } else {
          setErrorMessage("Não foi possível carregar os detalhes desta obra.");
        }
        setMedia(null);
      })
      .finally(() => {
        if (active) {
          setIsLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [category, client, externalId]);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-12 text-sm text-zinc-400">
        Carregando detalhes da obra...
      </div>
    );
  }

  if (errorMessage || !media) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-12">
        <p className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 text-zinc-300" role="alert">
          {errorMessage ?? "Obra não encontrada."}
        </p>
      </div>
    );
  }

  const categoryLabel = MEDIA_CATEGORY_LABELS[media.category];

  return (
    <article className="mx-auto flex max-w-5xl flex-col gap-6 px-4 py-10">
      <Link
        className="w-fit text-sm text-zinc-400 transition-colors hover:text-orange-400"
        href={`/search?category=${media.category}`}
      >
        ← Voltar para busca em {categoryLabel}
      </Link>

      <div className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/70">
        <div className="relative h-48 w-full overflow-hidden border-b border-zinc-800 sm:h-64">
          <Image
            alt={`Banner de ${media.title}`}
            className="h-full w-full object-cover opacity-80"
            height={256}
            src={media.banner_url || media.poster_url || "/assets/banners/0.png"}
            width={1024}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 via-zinc-950/30 to-transparent" />
        </div>

        <div className="flex flex-col gap-6 p-6 sm:flex-row">
          <Image
            alt={media.title}
            className="-mt-16 h-44 w-32 shrink-0 rounded-xl border border-zinc-700 object-cover shadow-xl"
            height={176}
            src={media.poster_url || "/assets/banners/0.png"}
            width={128}
          />
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-orange-500/20 px-3 py-0.5 text-xs font-medium text-orange-300">
                {categoryLabel}
              </span>
              {media.release_year && (
                <span className="text-xs text-zinc-400">{media.release_year}</span>
              )}
              <span className="text-xs font-semibold text-amber-400">
                Nota {media.score.toFixed(1)}
              </span>
            </div>

            <h1 className="text-3xl font-bold text-white">{media.title}</h1>
            <p className="text-sm leading-relaxed text-zinc-300">
              {media.description || "Sinopse ainda não disponível."}
            </p>

            {media.genres.length > 0 && (
              <div className="flex flex-wrap gap-2 pt-1">
                {media.genres.map((genre) => (
                  <span
                    className="rounded-md border border-zinc-700 bg-zinc-950 px-2.5 py-0.5 text-xs text-zinc-300"
                    key={genre}
                  >
                    {genre}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6">
        <h2 className="text-lg font-semibold text-white">Avaliações e diário</h2>
        <p className="mt-1 text-sm text-zinc-400">
          O registro de notas, resenhas e lista pessoal desta obra chega na próxima etapa.
        </p>
      </section>
    </article>
  );
}
