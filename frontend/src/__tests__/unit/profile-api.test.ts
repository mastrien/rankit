import { describe, expect, it } from "vitest";
import { ApiClient, type FetchLike } from "@/lib/api-client";
import {
  fetchFollowers,
  fetchFollowing,
  fetchFollowSuggestions,
  fetchProfile,
  fetchProfilePresets,
  followUser,
  unfollowUser,
  updateOwnProfile,
} from "@/lib/profile-api";

const SAMPLE_PROFILE = {
  id: 1,
  username: "alice",
  display_name: "Alice",
  bio: "Cinéfila",
  icon_id: 3,
  banner_id: 2,
  followers_count: 10,
  following_count: 5,
  is_following: false,
  is_self: true,
  created_at: "2026-11-25T20:00:00Z",
};

const SAMPLE_SUMMARY = {
  id: 2,
  username: "bob",
  display_name: "Bob",
  icon_id: 1,
};

class FakeProfileFetch {
  private readonly status: number;
  private readonly payload: unknown;

  constructor(status: number, payload: unknown) {
    this.status = status;
    this.payload = payload;
  }

  public call: FetchLike = async () =>
    new Response(this.status === 204 ? null : JSON.stringify(this.payload), {
      status: this.status,
      headers: { "Content-Type": "application/json" },
    });
}

describe("profile-api", () => {
  it("fetches and updates profile, presets, follow lists, and suggestions", async () => {
    const profileClient = new ApiClient(
      "http://localhost:8000",
      new FakeProfileFetch(200, SAMPLE_PROFILE).call,
    );
    expect((await fetchProfile("alice", profileClient)).username).toBe("alice");
    expect(
      (
        await updateOwnProfile(
          { display_name: "Alice", bio: "Bio", icon_id: 3, banner_id: 2 },
          profileClient,
        )
      ).icon_id,
    ).toBe(3);

    const presetsClient = new ApiClient(
      "http://localhost:8000",
      new FakeProfileFetch(200, { icons: [0, 1], banners: [0] }).call,
    );
    expect(await fetchProfilePresets(presetsClient)).toEqual({ icons: [0, 1], banners: [0] });

    const listClient = new ApiClient(
      "http://localhost:8000",
      new FakeProfileFetch(200, [SAMPLE_SUMMARY]).call,
    );
    expect(await fetchFollowers("alice", listClient)).toEqual([SAMPLE_SUMMARY]);
    expect(await fetchFollowing("alice", listClient)).toEqual([SAMPLE_SUMMARY]);
    expect(await fetchFollowSuggestions("alice", listClient)).toEqual([SAMPLE_SUMMARY]);

    const followClient = new ApiClient(
      "http://localhost:8000",
      new FakeProfileFetch(201, { detail: "ok" }).call,
    );
    await expect(followUser("bob", followClient)).resolves.toBeUndefined();

    const unfollowClient = new ApiClient(
      "http://localhost:8000",
      new FakeProfileFetch(204, null).call,
    );
    await expect(unfollowUser("bob", unfollowClient)).resolves.toBeUndefined();
  });

  it("throws descriptive errors on malformed profile, preset, or summary payloads", async () => {
    const badClient = new ApiClient("http://localhost:8000", new FakeProfileFetch(200, {}).call);
    const nullClient = new ApiClient("http://localhost:8000", new FakeProfileFetch(200, null).call);
    const badListClient = new ApiClient(
      "http://localhost:8000",
      new FakeProfileFetch(200, [null]).call,
    );

    await expect(fetchProfile("alice", badClient)).rejects.toThrow(/Invalid ProfileDetail payload/);
    await expect(fetchProfile("alice", nullClient)).rejects.toThrow(
      /Invalid ProfileDetail payload/,
    );
    await expect(fetchProfilePresets(badClient)).rejects.toThrow(/Invalid ProfilePresets payload/);
    await expect(fetchProfilePresets(nullClient)).rejects.toThrow(/Invalid ProfilePresets payload/);
    await expect(fetchFollowers("alice", badClient)).rejects.toThrow(
      /Invalid UserSummary\[\] payload/,
    );
    await expect(fetchFollowers("alice", badListClient)).rejects.toThrow(
      /Invalid UserSummary\[\] payload/,
    );
  });
});
