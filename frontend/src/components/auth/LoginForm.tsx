"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";
import { useAuth } from "@/components/auth/AuthProvider";
import SmoothButton from "@/components/smoothui/smooth-button";
import { ApiClientError } from "@/lib/api-client";

/** Login form backed by cookie-based JWT authentication. */
export function LoginForm() {
  const router = useRouter();
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);
    try {
      await login({ username, password });
      router.push("/");
    } catch (error) {
      if (error instanceof ApiClientError) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage("Não foi possível entrar agora. Tente novamente.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form
      className="mx-auto w-full max-w-md space-y-5 rounded-2xl border border-zinc-800 bg-zinc-900/70 p-8 shadow-xl"
      onSubmit={handleSubmit}
    >
      <div className="space-y-1">
        <h1 className="text-2xl font-bold text-white">Entrar no Rankit</h1>
        <p className="text-sm text-zinc-400">Acesse seu diário, reviews e listas.</p>
      </div>

      <div className="space-y-2">
        <label className="block text-sm font-medium text-zinc-200" htmlFor="login-username">
          Usuário
        </label>
        <input
          autoComplete="username"
          className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3.5 py-2.5 text-sm text-white placeholder:text-zinc-500 focus:border-orange-500 focus:outline-none"
          id="login-username"
          name="username"
          onChange={(event) => setUsername(event.target.value)}
          placeholder="seu_usuario"
          required
          type="text"
          value={username}
        />
      </div>

      <div className="space-y-2">
        <label className="block text-sm font-medium text-zinc-200" htmlFor="login-password">
          Senha
        </label>
        <input
          autoComplete="current-password"
          className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3.5 py-2.5 text-sm text-white placeholder:text-zinc-500 focus:border-orange-500 focus:outline-none"
          id="login-password"
          name="password"
          onChange={(event) => setPassword(event.target.value)}
          placeholder="••••••••"
          required
          type="password"
          value={password}
        />
      </div>

      {errorMessage ? (
        <p
          className="rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-300"
          role="alert"
        >
          {errorMessage}
        </p>
      ) : null}

      <SmoothButton
        className="w-full"
        color="accent"
        loading={isSubmitting}
        size="lg"
        type="submit"
        variant="candy"
      >
        Entrar
      </SmoothButton>

      <p className="text-center text-sm text-zinc-400">
        Ainda não tem conta?{" "}
        <Link className="font-medium text-orange-400 hover:underline" href="/register">
          Criar cadastro
        </Link>
      </p>
    </form>
  );
}
