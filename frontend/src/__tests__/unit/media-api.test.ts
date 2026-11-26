import { describe, expect, it } from "vitest";
import { ApiClient, type FetchLike } from "@/lib/api-client";
import {
  fetchMediaCategories,
  fetchMediaDetail,
  isMediaCategoryId,
  MEDIA_CATEGORY_LABELS,
  searchMedia,
} from "@/lib/media-api";

class RecordingMediaFetch {
  public requestedUrls: string[] = [];

  public call: FetchLike = async (input) => {
    this.requestedUrls.push(String(input));
    if (String(input).endsWith("/categories/")) {
      return new Response(
        JSON.stringify([{ id: "movie", name: "Filmes", provider: "Catálogo Local" }]),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }
    if (String(input).includes("/search/")) {
      return new Response(
        JSON.stringify([
          {
            external_id: "tt0468569",
            category: "movie",
            title: "Batman: O Cavaleiro das Trevas",
            poster_url: "/assets/banners/0.png",
            release_year: "2008",
            score: 9.0,
          },
        ]),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }
    return new Response(
      JSON.stringify({
        id: 1,
        universal_id: "game_1942",
        category: "game",
        external_id: "1942",
        title: "The Witcher 3",
        description: "RPG",
        score: 9.3,
        poster_url: "/assets/banners/6.png",
        banner_url: "/assets/banners/6.png",
        release_year: "2015",
        origin_country: "PL",
        genres: ["RPG"],
        views_count: 0,
        created_at: "2026-11-26T00:00:00Z",
        updated_at: "2026-11-26T00:00:00Z",
      }),
      { status: 200, headers: { "Content-Type": "application/json" } },
    );
  };
}

describe("media-api client", () => {
  it("validates supported categories and queries categories, search, and detail", async () => {
    expect(isMediaCategoryId("movie")).toBe(true);
    expect(isMediaCategoryId("podcast")).toBe(false);
    expect(MEDIA_CATEGORY_LABELS.game).toBe("Jogos");

    const recorder = new RecordingMediaFetch();
    const client = new ApiClient("http://localhost:8000", recorder.call);

    const categories = await fetchMediaCategories(client);
    expect(categories[0]?.id).toBe("movie");

    const hits = await searchMedia("movie", "  Batman ", client, 10);
    expect(hits[0]?.external_id).toBe("tt0468569");

    const detail = await fetchMediaDetail("game", "1942", client);
    expect(detail.title).toBe("The Witcher 3");

    expect(recorder.requestedUrls).toEqual([
      "http://localhost:8000/api/v1/media/categories/",
      "http://localhost:8000/api/v1/media/search/?category=movie&q=Batman&limit=10",
      "http://localhost:8000/api/v1/media/game/1942/",
    ]);
  });
});
