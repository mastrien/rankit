import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import HomePage from "@/app/page";

describe("HomePage", () => {
  it("renders welcome hero, primary CTAs, and all five media categories", () => {
    render(<HomePage />);

    expect(screen.getByRole("heading", { name: /Boas-vindas ao Rankit/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Comece já/i })).toHaveAttribute("href", "/register");
    expect(screen.getByRole("link", { name: /Já tenho uma conta/i })).toHaveAttribute(
      "href",
      "/login",
    );

    for (const label of ["Filmes", "Séries", "Animes", "Jogos", "Livros"]) {
      expect(screen.getAllByRole("heading", { name: label }).length).toBeGreaterThanOrEqual(1);
    }
  });
});
