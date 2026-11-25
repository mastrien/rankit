import { expect, test } from "@playwright/test";

const API_URL = process.env.E2E_API_URL ?? "http://localhost:8000";

test.describe("Rankit smoke & readiness", () => {
  test("home page renders Rankit hero and navigation links", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("heading", { name: /Boas-vindas ao Rankit/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /Comece já/i })).toBeVisible();
    await expect(page.getByRole("link", { name: "Entrar" })).toBeVisible();
    for (const label of ["Filmes", "Séries", "Animes", "Jogos", "Livros"]) {
      await expect(page.getByRole("heading", { name: label }).first()).toBeVisible();
    }
  });

  test("backend health endpoint confirms PostgreSQL readiness", async ({ request }) => {
    const response = await request.get(`${API_URL}/api/v1/health/`);

    expect(response.status()).toBe(200);
    await expect(response.json()).resolves.toEqual({
      status: "ok",
      database: "ok",
    });
  });
});
