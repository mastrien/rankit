"use client";

import Image from "next/image";
import Link from "next/link";
import { type FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import SmoothButton from "@/components/smoothui/smooth-button";
import { ApiClient } from "@/lib/api-client";
import {
  isMediaCategoryId,
  MEDIA_CATEGORY_LABELS,
  type MediaCategoryId,
  type MediaSearchResult,
  searchMedia,
} from "@/lib/media-api";

export interface MediaSearchViewProps {
  readonly initialCategory?: string;
  readonly initialQuery?: string;
  readonly apiClient?: ApiClient;
}

const CATEGORY_ORDER: readonly MediaCategoryId[] = ["movie", "serie", "anime", "game", "book"];

/** Interactive media catalog search page with category pills and result grid. */
export function MediaSearchView({
  initialCategory = "movie",
  initialQuery = "",
  apiClient,
}: MediaSearchViewProps) {
  const client = useMemo(() => apiClient ?? new ApiClient(), [apiClient]);
  const [category, setCategory] = useState<MediaCategoryId>(
    isMediaCategoryId(initialCategory) ? initialCategory : "movie",
  );
  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState<MediaSearchResult[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const executeSearch = useCallback(
    async (targetCategory: MediaCategoryId, rawQuery: string) => {
      const cleaned = rawQuery.trim();
      if (!cleaned) {
        setErrorMessage("Digite um termo para buscar no catálogo.");
        return;
      }
      setErrorMessage(null);
      setIsLoading(true);
      try {
        const items = await searchMedia(targetCategory, cleaned, client);
        setResults(items);
        setHasSearched(true);
      } catch {
        setErrorMessage("Não foi possível buscar obras no momento.");
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    },
    [client],
  );

  useEffect(() => {
    if (initialQuery.trim()) {
      const initialCat = isMediaCategoryId(initialCategory) ? initialCategory : "movie";
      void executeSearch(initialCat, initialQuery);
    }
  }, [executeSearch, initialCategory, initialQuery]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void executeSearch(category, query);
  }

  return (
    <section className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-10">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold text-white">Explorar catálogo</h1>
        <p className="text-sm text-zinc-400">
          Pesquise filmes, séries, animes, jogos e livros para abrir detalhes e avaliações.
        </p>
      </div>

      <div aria-label="Categorias de mídia" className="flex flex-wrap gap-2" role="group">
        {CATEGORY_ORDER.map((cat) => {
          const active = cat === category;
          return (
            <button
              aria-pressed={active}
              className={
                active
                  ? "rounded-full bg-orange-500 px-4 py-1.5 text-sm font-medium text-white"
                  : "rounded-full border border-zinc-700 bg-zinc-900 px-4 py-1.5 text-sm text-zinc-300 hover:border-zinc-500 hover:text-white"
              }
              key={cat}
              onClick={() => setCategory(cat)}
              type="button"
            >
              {MEDIA_CATEGORY_LABELS[cat]}
            </button>
          );
        })}
      </div>

      <form className="flex flex-col gap-3 sm:flex-row" onSubmit={handleSubmit}>
        <label className="sr-only" htmlFor="media-search-input">
          Buscar obra
        </label>
        <input
          className="flex-1 rounded-lg border border-zinc-700 bg-zinc-950 px-4 py-2.5 text-sm text-white placeholder:text-zinc-500 focus:border-orange-500 focus:outline-none"
          id="media-search-input"
          name="q"
          onChange={(event) => setQuery(event.target.value)}
          placeholder={`Buscar em ${MEDIA_CATEGORY_LABELS[category]}...`}
          type="search"
          value={query}
        />
        <SmoothButton color="accent" loading={isLoading} size="lg" type="submit" variant="candy">
          Buscar
        </SmoothButton>
      </form>

      {errorMessage && (
        <p
          className="rounded-lg border border-red-900/60 bg-red-950/60 px-4 py-2.5 text-sm text-red-200"
          role="alert"
        >
          {errorMessage}
        </p>
      )}

      {isLoading ? (
        <p className="py-8 text-sm text-zinc-400">Buscando no catálogo...</p>
      ) : hasSearched && results.length === 0 && !errorMessage ? (
        <p className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6 text-sm text-zinc-400">
          Nenhuma obra encontrada para esta busca.
        </p>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {results.map((item) => (
            <Link
              className="group flex gap-4 rounded-xl border border-zinc-800 bg-zinc-900/70 p-4 transition-colors hover:border-orange-500/60"
              href={`/media/${item.category}/${item.external_id}`}
              key={`${item.category}-${item.external_id}`}
            >
              <Image
                alt={item.title}
                className="h-24 w-16 shrink-0 rounded-md object-cover"
                height={96}
                src={item.poster_url || "/assets/banners/0.png"}
                width={64}
              />
              <div className="flex flex-col justify-between">
                <div>
                  <h2 className="font-semibold text-white group-hover:text-orange-400">
                    {item.title}
                  </h2>
                  <p className="mt-1 text-xs text-zinc-400">
                    {MEDIA_CATEGORY_LABELS[item.category]} • {item.release_year || "Ano indefinido"}
                  </p>
                </div>
                <p className="text-xs font-medium text-amber-400">Nota {item.score.toFixed(1)}</p>
              </div>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}
