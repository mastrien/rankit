import Link from "next/link";
import { CategoryShowcase } from "@/components/home/CategoryShowcase";
import SiriOrb from "@/components/smoothui/siri-orb";
import SmoothButton from "@/components/smoothui/smooth-button";

/** Rankit landing page introducing the five supported media categories. */
export default function HomePage() {
  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-16 px-4 py-14">
      <section className="relative overflow-hidden rounded-2xl border border-zinc-800 bg-gradient-to-br from-zinc-900 via-zinc-950 to-zinc-900 p-8 sm:p-12">
        <div className="flex flex-col items-start justify-between gap-8 md:flex-row md:items-center">
          <div className="max-w-2xl space-y-5">
            <span className="inline-flex items-center rounded-full border border-orange-500/30 bg-orange-500/10 px-3 py-1 text-xs font-medium text-orange-300">
              Tudo em um só lugar
            </span>
            <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl">
              Boas-vindas ao Rankit
            </h1>
            <p className="text-base leading-relaxed text-zinc-300 sm:text-lg">
              Avalie as obras que você já consumiu, mantenha seu diário pessoal e acompanhe as
              descobertas dos seus amigos em filmes, séries, animes, jogos e livros.
            </p>
            <div className="flex flex-wrap items-center gap-3 pt-2">
              <SmoothButton asChild color="accent" size="lg" variant="candy">
                <Link href="/register">Comece já</Link>
              </SmoothButton>
              <SmoothButton asChild size="lg" variant="outline">
                <Link href="/login">Já tenho uma conta</Link>
              </SmoothButton>
            </div>
          </div>

          <div aria-hidden="true" className="hidden shrink-0 md:block">
            <SiriOrb
              colors={{
                bg: "oklch(22% 0.03 30)",
                c1: "oklch(68% 0.21 35)",
                c2: "oklch(70% 0.18 350)",
                c3: "oklch(66% 0.2 280)",
                c4: "oklch(75% 0.18 65)",
              }}
              size="168px"
            />
          </div>
        </div>
      </section>

      <section aria-labelledby="categories-heading" className="space-y-6">
        <div className="space-y-2">
          <h2 className="text-2xl font-semibold tracking-tight text-white" id="categories-heading">
            Cinco universos, um só diário
          </h2>
          <p className="text-sm text-zinc-400">
            Integrações com TMDB, IGDB e Google Books com persistência relacional em PostgreSQL.
          </p>
        </div>
        <CategoryShowcase />
      </section>
    </div>
  );
}
