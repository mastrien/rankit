import { ApiClient } from "@/lib/api-client";

export type MediaCategoryId = "movie" | "serie" | "anime" | "game" | "book";

export interface MediaCategoryInfo {
  readonly id: MediaCategoryId;
  readonly name: string;
  readonly provider: string;
}

export interface MediaSearchResult {
  readonly external_id: string;
  readonly category: MediaCategoryId;
  readonly title: string;
  readonly poster_url: string;
  readonly release_year: string;
  readonly score: number;
}

export interface MediaDetail {
  readonly id: number;
  readonly universal_id: string;
  readonly category: MediaCategoryId;
  readonly external_id: string;
  readonly title: string;
  readonly description: string;
  readonly score: number;
  readonly poster_url: string;
  readonly banner_url: string;
  readonly release_year: string;
  readonly origin_country: string;
  readonly genres: readonly string[];
  readonly views_count: number;
  readonly created_at: string;
  readonly updated_at: string;
}

export const MEDIA_CATEGORY_LABELS: Record<MediaCategoryId, string> = {
  movie: "Filmes",
  serie: "Séries",
  anime: "Animes",
  game: "Jogos",
  book: "Livros",
};

const VALID_CATEGORIES = new Set<string>(Object.keys(MEDIA_CATEGORY_LABELS));

/** Runtime guard checking whether a string matches one of the 5 Rankit media categories. */
export function isMediaCategoryId(value: string): value is MediaCategoryId {
  return VALID_CATEGORIES.has(value);
}

/** Fetch supported media categories and active provider names. */
export async function fetchMediaCategories(
  client: ApiClient = new ApiClient(),
): Promise<MediaCategoryInfo[]> {
  return client.request<MediaCategoryInfo[]>("/api/v1/media/categories/", {
    method: "GET",
  });
}

/** Search catalog entries by category slug and text query. */
export async function searchMedia(
  category: MediaCategoryId,
  query: string,
  client: ApiClient = new ApiClient(),
  limit = 15,
): Promise<MediaSearchResult[]> {
  const params = new URLSearchParams({
    category,
    q: query.trim(),
    limit: String(limit),
  });
  return client.request<MediaSearchResult[]>(`/api/v1/media/search/?${params.toString()}`, {
    method: "GET",
  });
}

/** Retrieve full cached or hydrated media details by category and external ID. */
export async function fetchMediaDetail(
  category: string,
  externalId: string,
  client: ApiClient = new ApiClient(),
): Promise<MediaDetail> {
  return client.request<MediaDetail>(
    `/api/v1/media/${encodeURIComponent(category)}/${encodeURIComponent(externalId)}/`,
    { method: "GET" },
  );
}
