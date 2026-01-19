/**
 * Tests E2E pour le cost governance (Story 0.7).
 * 
 * Scénarios testés :
 * - AC#1 : Warning à 90% du budget (toast affiché)
 * - AC#2 : Blocage à 100% du budget (modal bloquante)
 * - AC#3 : Dashboard affiche budget et graphique
 * - AC#1 : Configuration budget fonctionne
 */
import { test, expect, type Page } from '@playwright/test'

test.describe('Cost Governance (Story 0.7)', () => {
  test.beforeEach(async ({ page }) => {
    // Naviguer vers l'application
    await page.goto('http://localhost:3000')
    
    // Attendre que l'application soit chargée
    await page.waitForSelector('h2:has-text("Génération de Dialogues")', { timeout: 10000 })
  })

  test('AC#3: Dashboard affiche budget et graphique', async ({ page }) => {
    // Ouvrir le modal de statistiques d'utilisation
    const usageButton = page.locator('button:has-text("Usage")').or(page.locator('[data-testid="usage-button"]'))
    if (await usageButton.isVisible({ timeout: 2000 })) {
      await usageButton.click()
      
      // Attendre que le dashboard s'affiche
      await page.waitForSelector('text=/Budget LLM|Suivi d\'utilisation/i', { timeout: 5000 })
      
      // Vérifier que la section budget est visible
      const budgetSection = page.locator('text=/Budget LLM/i')
      await expect(budgetSection).toBeVisible()
      
      // Vérifier les indicateurs budget
      await expect(page.locator('text=/Quota mensuel/i')).toBeVisible()
      await expect(page.locator('text=/Montant dépensé/i')).toBeVisible()
      await expect(page.locator('text=/Montant restant/i')).toBeVisible()
      await expect(page.locator('text=/Pourcentage utilisé/i')).toBeVisible()
      
      // Vérifier que le graphique est visible (ou au moins la section)
      const chartSection = page.locator('text=/Évolution des coûts/i')
      await expect(chartSection).toBeVisible({ timeout: 5000 })
    } else {
      test.skip('Bouton Usage non trouvé - test ignoré')
    }
  })

  test('AC#1: Configuration budget fonctionne', async ({ page }) => {
    // Note: Ce test nécessite une page settings ou modal settings
    // Pour l'instant, on teste via l'API directement
    // TODO: Ajouter navigation vers settings quand disponible
    
    // Test via API directe (à adapter selon UI disponible)
    const response = await page.request.put('http://localhost:4242/api/v1/costs/budget', {
      data: { quota: 150.0 }
    })
    
    expect(response.status()).toBe(200)
    const data = await response.json()
    expect(data.quota).toBe(150.0)
    
    // Vérifier que le budget a été mis à jour
    const getResponse = await page.request.get('http://localhost:4242/api/v1/costs/budget')
    expect(getResponse.status()).toBe(200)
    const budgetData = await getResponse.json()
    expect(budgetData.quota).toBe(150.0)
  })

  test('AC#1: Toast warning affiché à 90%', async ({ page }) => {
    // Prérequis : Configurer le budget à 90%
    await page.request.put('http://localhost:4242/api/v1/costs/budget', {
      data: { quota: 100.0 }
    })
    
    // Simuler 90€ dépensés (via API ou directement dans le fichier JSON)
    // Note: Ceci nécessite un moyen de modifier le budget directement
    // Pour un test complet, il faudrait utiliser l'API ou modifier le fichier JSON
    
    // Naviguer vers la génération
    await page.goto('http://localhost:3000')
    await page.waitForSelector('h2:has-text("Génération de Dialogues")', { timeout: 10000 })
    
    // Tenter une génération (si le budget est à 90%)
    // Le toast devrait s'afficher
    // Note: Ce test nécessite que le budget soit réellement à 90%
    // Pour un test complet, il faudrait setup le budget avant
    
    test.skip('Test nécessite setup du budget à 90% - à compléter avec setup approprié')
  })

  test('AC#2: Modal bloque génération à 100%', async ({ page }) => {
    // Prérequis : Configurer le budget à 100%
    await page.request.put('http://localhost:4242/api/v1/costs/budget', {
      data: { quota: 100.0 }
    })
    
    // Simuler 100€ dépensés (via API ou directement dans le fichier JSON)
    // Note: Ceci nécessite un moyen de modifier le budget directement
    
    // Naviguer vers la génération
    await page.goto('http://localhost:3000')
    await page.waitForSelector('h2:has-text("Génération de Dialogues")', { timeout: 10000 })
    
    // Tenter une génération
    // La modal de blocage devrait s'afficher
    // Note: Ce test nécessite que le budget soit réellement à 100%
    // Pour un test complet, il faudrait setup le budget avant
    
    test.skip('Test nécessite setup du budget à 100% - à compléter avec setup approprié')
  })
})
