import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import LoginPage from "@/app/login/page";
import { AuthProvider } from "@/components/auth/AuthProvider";
import { ApiClient, type FetchLike } from "@/lib/api-client";

const pushMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

class FakeLoginFetch {
  private readonly status: number;
  private readonly payload: unknown;

  constructor(status: number, payload: unknown) {
    this.status = status;
    this.payload = payload;
  }

  public call: FetchLike = async () =>
    new Response(JSON.stringify(this.payload), {
      status: this.status,
      headers: { "Content-Type": "application/json" },
    });
}

describe("LoginPage", () => {
  it("submits credentials and redirects to home on success", async () => {
    pushMock.mockReset();
    const fake = new FakeLoginFetch(200, {
      id: 1,
      username: "joao",
      display_name: "João",
      email: "joao@example.com",
      bio: "",
      icon_id: 0,
      banner_id: 0,
      created_at: "2026-11-25T20:00:00Z",
    });
    const client = new ApiClient("http://localhost:8000", fake.call);

    render(
      <AuthProvider apiClient={client} skipInitialFetch>
        <LoginPage />
      </AuthProvider>,
    );

    await userEvent.type(screen.getByLabelText("Usuário"), "joao");
    await userEvent.type(screen.getByLabelText("Senha"), "StrongPassword!2026");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));

    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/"));
  });

  it("displays API error alert when login fails", async () => {
    const fake = new FakeLoginFetch(401, { detail: "Usuário ou senha incorretos." });
    const client = new ApiClient("http://localhost:8000", fake.call);

    render(
      <AuthProvider apiClient={client} skipInitialFetch>
        <LoginPage />
      </AuthProvider>,
    );

    await userEvent.type(screen.getByLabelText("Usuário"), "joao");
    await userEvent.type(screen.getByLabelText("Senha"), "wrongpass");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Usuário ou senha incorretos.");
  });
});
