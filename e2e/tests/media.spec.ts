import { expect, test } from "@playwright/test";

test.describe("Media catalog search and cached detail flow", () => {
  test("visitor searches catalog, opens media detail, and reloads PostgreSQL-cached page", async ({
    page,
  }) => {
    await page.goto("/search");
    await expect(page.getByRole("heading", { name: "Explorar catálogo" })).toBeVisible();

    await page.getByRole("button", { name: "Filmes" }).click();
    await page.getByLabel("Buscar obra").fill("Batman");
    await page.getByRole("button", { name: "Buscar" }).click();

    const cardLink = page.getByRole("link", { name: /Batman: O Cavaleiro das Trevas/i });
    await expect(cardLink).toBeVisible();
    await cardLink.click();

    await expect(page).toHaveURL("/media/movie/tt0468569");
    await expect(
      page.getByRole("heading", { name: "Batman: O Cavaleiro das Trevas" }),
    ).toBeVisible();
    await expect(page.getByText(/Coringa em Gotham/i)).toBeVisible();

    await page.reload();
    await expect(
      page.getByRole("heading", { name: "Batman: O Cavaleiro das Trevas" }),
    ).toBeVisible();
  });
});
