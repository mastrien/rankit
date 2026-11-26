import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import SearchPage from "@/app/search/page";
import { MediaSearchView } from "@/components/media/MediaSearchView";
import { ApiClient, type FetchLike } from "@/lib/api-client";

class FakeSearchFetch {
  public mode: "results" | "empty" | "error" = "results";

  public call: FetchLike = async (input) => {
    const url = String(input);
    if (this.mode === "error") {
      return new Response(JSON.stringify({ detail: "Upstream error" }), {
        status: 502,
        headers: { "Content-Type": "application/json" },
      });
    }
    if (this.mode === "empty") {
      return new Response(JSON.stringify([]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }
    if (url.includes("category=game")) {
      return new Response(
        JSON.stringify([
          {
            external_id: "119133",
            category: "game",
            title: "Elden Ring",
            poster_url: "",
            release_year: "",
            score: 9.5,
          },
        ]),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }
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
  };
}

describe("SearchPage", () => {
  it("validates empty input, switches categories, renders cards, empty states, and errors", async () => {
    const fake = new FakeSearchFetch();
    const client = new ApiClient("http://localhost:8000", fake.call);

    render(<MediaSearchView apiClient={client} />);

    await userEvent.click(screen.getByRole("button", { name: "Buscar" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Digite um termo para buscar no catálogo.",
    );

    await userEvent.click(screen.getByRole("button", { name: "Jogos" }));
    expect(screen.getByRole("button", { name: "Jogos" })).toHaveAttribute("aria-pressed", "true");

    await userEvent.type(screen.getByLabelText("Buscar obra"), "elden");
    await userEvent.click(screen.getByRole("button", { name: "Buscar" }));

    const resultLink = await screen.findByRole("link", { name: /Elden Ring/i });
    expect(resultLink).toHaveAttribute("href", "/media/game/119133");
    expect(screen.getByText(/Ano indefinido/)).toBeInTheDocument();

    fake.mode = "empty";
    await userEvent.click(screen.getByRole("button", { name: "Buscar" }));
    expect(await screen.findByText("Nenhuma obra encontrada para esta busca.")).toBeInTheDocument();

    fake.mode = "error";
    await userEvent.click(screen.getByRole("button", { name: "Buscar" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Não foi possível buscar obras no momento.",
    );
  });

  it("auto-searches initial query and resolves SearchPage searchParams", async () => {
    const fake = new FakeSearchFetch();
    const client = new ApiClient("http://localhost:8000", fake.call);

    render(<MediaSearchView apiClient={client} initialCategory="unknown" initialQuery="batman" />);

    await waitFor(() =>
      expect(screen.getByRole("link", { name: /Batman: O Cavaleiro das Trevas/i })).toHaveAttribute(
        "href",
        "/media/movie/tt0468569",
      ),
    );

    const pageEl = await SearchPage({
      searchParams: Promise.resolve({ category: "book", q: "duna" }),
    });
    expect(pageEl).toBeTruthy();

    const defaultPageEl = await SearchPage({ searchParams: Promise.resolve({}) });
    expect(defaultPageEl).toBeTruthy();
  });
});
