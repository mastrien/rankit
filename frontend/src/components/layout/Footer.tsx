import Link from "next/link";

/** Footer displaying Rankit attribution and quick navigation. */
export function Footer() {
  return (
    <footer className="border-t border-zinc-800 bg-zinc-950 py-8 text-sm text-zinc-400">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-4 sm:flex-row">
        <p>Rankit — Avalie filmes, séries, animes, jogos e livros em um só lugar.</p>
        <div className="flex items-center gap-4">
          <Link className="transition-colors hover:text-white" href="/">
            Início
          </Link>
          <Link className="transition-colors hover:text-white" href="/login">
            Login
          </Link>
          <Link className="transition-colors hover:text-white" href="/register">
            Cadastro
          </Link>
        </div>
      </div>
    </footer>
  );
}
