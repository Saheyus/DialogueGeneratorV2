/**
 * Tests E2E pour la sélection multi-provider LLM (Story 0.3)
 */
import { test, expect } from '@playwright/test';

test.describe('Multi-Provider LLM Selection', () => {
  test.beforeEach(async ({ page }) => {
    // Naviguer vers l'application
    await page.goto('http://localhost:3000');
    // Attendre que l'application soit chargée
    await page.waitForSelector('[data-testid="generation-panel"], #model-select', { timeout: 10000 });
  });

  test('should display model selector', async ({ page }) => {
    // Vérifier que le sélecteur de modèle est visible
    const modelSelector = page.locator('#model-select');
    await expect(modelSelector).toBeVisible();
  });

  test('should show OpenAI and Mistral providers', async ({ page }) => {
    // Vérifier que les groupes de providers sont présents
    const select = page.locator('#model-select');
    const content = await select.innerHTML();
    
    expect(content).toContain('OpenAI');
    expect(content).toContain('Mistral');
  });

  test('should change model selection', async ({ page }) => {
    // Sélectionner un modèle Mistral
    await page.selectOption('#model-select', 'labs-mistral-small-creative');
    
    // Vérifier que la sélection a changé
    const selectedValue = await page.inputValue('#model-select');
    expect(selectedValue).toBe('labs-mistral-small-creative');
  });

  test('should persist model selection in localStorage', async ({ page }) => {
    // Sélectionner un modèle Mistral
    await page.selectOption('#model-select', 'labs-mistral-small-creative');
    
    // Rafraîchir la page
    await page.reload();
    await page.waitForSelector('#model-select', { timeout: 10000 });
    
    // Vérifier que la sélection est conservée
    const selectedValue = await page.inputValue('#model-select');
    expect(selectedValue).toBe('labs-mistral-small-creative');
  });

  test('should display provider in UI', async ({ page }) => {
    // Sélectionner un modèle Mistral
    await page.selectOption('#model-select', 'labs-mistral-small-creative');
    
    // Vérifier que le provider actuel est affiché
    const providerText = await page.textContent('.model-selector');
    expect(providerText).toContain('Mistral');
  });

  test.skip('should generate dialogue with Mistral (requires API key)', async ({ page }) => {
    // NOTE: Ce test nécessite une clé API Mistral valide et est désactivé par défaut
    
    // Sélectionner Mistral
    await page.selectOption('#model-select', 'labs-mistral-small-creative');
    
    // Remplir le formulaire de génération
    await page.fill('#user-instructions', 'Test generation with Mistral');
    
    // Lancer la génération
    await page.click('button:has-text("Générer")');
    
    // Attendre que la génération commence
    await page.waitForSelector('[data-testid="generation-progress"]', { timeout: 5000 });
    
    // Vérifier que la génération fonctionne (pas d'erreur immédiate)
    const errorMessage = page.locator('.error-message');
    await expect(errorMessage).not.toBeVisible({ timeout: 2000 });
  });

  test.skip('should handle Mistral API error gracefully (requires invalid key)', async ({ page }) => {
    // NOTE: Ce test nécessite une clé API Mistral invalide et est désactivé par défaut
    
    // Sélectionner Mistral
    await page.selectOption('#model-select', 'labs-mistral-small-creative');
    
    // Lancer la génération
    await page.click('button:has-text("Générer")');
    
    // Attendre le message d'erreur
    const errorMessage = page.locator('.error-message');
    await expect(errorMessage).toBeVisible({ timeout: 10000 });
    await expect(errorMessage).toContainText('Mistral API unavailable');
  });
});
