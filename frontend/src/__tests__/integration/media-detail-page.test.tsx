import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import MediaDetailPage from "@/app/media/[category]/[id]/page";
import { MediaDetailView } from "@/components/media/MediaDetailView";
import { ApiClient, type FetchLike } from "@/lib/api-client";

class FakeMediaDetailFetch {
  public call: FetchLike = async (input) => {
    const url = String(input);
    if (url.includes("/missing/")) {
      return new Response(JSON.stringify({ detail: "Not found" }), {
        status: 404,
        headers: { "Content-Type": "application/json" },
      });
    }
    if (url.includes("/boom/")) {
      return new Response(JSON.stringify({ detail: "Bad gateway" }), {
        status: 502,
        headers: { "Content-Type": "application/json" },
      });
    }
    if (url.includes("/sparse/")) {
      return new Response(
        JSON.stringify({
          id: 2,
          universal_id: "book_sparse",
          category: "book",
          external_id: "sparse",
          title: "Obra Sem Metadados",
          description: "",
          score: 7.5,
          poster_url: "",
          banner_url: "",
          release_year: "",
          origin_country: "",
          genres: [],
          views_count: 0,
          created_at: "2026-11-26T00:00:00Z",
          updated_at: "2026-11-26T00:00:00Z",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }
    return new Response(
      JSON.stringify({
        id: 1,
        universal_id: "movie_tt0468569",
        category: "movie",
        external_id: "tt0468569",
        title: "Batman: O Cavaleiro das Trevas",
        description: "Batman enfrenta o Coringa em Gotham.",
        score: 9.0,
        poster_url: "/assets/banners/0.png",
        banner_url: "/assets/banners/0.png",
        release_year: "2008",
        origin_country: "US",
        genres: ["Ação", "Drama"],
        views_count: 4,
        created_at: "2026-11-26T00:00:00Z",
        updated_at: "2026-11-26T00:00:00Z",
      }),
      { status: 200, headers: { "Content-Type": "application/json" } },
    );
  };
}

describe("MediaDetailPage", () => {
  it("renders cached detail with genres, score, and back link", async () => {
    const client = new ApiClient("http://localhost:8000", new FakeMediaDetailFetch().call);

    render(<MediaDetailView apiClient={client} category="movie" externalId="tt0468569" />);

    expect(
      await screen.findByRole("heading", { name: "Batman: O Cavaleiro das Trevas" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Batman enfrenta o Coringa em Gotham.")).toBeInTheDocument();
    expect(screen.getByText("Ação")).toBeInTheDocument();
    expect(screen.getByText("Nota 9.0")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Voltar para busca em Filmes/i })).toHaveAttribute(
      "href",
      "/search?category=movie",
    );
  });

  it("handles sparse metadata fallbacks, 404, 502, and resolves MediaDetailPage params", async () => {
    const client = new ApiClient("http://localhost:8000", new FakeMediaDetailFetch().call);

    const { rerender } = render(
      <MediaDetailView apiClient={client} category="book" externalId="sparse" />,
    );
    expect(await screen.findByRole("heading", { name: "Obra Sem Metadados" })).toBeInTheDocument();
    expect(screen.getByText("Sinopse ainda não disponível.")).toBeInTheDocument();

    rerender(<MediaDetailView apiClient={client} category="movie" externalId="missing" />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Obra não encontrada.");

    rerender(<MediaDetailView apiClient={client} category="movie" externalId="boom" />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Não foi possível carregar os detalhes desta obra.",
    );

    const pageEl = await MediaDetailPage({
      params: Promise.resolve({ category: "movie", id: "tt0468569" }),
    });
    expect(pageEl).toBeTruthy();
  });
});
