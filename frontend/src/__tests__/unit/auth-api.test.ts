import { describe, expect, it } from "vitest";
import { ApiClient, type FetchLike } from "@/lib/api-client";
import {
  fetchCurrentUser,
  loginUser,
  logoutUser,
  refreshSession,
  registerUser,
} from "@/lib/auth-api";

const SAMPLE_USER = {
  id: 1,
  username: "joao",
  display_name: "João Pedro",
  email: "joao@example.com",
  bio: "",
  icon_id: 0,
  banner_id: 0,
  created_at: "2026-11-25T20:00:00Z",
};

class FakeAuthFetch {
  public lastPath = "";
  private readonly status: number;
  private readonly payload: unknown;

  constructor(status: number, payload: unknown) {
    this.status = status;
    this.payload = payload;
  }

  public call: FetchLike = async (input) => {
    this.lastPath = String(input);
    return new Response(this.status === 204 ? null : JSON.stringify(this.payload), {
      status: this.status,
      headers: { "Content-Type": "application/json" },
    });
  };
}

describe("auth-api", () => {
  it("registers, logs in, fetches current user, refreshes, and logs out", async () => {
    const okFetch = new FakeAuthFetch(200, SAMPLE_USER);
    const client = new ApiClient("http://localhost:8000", okFetch.call);

    const registered = await registerUser(
      {
        display_name: "João Pedro",
        username: "joao",
        email: "joao@example.com",
        password: "StrongPassword!2026",
        password_confirm: "StrongPassword!2026",
      },
      client,
    );
    expect(registered.username).toBe("joao");
    expect(okFetch.lastPath).toContain("/api/v1/auth/register/");

    const loggedIn = await loginUser({ username: "joao", password: "StrongPassword!2026" }, client);
    expect(loggedIn.display_name).toBe("João Pedro");

    const me = await fetchCurrentUser(client);
    expect(me.email).toBe("joao@example.com");

    await expect(refreshSession(client)).resolves.toBeUndefined();

    const logoutFetch = new FakeAuthFetch(204, null);
    const logoutClient = new ApiClient("http://localhost:8000", logoutFetch.call);
    await expect(logoutUser(logoutClient)).resolves.toBeUndefined();
  });

  it("throws descriptive error when AuthUser payload shape is invalid", async () => {
    const badFetch = new FakeAuthFetch(200, { invalid: true });
    const client = new ApiClient("http://localhost:8000", badFetch.call);

    await expect(fetchCurrentUser(client)).rejects.toThrow(/Invalid AuthUser payload/);
    await expect(
      fetchCurrentUser(new ApiClient("http://localhost:8000", new FakeAuthFetch(200, null).call)),
    ).rejects.toThrow(/Invalid AuthUser payload/);
  });
});
