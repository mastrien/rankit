import { describe, expect, it, vi } from "vitest";
import { ApiClient, ApiClientError, type FetchLike } from "@/lib/api-client";

class FakeJsonFetch {
  public lastUrl = "";
  public lastInit: RequestInit | undefined;
  private readonly status: number;
  private readonly payload: unknown;

  constructor(status: number, payload: unknown) {
    this.status = status;
    this.payload = payload;
  }

  public call: FetchLike = async (input, init) => {
    this.lastUrl = String(input);
    this.lastInit = init;
    return new Response(this.status === 204 ? null : JSON.stringify(this.payload), {
      status: this.status,
      headers: { "Content-Type": "application/json" },
    });
  };
}

describe("ApiClient", () => {
  it("sends credentials include and JSON headers on POST", async () => {
    const fake = new FakeJsonFetch(200, { ok: true });
    const client = new ApiClient("http://localhost:8000", fake.call);

    const result = await client.post<{ ok: boolean }>("/api/v1/test/", { name: "rankit" });

    expect(result).toEqual({ ok: true });
    expect(fake.lastUrl).toBe("http://localhost:8000/api/v1/test/");
    expect(fake.lastInit?.credentials).toBe("include");
    expect(fake.lastInit?.method).toBe("POST");
  });

  it("handles 204 No Content on DELETE", async () => {
    const fake = new FakeJsonFetch(204, null);
    const client = new ApiClient("http://localhost:8000", fake.call);

    const result = await client.delete<null>("/api/v1/resource/");

    expect(result).toBeNull();
    expect(fake.lastInit?.method).toBe("DELETE");
  });

  it("supports PATCH with serialized JSON payload", async () => {
    const fake = new FakeJsonFetch(200, { updated: true });
    const client = new ApiClient("http://localhost:8000", fake.call);

    const result = await client.patch<{ updated: boolean }>("/api/v1/me/", { bio: "hi" });

    expect(result).toEqual({ updated: true });
    expect(fake.lastInit?.method).toBe("PATCH");
  });

  it("throws ApiClientError with detail message on HTTP failure", async () => {
    const fake = new FakeJsonFetch(401, { detail: "Credenciais inválidas." });
    const client = new ApiClient("http://localhost:8000", fake.call);

    await expect(client.get("/api/v1/auth/me/")).rejects.toThrowError(ApiClientError);
    await expect(client.get("/api/v1/auth/me/")).rejects.toMatchObject({
      status: 401,
      message: "Credenciais inválidas.",
    });
  });

  it("falls back to descriptive HTTP error when payload has no detail", async () => {
    const fake = new FakeJsonFetch(500, { error: "boom" });
    const client = new ApiClient("http://localhost:8000", fake.call);

    await expect(client.get("/api/v1/health/")).rejects.toMatchObject({
      status: 500,
      message:
        "Request to http://localhost:8000/api/v1/health/ failed with HTTP status 500 (expected 2xx JSON response).",
    });
  });

  it("uses globalThis.fetch when no custom fetcher is injected", async () => {
    const fake = new FakeJsonFetch(200, { status: "ok" });
    vi.stubGlobal("fetch", fake.call);
    try {
      const client = new ApiClient("http://localhost:8000");
      const result = await client.get<{ status: string }>("/api/v1/health/");
      expect(result).toEqual({ status: "ok" });
    } finally {
      vi.unstubAllGlobals();
    }
  });
});
