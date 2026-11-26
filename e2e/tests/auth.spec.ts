import { expect, test } from "@playwright/test";

test.describe("Authentication flow (HttpOnly JWT cookies)", () => {
  test("user can register, persist session across reload, logout, and login again", async ({
    page,
  }) => {
    const uniqueSuffix = Date.now().toString(36);
    const username = `rankit_${uniqueSuffix}`;
    const displayName = `Rankit User ${uniqueSuffix}`;
    const email = `${username}@example.com`;
    const password = "StrongPassword!2026";

    await page.goto("/register");
    await page.getByLabel("Nome de exibição").fill(displayName);
    await page.getByLabel("Usuário").fill(username);
    await page.getByLabel("E-mail").fill(email);
    await page.getByLabel("Senha", { exact: true }).fill(password);
    await page.getByLabel("Confirmar senha", { exact: true }).fill(password);
    await page.getByRole("button", { name: "Cadastrar" }).click();

    await expect(page).toHaveURL("/");
    await expect(page.getByRole("link", { name: displayName })).toBeVisible();

    await page.reload();
    await expect(page.getByRole("link", { name: displayName })).toBeVisible();

    await page.getByRole("button", { name: "Sair" }).click();
    await expect(page.getByRole("link", { name: "Entrar" })).toBeVisible();

    await page.goto("/login");
    await page.getByLabel("Usuário").fill(username);
    await page.getByLabel("Senha").fill(password);
    await page.getByRole("button", { name: "Entrar" }).click();

    await expect(page).toHaveURL("/");
    await expect(page.getByRole("link", { name: displayName })).toBeVisible();
  });
});
