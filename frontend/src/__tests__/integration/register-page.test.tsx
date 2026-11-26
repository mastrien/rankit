import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import RegisterPage from "@/app/register/page";
import { AuthProvider } from "@/components/auth/AuthProvider";
import { ApiClient, type FetchLike } from "@/lib/api-client";

const pushMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

class FakeRegisterFetch {
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

async function fillAndSubmitRegisterForm() {
  await userEvent.type(screen.getByLabelText("Nome de exibição"), "Fabio");
  await userEvent.type(screen.getByLabelText("Usuário"), "fabio");
  await userEvent.type(screen.getByLabelText("E-mail"), "fabio@example.com");
  await userEvent.type(screen.getByLabelText("Senha"), "StrongPassword!2026");
  await userEvent.type(screen.getByLabelText("Confirmar senha"), "StrongPassword!2026");
  await userEvent.click(screen.getByRole("button", { name: "Cadastrar" }));
}

describe("RegisterPage", () => {
  it("validates password confirmation locally before calling API", async () => {
    const client = new ApiClient("http://localhost:8000", new FakeRegisterFetch(201, {}).call);

    render(
      <AuthProvider apiClient={client} skipInitialFetch>
        <RegisterPage />
      </AuthProvider>,
    );

    await userEvent.type(screen.getByLabelText("Nome de exibição"), "Fabio");
    await userEvent.type(screen.getByLabelText("Usuário"), "fabio");
    await userEvent.type(screen.getByLabelText("E-mail"), "fabio@example.com");
    await userEvent.type(screen.getByLabelText("Senha"), "StrongPassword!2026");
    await userEvent.type(screen.getByLabelText("Confirmar senha"), "MismatchPassword!2026");
    await userEvent.click(screen.getByRole("button", { name: "Cadastrar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("As senhas não coincidem.");
  });

  it("registers account and redirects on success", async () => {
    pushMock.mockReset();
    const okClient = new ApiClient(
      "http://localhost:8000",
      new FakeRegisterFetch(201, {
        id: 2,
        username: "fabio",
        display_name: "Fabio",
        email: "fabio@example.com",
        bio: "",
        icon_id: 0,
        banner_id: 0,
        created_at: "2026-11-25T20:00:00Z",
      }).call,
    );

    render(
      <AuthProvider apiClient={okClient} skipInitialFetch>
        <RegisterPage />
      </AuthProvider>,
    );

    await fillAndSubmitRegisterForm();
    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/"));
  });

  it("surfaces DRF serializer field errors when registration is rejected", async () => {
    const errorClient = new ApiClient(
      "http://localhost:8000",
      new FakeRegisterFetch(400, {
        username: ["Já existe um usuário com este nome de usuário."],
      }).call,
    );

    render(
      <AuthProvider apiClient={errorClient} skipInitialFetch>
        <RegisterPage />
      </AuthProvider>,
    );

    await fillAndSubmitRegisterForm();
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Já existe um usuário com este nome de usuário.",
    );
  });
});
