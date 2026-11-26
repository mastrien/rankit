import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Footer } from "@/components/layout/Footer";
import { Navbar } from "@/components/layout/Navbar";

describe("Navigation layout components", () => {
  it("renders Rankit logo and auth navigation links in Navbar", () => {
    render(<Navbar />);

    expect(screen.getByRole("img", { name: "Rankit" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Início" })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: "Entrar" })).toHaveAttribute("href", "/login");
    expect(screen.getByRole("link", { name: "Cadastro" })).toHaveAttribute("href", "/register");
  });

  it("renders Footer summary and navigation links", () => {
    render(<Footer />);

    expect(
      screen.getByText(/Avalie filmes, séries, animes, jogos e livros em um só lugar/i),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Login" })).toHaveAttribute("href", "/login");
    expect(screen.getByRole("link", { name: "Cadastro" })).toHaveAttribute("href", "/register");
  });
});
