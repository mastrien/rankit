import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Footer } from "@/components/layout/Footer";
import { Navbar } from "@/components/layout/Navbar";
import "./globals.css";

export const metadata: Metadata = {
  title: "Rankit — Avalie filmes, séries, animes, jogos e livros",
  description:
    "Plataforma social para catalogar obras vistas, escrever reviews, manter seu diário e acompanhar amigos.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html className="dark" lang="pt-BR">
      <body className="flex min-h-screen flex-col bg-zinc-950 text-zinc-50 antialiased">
        <Navbar />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
