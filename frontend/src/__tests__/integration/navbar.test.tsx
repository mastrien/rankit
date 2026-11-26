import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { AuthProvider } from "@/components/auth/AuthProvider";
import { Footer } from "@/components/layout/Footer";
import { Navbar } from "@/components/layout/Navbar";
import { ApiClient, type FetchLike } from "@/lib/api-client";

class FakeLogoutFetch {
  public called = false;
  public call: FetchLike = async () => {
    this.called = true;
    return new Response(null, { status: 204 });
  };
}

describe("Navigation layout components", () => {
  it("renders Rankit logo and auth navigation links when unauthenticated", () => {
    render(
      <AuthProvider skipInitialFetch>
        <Navbar />
      </AuthProvider>,
    );

    expect(screen.getByRole("img", { name: "Rankit" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Início" })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: "Entrar" })).toHaveAttribute("href", "/login");
    expect(screen.getByRole("link", { name: "Cadastro" })).toHaveAttribute("href", "/register");
  });

  it("renders user profile link and handles logout when authenticated", async () => {
    const fakeLogout = new FakeLogoutFetch();
    const client = new ApiClient("http://localhost:8000", fakeLogout.call);

    render(
      <AuthProvider
        apiClient={client}
        initialUser={{
          id: 1,
          username: "joao",
          display_name: "João Pedro",
          email: "joao@example.com",
          bio: "",
          icon_id: 0,
          banner_id: 0,
          created_at: "2026-11-25T20:00:00Z",
        }}
        skipInitialFetch
      >
        <Navbar />
      </AuthProvider>,
    );

    expect(screen.getByRole("link", { name: "João Pedro" })).toHaveAttribute(
      "href",
      "/profile/joao",
    );
    await userEvent.click(screen.getByRole("button", { name: "Sair" }));

    await waitFor(() => expect(fakeLogout.called).toBe(true));
    expect(screen.getByRole("link", { name: "Entrar" })).toBeInTheDocument();
  });

  it("renders Footer summary and navigation links", () => {
    render(<Footer />);

    expect(
      screen.getByText(/Avalie filmes, séries, animes, jogos e livros em um só lugar/i),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Login" })).toHaveAttribute("href", "/login");
    expect(screen.getByRole("link", { name: "Cadastro" })).toHaveAttribute("href", "/register");
  });
});
