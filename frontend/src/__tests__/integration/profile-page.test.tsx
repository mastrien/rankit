import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import ProfilePage from "@/app/profile/[username]/page";
import { AuthProvider } from "@/components/auth/AuthProvider";
import { ApiClient, type FetchLike } from "@/lib/api-client";

class FakeProfileRouterFetch {
  public isFollowing = false;
  public followersCount = 1;

  public call: FetchLike = async (input, init) => {
    const url = String(input);
    const method = init?.method ?? "GET";

    if (url.endsWith("/api/v1/profiles/missing/")) {
      return new Response(JSON.stringify({ detail: "Perfil não encontrado." }), {
        status: 404,
        headers: { "Content-Type": "application/json" },
      });
    }
    if (url.endsWith("/api/v1/profiles/bob/") && method === "GET") {
      return new Response(
        JSON.stringify({
          id: 2,
          username: "bob",
          display_name: "Bob",
          bio: "",
          icon_id: 1,
          banner_id: 2,
          followers_count: this.followersCount,
          following_count: 1,
          is_following: this.isFollowing,
          is_self: false,
          created_at: "2026-11-25T20:00:00Z",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }
    if (url.endsWith("/api/v1/profiles/alice/") && method === "GET") {
      return new Response(
        JSON.stringify({
          id: 1,
          username: "alice",
          display_name: "Alice",
          bio: "Amo cinema",
          icon_id: 0,
          banner_id: 0,
          followers_count: 0,
          following_count: 0,
          is_following: false,
          is_self: true,
          created_at: "2026-11-25T20:00:00Z",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }
    if (url.endsWith("/api/v1/profiles/bob/suggestions/")) {
      return new Response(
        JSON.stringify([{ id: 3, username: "carol", display_name: "Carol", icon_id: 4 }]),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }
    if (url.endsWith("/follow/") && method === "POST") {
      this.isFollowing = true;
      this.followersCount += 1;
      return new Response(JSON.stringify({ detail: "ok" }), {
        status: 201,
        headers: { "Content-Type": "application/json" },
      });
    }
    if (url.endsWith("/follow/") && method === "DELETE") {
      this.isFollowing = false;
      this.followersCount -= 1;
      return new Response(null, { status: 204 });
    }
    if (url.endsWith("/followers/")) {
      return new Response(
        JSON.stringify([{ id: 4, username: "dave", display_name: "Dave", icon_id: 5 }]),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }
    if (url.endsWith("/following/")) {
      return new Response(JSON.stringify([]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }
    return new Response(null, { status: 500 });
  };
}

const VIEWER_ALICE = {
  id: 1,
  username: "alice",
  display_name: "Alice",
  email: "alice@example.com",
  bio: "Amo cinema",
  icon_id: 0,
  banner_id: 0,
  created_at: "2026-11-25T20:00:00Z",
};

describe("ProfilePage", () => {
  it("renders own profile with edit button", async () => {
    const fake = new FakeProfileRouterFetch();
    const client = new ApiClient("http://localhost:8000", fake.call);
    const { ProfileView } = await import("@/components/profile/ProfileView");

    render(
      <AuthProvider apiClient={client} initialUser={VIEWER_ALICE} skipInitialFetch>
        <ProfileView apiClient={client} username="alice" />
      </AuthProvider>,
    );

    expect(await screen.findByRole("heading", { name: "Alice" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Editar perfil" })).toHaveAttribute(
      "href",
      "/profile/edit",
    );
  });

  it("handles follow, unfollow, suggestions, and followers/following modals", async () => {
    const fake = new FakeProfileRouterFetch();
    const client = new ApiClient("http://localhost:8000", fake.call);
    const { ProfileView } = await import("@/components/profile/ProfileView");

    render(
      <AuthProvider apiClient={client} initialUser={VIEWER_ALICE} skipInitialFetch>
        <ProfileView apiClient={client} username="bob" />
      </AuthProvider>,
    );

    expect(await screen.findByRole("heading", { name: "Bob" })).toBeInTheDocument();
    expect(screen.getByText("Carol")).toBeInTheDocument();

    const followButtons = screen.getAllByRole("button", { name: "Seguir" });
    await userEvent.click(followButtons[0]!);
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Seguindo" })).toBeInTheDocument(),
    );

    await userEvent.click(screen.getByRole("button", { name: "Seguindo" }));
    await waitFor(() => expect(screen.getAllByRole("button", { name: "Seguir" }).length).toBe(2));

    await userEvent.click(screen.getAllByRole("button", { name: "Seguir" })[1]!);
    await waitFor(() => expect(screen.queryByText("Carol")).not.toBeInTheDocument());

    await userEvent.click(screen.getByRole("button", { name: /Seguidores/i }));
    expect(await screen.findByRole("dialog")).toHaveTextContent("Dave");
    await userEvent.click(screen.getByRole("button", { name: "Fechar" }));

    await userEvent.click(screen.getByRole("button", { name: /Seguindo/i }));
    expect(await screen.findByRole("dialog")).toHaveTextContent("Nenhum usuário encontrado.");
    await userEvent.click(screen.getByRole("button", { name: "Fechar" }));
  });

  it("renders 404 alert for unknown profile and resolves async ProfilePage params", async () => {
    const fake = new FakeProfileRouterFetch();
    const client = new ApiClient("http://localhost:8000", fake.call);
    const { ProfileView } = await import("@/components/profile/ProfileView");

    render(
      <AuthProvider apiClient={client} skipInitialFetch>
        <ProfileView apiClient={client} username="missing" />
      </AuthProvider>,
    );

    expect(await screen.findByRole("alert")).toHaveTextContent("Perfil não encontrado.");

    const pageElement = await ProfilePage({ params: Promise.resolve({ username: "alice" }) });
    expect(pageElement).toBeTruthy();
  });

  it("degrades suggestions cleanly on 500, shows inline action alerts, and closes modal on Escape", async () => {
    const baseFake = new FakeProfileRouterFetch();
    let failSuggestions = true;
    let failFollow = false;
    let failFollowersList = false;

    const client = new ApiClient("http://localhost:8000", async (input, init) => {
      const url = String(input);
      const method = init?.method ?? "GET";
      if (url.endsWith("/suggestions/") && failSuggestions) {
        return new Response(null, { status: 500 });
      }
      if (url.endsWith("/follow/") && method === "POST" && failFollow) {
        return new Response(null, { status: 500 });
      }
      if (url.endsWith("/followers/") && failFollowersList) {
        return new Response(null, { status: 500 });
      }
      return baseFake.call(input, init);
    });
    const { ProfileView } = await import("@/components/profile/ProfileView");

    const { rerender } = render(
      <AuthProvider apiClient={client} initialUser={VIEWER_ALICE} skipInitialFetch>
        <ProfileView apiClient={client} username="bob" />
      </AuthProvider>,
    );

    expect(await screen.findByRole("heading", { name: "Bob" })).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();

    failSuggestions = false;
    failFollow = true;
    rerender(
      <AuthProvider apiClient={client} initialUser={VIEWER_ALICE} skipInitialFetch>
        <ProfileView apiClient={client} username="bob" />
      </AuthProvider>,
    );
    await userEvent.click(screen.getAllByRole("button", { name: "Seguir" })[0]!);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Não foi possível atualizar o status de seguidor.",
    );

    const suggestButtons = screen.getAllByRole("button", { name: "Seguir" });
    if (suggestButtons[1]) {
      await userEvent.click(suggestButtons[1]);
      expect(await screen.findByRole("alert")).toHaveTextContent(
        "Não foi possível seguir a sugestão selecionada.",
      );
    }

    failFollowersList = true;
    await userEvent.click(screen.getByRole("button", { name: /Seguidores/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Não foi possível carregar a lista de conexões.",
    );

    failFollowersList = false;
    await userEvent.click(screen.getByRole("button", { name: /Seguidores/i }));
    const dialog = await screen.findByRole("dialog");
    const labelledBy = dialog.getAttribute("aria-labelledby");
    expect(labelledBy).toBeTruthy();
    expect(document.getElementById(labelledBy!)?.textContent).toBe("Seguidores");

    await userEvent.keyboard("{Escape}");
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
  });
});
