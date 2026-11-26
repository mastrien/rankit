"use client";

import { BookOpen, Film, Gamepad2, Sparkles, Tv } from "lucide-react";
import Link from "next/link";
import GlowHover, { type GlowHoverItem } from "@/components/smoothui/glow-hover-card";

interface MediaCategoryMeta {
  readonly id: string;
  readonly label: string;
  readonly description: string;
  readonly provider: string;
  readonly hue: number;
}

const RANKIT_CATEGORIES: readonly MediaCategoryMeta[] = [
  {
    id: "movie",
    label: "Filmes",
    description: "Registre filmes assistidos, notas e resenhas.",
    provider: "TMDB",
    hue: 25,
  },
  {
    id: "serie",
    label: "Séries",
    description: "Acompanhe temporadas e compartilhe opiniões.",
    provider: "TMDB",
    hue: 210,
  },
  {
    id: "anime",
    label: "Animes",
    description: "Organize seus animes favoritos e descobertas.",
    provider: "TMDB",
    hue: 325,
  },
  {
    id: "game",
    label: "Jogos",
    description: "Catalogação completa dos jogos zerados.",
    provider: "IGDB",
    hue: 150,
  },
  {
    id: "book",
    label: "Livros",
    description: "Diário de leitura com avaliações detalhadas.",
    provider: "Google Books",
    hue: 45,
  },
];

function CategoryIcon({ id }: { readonly id: string }) {
  switch (id) {
    case "movie":
      return <Film aria-hidden="true" className="h-5 w-5 text-orange-400" />;
    case "serie":
      return <Tv aria-hidden="true" className="h-5 w-5 text-sky-400" />;
    case "anime":
      return <Sparkles aria-hidden="true" className="h-5 w-5 text-pink-400" />;
    case "game":
      return <Gamepad2 aria-hidden="true" className="h-5 w-5 text-emerald-400" />;
    default:
      return <BookOpen aria-hidden="true" className="h-5 w-5 text-amber-400" />;
  }
}

/** Interactive SmoothUI GlowHover grid showcasing Rankit's 5 media categories. */
export function CategoryShowcase() {
  const items: GlowHoverItem[] = RANKIT_CATEGORIES.map((category) => ({
    id: category.id,
    theme: { hue: category.hue, saturation: 85, lightness: 58 },
    element: (
      <Link className="block h-full" href={`/search?category=${category.id}`}>
        <article className="flex h-full flex-col justify-between rounded-xl border border-zinc-800 bg-zinc-900/70 p-5">
          <div className="flex items-center justify-between">
            <CategoryIcon id={category.id} />
            <span className="rounded-full bg-zinc-800 px-2.5 py-0.5 text-xs text-zinc-300">
              {category.provider}
            </span>
          </div>
          <div className="mt-4">
            <h3 className="text-lg font-semibold text-white">{category.label}</h3>
            <p className="mt-1 text-sm text-zinc-400">{category.description}</p>
          </div>
        </article>
      </Link>
    ),
  }));

  return (
    <GlowHover
      className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5"
      glowIntensity={0.18}
      items={items}
    />
  );
}
