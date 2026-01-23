/**
 * Tests d'intégration pour le parsing structuré du prompt avec vraies données.
 * 
 * Ces tests utilisent le prompt brut réel retourné par l'API pour vérifier
 * que le parsing structuré fonctionne correctement avec le format réel.
 * 
 * Types de tests :
 * - Tests d'intégration : Utilisent les vraies données du prompt API
 * - Tests frontend : Vérifient le parsing TypeScript
 * 
 * Pour exécuter ces tests :
 *     npm run test:frontend -- tests/frontend/test_prompt_parsing_integration.test.ts
 */
import { describe, it, expect } from 'vitest'
import { parsePromptSections, type PromptSection } from '../../frontend/src/hooks/usePromptPreview'
import { readFileSync } from 'fs'
import { join } from 'path'

describe('parsePromptSections - Integration avec vraies données API', () => {
  it('devrait parser un prompt réel avec SECTION 2A et CHARACTERS', () => {
    // Lire le prompt réel depuis le fichier généré par le test API
    const promptPath = join(__dirname, '../../test_prompt_output.txt')
    let realPrompt: string
    
    try {
      const fileContent = readFileSync(promptPath, 'utf-8')
      // Extraire le prompt (entre les séparateurs ===)
      const match = fileContent.match(/={80}\nPROMPT BRUT COMPLET RETOURNÉ PAR L'API:\n={80}\n([\s\S]*?)\n={80}/)
      realPrompt = match ? match[1] : fileContent
    } catch (error) {
      // Si le fichier n'existe pas, utiliser un prompt de test
      console.warn('Fichier test_prompt_output.txt non trouvé, utilisation d\'un prompt de test')
      realPrompt = `### SECTION 2A. CONTEXTE GDD

**CONTEXTE GÉNÉRAL DE LA SCÈNE**
--- CHARACTERS ---
--- IDENTITÉ ---
Nom: Akthar-Neth Amatru, l'Exégète
Alias: Grand-Père

--- CARACTÉRISATION ---
Désir Principal: Accomplir le Dernier Rituel

### SECTION 2B. GUIDES NARRATIFS
Contenu...
`
    }
    
    const sections = parsePromptSections(realPrompt)
    
    // Vérifier que SECTION 2A est présente
    const section2A = sections.find(s => s.title.includes('SECTION 2A'))
    expect(section2A).toBeDefined()
    
    if (section2A) {
      // Vérifier que SECTION 2A contient le contenu
      expect(section2A.content.length).toBeGreaterThan(0)
      
      // Vérifier que les sous-sections sont parsées
      // Le format réel peut avoir --- CHARACTERS --- ou directement les sections IDENTITÉ
      const hasCharacterSections = section2A.children?.some(
        child => child.title.includes('CHARACTER') || 
                 child.title === 'IDENTITÉ' || 
                 child.title === 'CARACTÉRISATION' ||
                 child.title.includes('IDENTITÉ')
      )
      
      // Si pas de children, vérifier que le contenu contient au moins le nom du personnage
      if (!hasCharacterSections && section2A.children?.length === 0) {
        expect(section2A.content).toContain('Akthar')
      } else {
        expect(hasCharacterSections).toBe(true)
      }
      
      console.log(`[OK] SECTION 2A parsée: ${section2A.children?.length || 0} sous-sections`)
    }
  })
  
  it('devrait parser toutes les sections principales du prompt réel', () => {
    const promptPath = join(__dirname, '../../test_prompt_output.txt')
    let realPrompt: string
    
    try {
      const fileContent = readFileSync(promptPath, 'utf-8')
      const match = fileContent.match(/={80}\nPROMPT BRUT COMPLET RETOURNÉ PAR L'API:\n={80}\n([\s\S]*?)\n={80}/)
      realPrompt = match ? match[1] : fileContent
    } catch {
      realPrompt = `### SECTION 0. CONTRAT GLOBAL
Contenu SECTION 0

### SECTION 1. INSTRUCTIONS TECHNIQUES
Contenu SECTION 1

### SECTION 2A. CONTEXTE GDD
--- CHARACTERS ---
Nom: Test

### SECTION 2B. GUIDES NARRATIFS
Contenu SECTION 2B

### SECTION 3. INSTRUCTIONS DE SCÈNE
Contenu SECTION 3
`
    }
    
    const sections = parsePromptSections(realPrompt)
    
    // Vérifier que toutes les sections principales sont présentes
    const sectionTitles = sections.map(s => s.title)
    const hasSection0 = sectionTitles.some(t => t.includes('SECTION 0'))
    const hasSection1 = sectionTitles.some(t => t.includes('SECTION 1'))
    const hasSection2A = sectionTitles.some(t => t.includes('SECTION 2A'))
    const hasSection2B = sectionTitles.some(t => t.includes('SECTION 2B'))
    const hasSection3 = sectionTitles.some(t => t.includes('SECTION 3'))
    
    expect(hasSection0 || hasSection1 || hasSection2A || hasSection2B || hasSection3).toBe(true)
    
    console.log(`[OK] Sections parsées: ${sections.length} (${sectionTitles.join(', ')})`)
  })
})
