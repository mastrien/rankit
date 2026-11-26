"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";
import { useAuth } from "@/components/auth/AuthProvider";
import SmoothButton from "@/components/smoothui/smooth-button";
import { ApiClientError } from "@/lib/api-client";

function formatSerializerErrors(details: unknown, fallback: string): string {
  if (!details || typeof details !== "object") {
    return fallback;
  }
  const record = details as Record<string, unknown>;
  for (const value of Object.values(record)) {
    if (Array.isArray(value) && typeof value[0] === "string") {
      return value[0];
    }
    if (typeof value === "string") {
      return value;
    }
  }
  return fallback;
}

/** Registration form creating a Rankit account and starting an HttpOnly cookie session. */
export function RegisterForm() {
  const router = useRouter();
  const { register } = useAuth();
  const [displayName, setDisplayName] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (password !== passwordConfirm) {
      setErrorMessage("As senhas não coincidem.");
      return;
    }
    setErrorMessage(null);
    setIsSubmitting(true);
    try {
      await register({
        display_name: displayName,
        username,
        email,
        password,
        password_confirm: passwordConfirm,
      });
      router.push("/");
    } catch (error) {
      if (error instanceof ApiClientError) {
        setErrorMessage(formatSerializerErrors(error.details, error.message));
      } else {
        setErrorMessage("Erro ao criar sua conta. Tente novamente.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form
      className="mx-auto w-full max-w-md space-y-4 rounded-2xl border border-zinc-800 bg-zinc-900/70 p-8 shadow-xl"
      onSubmit={handleSubmit}
    >
      <div className="space-y-1">
        <h1 className="text-2xl font-bold text-white">Criar conta no Rankit</h1>
        <p className="text-sm text-zinc-400">Comece seu catálogo de obras hoje.</p>
      </div>

      <div className="space-y-1.5">
        <label className="block text-sm font-medium text-zinc-200" htmlFor="register-display-name">
          Nome de exibição
        </label>
        <input
          className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3.5 py-2.5 text-sm text-white placeholder:text-zinc-500 focus:border-orange-500 focus:outline-none"
          id="register-display-name"
          name="display_name"
          onChange={(event) => setDisplayName(event.target.value)}
          placeholder="Seu nome"
          required
          type="text"
          value={displayName}
        />
      </div>

      <div className="space-y-1.5">
        <label className="block text-sm font-medium text-zinc-200" htmlFor="register-username">
          Usuário
        </label>
        <input
          autoComplete="username"
          className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3.5 py-2.5 text-sm text-white placeholder:text-zinc-500 focus:border-orange-500 focus:outline-none"
          id="register-username"
          name="username"
          onChange={(event) => setUsername(event.target.value)}
          placeholder="nome_unico"
          required
          type="text"
          value={username}
        />
      </div>

      <div className="space-y-1.5">
        <label className="block text-sm font-medium text-zinc-200" htmlFor="register-email">
          E-mail
        </label>
        <input
          autoComplete="email"
          className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3.5 py-2.5 text-sm text-white placeholder:text-zinc-500 focus:border-orange-500 focus:outline-none"
          id="register-email"
          name="email"
          onChange={(event) => setEmail(event.target.value)}
          placeholder="voce@exemplo.com"
          required
          type="email"
          value={email}
        />
      </div>

      <div className="space-y-1.5">
        <label className="block text-sm font-medium text-zinc-200" htmlFor="register-password">
          Senha
        </label>
        <input
          autoComplete="new-password"
          className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3.5 py-2.5 text-sm text-white placeholder:text-zinc-500 focus:border-orange-500 focus:outline-none"
          id="register-password"
          minLength={8}
          name="password"
          onChange={(event) => setPassword(event.target.value)}
          placeholder="Mínimo 8 caracteres"
          required
          type="password"
          value={password}
        />
      </div>

      <div className="space-y-1.5">
        <label className="block text-sm font-medium text-zinc-200" htmlFor="register-confirm">
          Confirmar senha
        </label>
        <input
          autoComplete="new-password"
          className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3.5 py-2.5 text-sm text-white placeholder:text-zinc-500 focus:border-orange-500 focus:outline-none"
          id="register-confirm"
          minLength={8}
          name="password_confirm"
          onChange={(event) => setPasswordConfirm(event.target.value)}
          placeholder="Repita sua senha"
          required
          type="password"
          value={passwordConfirm}
        />
      </div>

      {errorMessage ? (
        <p className="rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-300" role="alert">
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
        Cadastrar
      </SmoothButton>

      <p className="text-center text-sm text-zinc-400">
        Já tem uma conta?{" "}
        <Link className="font-medium text-orange-400 hover:underline" href="/login">
          Entrar
        </Link>
      </p>
    </form>
  );
}
