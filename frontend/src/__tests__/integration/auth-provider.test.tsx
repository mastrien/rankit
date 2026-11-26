import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { AuthProvider, useAuth } from "@/components/auth/AuthProvider";
import { ApiClient, type FetchLike } from "@/lib/api-client";

const SAMPLE_USER = {
  id: 7,
  username: "nathan",
  display_name: "Nathan",
  email: "nathan@example.com",
  bio: "",
  icon_id: 2,
  banner_id: 1,
  created_at: "2026-11-25T20:00:00Z",
};

class SequenceAuthFetch {
  private readonly handlers: readonly (() => Response)[];
  private index = 0;

  constructor(handlers: readonly (() => Response)[]) {
    this.handlers = handlers;
  }

  public call: FetchLike = async () => {
    const handler = this.handlers[this.index] ?? this.handlers[this.handlers.length - 1];
    this.index += 1;
    if (!handler) {
      return new Response(null, { status: 500 });
    }
    return handler();
  };
}

function ProbeConsumer() {
  const { user, isLoading, logout } = useAuth();
  if (isLoading) {
    return <span>loading</span>;
  }
  return (
    <div>
      <span>{user ? user.username : "anon"}</span>
      {user ? (
        <button onClick={() => void logout()} type="button">
          do-logout
        </button>
      ) : null}
    </div>
  );
}

describe("AuthProvider", () => {
  it("recovers session via refresh endpoint when /me/ returns 401", async () => {
    const seq = new SequenceAuthFetch([
      () => new Response(JSON.stringify({ detail: "expired" }), { status: 401, headers: { "Content-Type": "application/json" } }),
      () => new Response(JSON.stringify({ detail: "ok" }), { status: 200, headers: { "Content-Type": "application/json" } }),
      () => new Response(JSON.stringify(SAMPLE_USER), { status: 200, headers: { "Content-Type": "application/json" } }),
      () => new Response(null, { status: 204 }),
    ]);
    const client = new ApiClient("http://localhost:8000", seq.call);

    render(
      <AuthProvider apiClient={client}>
        <ProbeConsumer />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByText("nathan")).toBeInTheDocument());

    await userEvent.click(screen.getByRole("button", { name: "do-logout" }));
    await waitFor(() => expect(screen.getByText("anon")).toBeInTheDocument());
  });

  it("sets user to null when both /me/ and /refresh/ fail", async () => {
    const seq = new SequenceAuthFetch([
      () => new Response(JSON.stringify({ detail: "unauthorized" }), { status: 401, headers: { "Content-Type": "application/json" } }),
      () => new Response(JSON.stringify({ detail: "invalid refresh" }), { status: 401, headers: { "Content-Type": "application/json" } }),
    ]);
    const client = new ApiClient("http://localhost:8000", seq.call);

    render(
      <AuthProvider apiClient={client}>
        <ProbeConsumer />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByText("anon")).toBeInTheDocument());
  });

  it("sets user to null on non-401 error and throws when useAuth is used outside provider", async () => {
    const seq = new SequenceAuthFetch([
      () => new Response(JSON.stringify({ detail: "server error" }), { status: 500, headers: { "Content-Type": "application/json" } }),
    ]);
    const client = new ApiClient("http://localhost:8000", seq.call);

    render(
      <AuthProvider apiClient={client}>
        <ProbeConsumer />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByText("anon")).toBeInTheDocument());
    expect(() => render(<ProbeConsumer />)).toThrow(/useAuth must be used inside/);
  });
});
