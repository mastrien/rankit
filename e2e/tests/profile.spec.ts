import { expect, test } from "@playwright/test";

test.describe("User profiles, customization, and follow graph", () => {
  test("user edits profile and another user follows and unfollows", async ({ browser }) => {
    const suffix = Date.now().toString(36);
    const userA = `alice_${suffix}`;
    const userB = `bob_${suffix}`;
    const password = "StrongPassword!2026";

    const contextA = await browser.newContext();
    const pageA = await contextA.newPage();

    await pageA.goto("/register");
    await pageA.getByLabel("Nome de exibição").fill("Alice Original");
    await pageA.getByLabel("Usuário").fill(userA);
    await pageA.getByLabel("E-mail").fill(`${userA}@example.com`);
    await pageA.getByLabel("Senha", { exact: true }).fill(password);
    await pageA.getByLabel("Confirmar senha", { exact: true }).fill(password);
    await pageA.getByRole("button", { name: "Cadastrar" }).click();
    await expect(pageA).toHaveURL("/");

    await pageA.getByRole("link", { name: "Alice Original" }).click();
    await expect(pageA).toHaveURL(`/profile/${userA}`);

    await pageA.getByRole("link", { name: "Editar perfil" }).click();
    await expect(pageA).toHaveURL("/profile/edit");

    const nameInput = pageA.getByLabel("Nome de exibição");
    await nameInput.fill("Alice Atualizada");
    await pageA.getByLabel(/Biografia/i).fill("Fã de cinema e RPGs.");
    await pageA.getByRole("button", { name: "Ícone 5" }).click();
    await pageA.getByRole("button", { name: "Banner 3" }).click();
    await pageA.getByRole("button", { name: "Salvar alterações" }).click();

    await expect(pageA).toHaveURL(`/profile/${userA}`);
    await expect(pageA.getByRole("heading", { name: "Alice Atualizada" })).toBeVisible();
    await expect(pageA.getByText("Fã de cinema e RPGs.")).toBeVisible();
    await contextA.close();

    const contextB = await browser.newContext();
    const pageB = await contextB.newPage();

    await pageB.goto("/register");
    await pageB.getByLabel("Nome de exibição").fill("Bob Viewer");
    await pageB.getByLabel("Usuário").fill(userB);
    await pageB.getByLabel("E-mail").fill(`${userB}@example.com`);
    await pageB.getByLabel("Senha", { exact: true }).fill(password);
    await pageB.getByLabel("Confirmar senha", { exact: true }).fill(password);
    await pageB.getByRole("button", { name: "Cadastrar" }).click();
    await expect(pageB).toHaveURL("/");

    await pageB.goto(`/profile/${userA}`);
    await expect(pageB.getByRole("heading", { name: "Alice Atualizada" })).toBeVisible();
    await pageB.getByRole("button", { name: "Seguir" }).click();

    await expect(pageB.getByRole("button", { name: "Seguindo", exact: true })).toBeVisible();
    await expect(pageB.getByRole("button", { name: /1\s*Seguidores/i })).toBeVisible();

    await pageB.reload();
    await expect(pageB.getByRole("button", { name: "Seguindo", exact: true })).toBeVisible();
    await expect(pageB.getByRole("button", { name: /1\s*Seguidores/i })).toBeVisible();

    await pageB.getByRole("button", { name: "Seguindo", exact: true }).click();
    await expect(pageB.getByRole("button", { name: "Seguir", exact: true })).toBeVisible();
    await expect(pageB.getByRole("button", { name: /0\s*Seguidores/i })).toBeVisible();

    await contextB.close();
  });
});
