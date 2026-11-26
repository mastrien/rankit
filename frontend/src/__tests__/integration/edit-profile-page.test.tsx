import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import EditProfilePage from "@/app/profile/edit/page";
import { AuthProvider } from "@/components/auth/AuthProvider";
import { EditProfileForm } from "@/components/profile/EditProfileForm";
import { ApiClient, type FetchLike } from "@/lib/api-client";

const pushMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

class FakeEditProfileFetch {
  public lastPatchBody: Record<string, unknown> | null = null;
  private readonly patchStatus: number;
  private readonly errorPayload: Record<string, unknown>;

  constructor(
    patchStatus = 200,
    errorPayload: Record<string, unknown> = { detail: "Erro ao salvar perfil." },
  ) {
    this.patchStatus = patchStatus;
    this.errorPayload = errorPayload;
  }

  public call: FetchLike = async (input, init) => {
    const url = String(input);
    const method = init?.method ?? "GET";

    if (url.endsWith("/api/v1/profiles/presets/")) {
      return new Response(JSON.stringify({ icons: [0, 1, 2, 3], banners: [0, 1, 2] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }
    if (url.endsWith("/api/v1/auth/me/")) {
      return new Response(
        JSON.stringify({
          id: 1,
          username: "alice",
          display_name: "Alice Nova",
          email: "alice@example.com",
          bio: "Bio nova",
          icon_id: 2,
          banner_id: 1,
          created_at: "2026-11-25T20:00:00Z",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }
    if (url.endsWith("/api/v1/profiles/me/") && method === "PATCH") {
      this.lastPatchBody = JSON.parse(String(init?.body)) as Record<string, unknown>;
      if (this.patchStatus !== 200) {
        return new Response(JSON.stringify(this.errorPayload), {
          status: this.patchStatus,
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response(
        JSON.stringify({
          id: 1,
          username: "alice",
          display_name: "Alice Nova",
          bio: "Bio nova",
          icon_id: 2,
          banner_id: 1,
          followers_count: 0,
          following_count: 0,
          is_following: false,
          is_self: true,
          created_at: "2026-11-25T20:00:00Z",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }
    return new Response(null, { status: 500 });
  };
}

const SAMPLE_USER = {
  id: 1,
  username: "alice",
  display_name: "Alice",
  email: "alice@example.com",
  bio: "",
  icon_id: 0,
  banner_id: 0,
  created_at: "2026-11-25T20:00:00Z",
};

describe("EditProfilePage", () => {
  it("prompts login when visitor is unauthenticated", () => {
    const client = new ApiClient("http://localhost:8000", new FakeEditProfileFetch().call);

    render(
      <AuthProvider apiClient={client} skipInitialFetch>
        <EditProfilePage />
      </AuthProvider>,
    );

    expect(screen.getByText(/Você precisa entrar para editar seu perfil/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Ir para login" })).toHaveAttribute("href", "/login");
  });

  it("updates display name, bio, icon, and banner and redirects to profile", async () => {
    pushMock.mockReset();
    const fake = new FakeEditProfileFetch(200);
    const client = new ApiClient("http://localhost:8000", fake.call);

    render(
      <AuthProvider apiClient={client} initialUser={SAMPLE_USER} skipInitialFetch>
        <EditProfileForm apiClient={client} />
      </AuthProvider>,
    );

    const nameInput = await screen.findByLabelText("Nome de exibição");
    await userEvent.clear(nameInput);
    await userEvent.type(nameInput, "Alice Nova");
    await userEvent.type(screen.getByLabelText(/Biografia/i), "Bio nova");
    await userEvent.click(await screen.findByRole("button", { name: "Ícone 2" }));
    await userEvent.click(await screen.findByRole("button", { name: "Banner 1" }));
    await userEvent.click(screen.getByRole("button", { name: "Salvar alterações" }));

    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/profile/alice"));
    expect(fake.lastPatchBody).toEqual({
      display_name: "Alice Nova",
      bio: "Bio nova",
      icon_id: 2,
      banner_id: 1,
    });
  });

  it("displays alert when profile update fails", async () => {
    const fake = new FakeEditProfileFetch(400);
    const client = new ApiClient("http://localhost:8000", fake.call);

    render(
      <AuthProvider apiClient={client} initialUser={SAMPLE_USER} skipInitialFetch>
        <EditProfileForm apiClient={client} />
      </AuthProvider>,
    );

    await userEvent.click(screen.getByRole("button", { name: "Salvar alterações" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Erro ao salvar perfil.");
  });

  it("formats DRF serializer field errors on edit profile rejection", async () => {
    const fake = new FakeEditProfileFetch(400, {
      bio: ["A biografia excedeu o limite permitido."],
    });
    const client = new ApiClient("http://localhost:8000", fake.call);

    render(
      <AuthProvider apiClient={client} initialUser={SAMPLE_USER} skipInitialFetch>
        <EditProfileForm apiClient={client} />
      </AuthProvider>,
    );

    await userEvent.click(screen.getByRole("button", { name: "Salvar alterações" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "A biografia excedeu o limite permitido.",
    );
  });
});
