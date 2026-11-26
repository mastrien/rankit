"use client";

import Image from "next/image";
import Link from "next/link";
import SmoothButton from "@/components/smoothui/smooth-button";

/** Top navigation bar shared across Rankit pages. */
export function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-zinc-800 bg-zinc-950/90 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
        <Link className="flex items-center gap-3 font-semibold tracking-tight text-white" href="/">
          <Image
            alt="Rankit"
            className="h-8 w-auto"
            height={32}
            priority
            src="/assets/logo.png"
            width={110}
          />
          <span className="sr-only">Rankit</span>
        </Link>

        <nav aria-label="Navegação principal" className="flex items-center gap-3">
          <Link
            className="rounded-md px-3 py-1.5 text-sm text-zinc-300 transition-colors hover:text-white"
            href="/"
          >
            Início
          </Link>
          <SmoothButton asChild size="sm" variant="ghost">
            <Link href="/login">Entrar</Link>
          </SmoothButton>
          <SmoothButton asChild color="accent" size="sm" variant="candy">
            <Link href="/register">Cadastro</Link>
          </SmoothButton>
        </nav>
      </div>
    </header>
  );
}
