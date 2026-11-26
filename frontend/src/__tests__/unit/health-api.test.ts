import { describe, expect, it } from "vitest";
import { ApiClient, type FetchLike } from "@/lib/api-client";
import { fetchBackendHealth } from "@/lib/health-api";

class FakeHealthFetch {
  private readonly payload: unknown;

  constructor(payload: unknown) {
    this.payload = payload;
  }

  public call: FetchLike = async () =>
    new Response(JSON.stringify(this.payload), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
}

describe("fetchBackendHealth", () => {
  it("returns validated health payload", async () => {
    const fake = new FakeHealthFetch({ status: "ok", database: "ok" });
    const client = new ApiClient("http://localhost:8000", fake.call);

    const health = await fetchBackendHealth(client);

    expect(health).toEqual({ status: "ok", database: "ok" });
  });

  it("throws descriptive error when payload shape is invalid or null", async () => {
    const badClient = new ApiClient(
      "http://localhost:8000",
      new FakeHealthFetch({ status: "unknown" }).call,
    );
    const nullClient = new ApiClient("http://localhost:8000", new FakeHealthFetch(null).call);

    await expect(fetchBackendHealth(badClient)).rejects.toThrow(/Invalid backend health payload/);
    await expect(fetchBackendHealth(nullClient)).rejects.toThrow(/Invalid backend health payload/);
  });
});
