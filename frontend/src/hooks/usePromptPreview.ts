/**
 * Hook personnalisé pour formater et afficher le prompt.
 */
import { useMemo } from 'react'
import { hasJsonContent } from '../utils/jsonPrettifier'
import { estimateTokens } from '../utils/tokenEstimation'

export interface PromptSection {
  title: string
  content: string
  hasJson: boolean
  tokenCount?: number
  children?: PromptSection[]  // Sous-sections imbriquées
}

/**
 * Sections de niveau 2 (catégories) : CHARACTERS, LOCATIONS, ITEMS, SPECIES, COMMUNITIES, etc.
 * Ces sections marquent le début d'un nouvel élément dans la catégorie
 */
const LEVEL_2_CATEGORIES = [
  'CHARACTERS', 'PERSONNAGES',
  'LOCATIONS', 'LIEUX',
  'ITEMS', 'OBJETS',
  'SPECIES', 'ESPÈCES', 'ESPECES',
  'COMMUNITIES', 'COMMUNAUTÉS', 'COMMUNAUTES',
  'QUESTS', 'QUÊTES', 'QUETES',
]

/**
 * Mapping des catégories vers leurs noms d'éléments individuels
 */
const CATEGORY_TO_ITEM_NAME: Record<string, string> = {
  'CHARACTERS': 'CHARACTER',
  'PERSONNAGES': 'CHARACTER',
  'LOCATIONS': 'LOCATION',
  'LIEUX': 'LOCATION',
  'ITEMS': 'ITEM',
  'OBJETS': 'ITEM',
  'SPECIES': 'SPECIES',
  'ESPÈCES': 'SPECIES',
  'ESPECES': 'SPECIES',
  'COMMUNITIES': 'COMMUNITY',
  'COMMUNAUTÉS': 'COMMUNITY',
  'COMMUNAUTES': 'COMMUNITY',
  'QUESTS': 'QUEST',
  'QUÊTES': 'QUEST',
  'QUETES': 'QUEST',
}

/**
 * Sections de niveau 3 (sections d'éléments) : IDENTITÉ, CARACTÉRISATION, etc.
 * Ces sections sont regroupées sous les éléments individuels
 */
const LEVEL_3_SECTIONS = [
  'IDENTITÉ', 'IDENTITE',
  'CARACTÉRISATION', 'CARACTERISATION',
  'VOIX ET STYLE',
  'HISTOIRE ET RELATIONS',
  'MÉCANIQUES', 'MECANIQUES',
  'AUTRES INFORMATIONS',
  'INTRODUCTION',
]

/**
 * Vérifie si une section est une catégorie de niveau 2
 */
function isLevel2Category(title: string): boolean {
  const upperTitle = title.toUpperCase()
  return LEVEL_2_CATEGORIES.some(cat => upperTitle === cat.toUpperCase())
}

/**
 * Vérifie si une section est une section de niveau 3
 */
function isLevel3Section(title: string): boolean {
  const upperTitle = title.toUpperCase()
  return LEVEL_3_SECTIONS.some(sec => upperTitle === sec.toUpperCase())
}

/**
 * Obtient le nom d'élément individuel pour une catégorie
 */
function getItemNameForCategory(categoryTitle: string): string {
  const upperTitle = categoryTitle.toUpperCase()
  for (const [cat, itemName] of Object.entries(CATEGORY_TO_ITEM_NAME)) {
    if (upperTitle === cat.toUpperCase()) {
      return itemName
    }
  }
  return categoryTitle // Fallback
}

/**
 * Parse récursivement les sous-sections dans un contenu (sections de niveau 2+).
 * Détecte les sections au format --- TITRE --- et crée une hiérarchie :
 * - Niveau 2 : Catégories (CHARACTERS, LOCATIONS, etc.)
 * - Niveau 3 : Sections d'éléments (IDENTITÉ, CARACTÉRISATION, etc.) regroupées sous les catégories
 */
function parseSubSections(content: string): { children: PromptSection[], remainingContent: string } {
  const children: PromptSection[] = []
  const subSectionRegex = /^--- (.+?) ---$/gm
  
  // Trouver toutes les positions des sous-sections
  const subSectionMatches: Array<{ index: number; title: string; isLevel2: boolean }> = []
  let match
  while ((match = subSectionRegex.exec(content)) !== null) {
    const title = match[1].trim()
    if (title) {
      subSectionMatches.push({
        index: match.index,
        title,
        isLevel2: isLevel2Category(title),
      })
    }
  }
  
  if (subSectionMatches.length === 0) {
    // Pas de sous-sections, retourner le contenu tel quel
    return { children: [], remainingContent: content }
  }
  
  // Grouper les éléments individuels par catégorie
  // Structure réelle : un seul marqueur "CHARACTERS" puis tous les personnages avec leurs sections
  let i = 0
  while (i < subSectionMatches.length) {
    const currentSection = subSectionMatches[i]
    
    if (currentSection.isLevel2) {
      // Section de niveau 2 (marqueur de catégorie) : trouver toutes les sections de niveau 3 qui suivent
      const categoryTitle = currentSection.title
      const itemName = getItemNameForCategory(categoryTitle)
      
      // Trouver où se termine cette catégorie (prochaine catégorie ou fin du contenu)
      let categoryEnd = content.length
      let j = i + 1
      while (j < subSectionMatches.length) {
        if (subSectionMatches[j].isLevel2) {
          categoryEnd = subSectionMatches[j].index
          break
        }
        j++
      }
      
      // Extraire le contenu de la catégorie
      const categoryStart = currentSection.index
      const categoryHeaderMatch = content.substring(categoryStart).match(/^--- (.+?) ---\s*\n?/m)
      if (!categoryHeaderMatch) {
        i++
        continue
      }
      
      const categoryContentStart = categoryStart + categoryHeaderMatch[0].length
      const categoryContent = content.substring(categoryContentStart, categoryEnd).trim()
      
      // Extraire toutes les sections de niveau 3 dans cette catégorie
      const level3Matches: Array<{ index: number; title: string }> = []
      let level3Match
      const level3Regex = /^--- (.+?) ---$/gm
      while ((level3Match = level3Regex.exec(categoryContent)) !== null) {
        const level3Title = level3Match[1].trim()
        if (level3Title && !isLevel2Category(level3Title)) {
          level3Matches.push({
            index: level3Match.index,
            title: level3Title,
          })
        }
      }
      
      if (level3Matches.length === 0) {
        // Pas de sections de niveau 3, passer à la suite
        i = j
        continue
      }
      
      // Grouper les sections de niveau 3 par élément individuel
      // Un nouvel élément commence quand on voit une section IDENTITÉ après avoir vu d'autres sections
      // ou quand on voit une section IDENTITÉ et qu'on a déjà un élément en cours avec des sections non-IDENTITÉ
      const items: Array<{ sections: PromptSection[] }> = []
      let currentItemSections: PromptSection[] = []
      
      for (let k = 0; k < level3Matches.length; k++) {
        const level3Match = level3Matches[k]
        const isIdentity = level3Match.title.toUpperCase() === 'IDENTITÉ' || level3Match.title.toUpperCase() === 'IDENTITE'
        
        // Si on voit IDENTITÉ et qu'on a déjà un élément en cours avec des sections, c'est un nouvel élément
        if (isIdentity && currentItemSections.length > 0) {
          // Vérifier si l'élément en cours contient des sections autres que IDENTITÉ
          const hasNonIdentitySections = currentItemSections.some(sec => {
            const secTitle = sec.title.toUpperCase()
            return secTitle !== 'IDENTITÉ' && secTitle !== 'IDENTITE'
          })
          
          if (hasNonIdentitySections) {
            // Finaliser l'élément précédent
            items.push({
              sections: [...currentItemSections],
            })
            
            // Commencer un nouvel élément
            currentItemSections = []
          }
        }
        
        // Extraire le contenu de cette section
        const level3Start = level3Match.index
        const level3End = k < level3Matches.length - 1 
          ? level3Matches[k + 1].index 
          : categoryContent.length
        
        const level3HeaderMatch = categoryContent.substring(level3Start).match(/^--- (.+?) ---\s*\n?/m)
        if (level3HeaderMatch) {
          const level3ContentStart = level3Start + level3HeaderMatch[0].length
          const level3Content = categoryContent.substring(level3ContentStart, level3End).trim()
          
          if (level3Content) {
            const level3TokenCount = estimateTokens(level3Content)
            currentItemSections.push({
              title: level3Match.title,
              content: level3Content,
              hasJson: hasJsonContent(level3Content),
              tokenCount: level3TokenCount,
            })
          }
        }
      }
      
      // Ajouter le dernier élément
      if (currentItemSections.length > 0) {
        items.push({
          sections: currentItemSections,
        })
      }
      
      // Si il n'y a qu'un seul élément, afficher directement ses sections sans wrapper
      if (items.length === 1) {
        children.push(...items[0].sections)
      } else if (items.length > 1) {
        // Plusieurs éléments : créer des sections "CHARACTER 1", "CHARACTER 2", etc.
        items.forEach((item, idx) => {
          const itemTokenCount = item.sections.reduce((sum, sec) => sum + (sec.tokenCount || 0), 0)
          children.push({
            title: `${itemName} ${idx + 1}`,
            content: '',
            hasJson: false,
            tokenCount: itemTokenCount,
            children: item.sections.length > 0 ? item.sections : undefined,
          })
        })
      }
      
      // Passer à la prochaine catégorie
      i = j
    } else {
      // Section de niveau 3 (ou autre) : traiter normalement (récursif pour les niveaux plus profonds)
      const sectionStart = currentSection.index
      const sectionEnd = i < subSectionMatches.length - 1 
        ? subSectionMatches[i + 1].index 
        : content.length
      
      // Extraire le contenu de la sous-section (après le marqueur)
      const sectionHeaderMatch = content.substring(sectionStart).match(/^--- (.+?) ---\s*\n?/m)
      if (sectionHeaderMatch) {
        const contentStart = sectionStart + sectionHeaderMatch[0].length
        const subContent = content.substring(contentStart, sectionEnd).trim()
        
        if (subContent) {
          // Parser récursivement les sous-sections de niveau inférieur (niveau 4+)
          const { children: grandChildren, remainingContent: finalContent } = parseSubSections(subContent)
          
          // Calculer le token count récursivement
          const childrenTokenCount = grandChildren.reduce((sum, child) => sum + (child.tokenCount || 0), 0)
          const contentTokenCount = estimateTokens(finalContent)
          const totalTokenCount = childrenTokenCount + contentTokenCount
          
          children.push({
            title: currentSection.title,
            content: finalContent,
            hasJson: hasJsonContent(finalContent),
            tokenCount: totalTokenCount,
            children: grandChildren.length > 0 ? grandChildren : undefined,
          })
        }
      }
      
      i++
    }
  }
  
  // Construire le contenu restant (avant la première sous-section)
  const firstSubSectionIndex = subSectionMatches[0].index
  const remainingContent = content.substring(0, firstSubSectionIndex).trim()
  
  return { children, remainingContent }
}

/**
 * Parse le prompt en sections délimitées par --- SECTION --- ou ### SECTION X.
 * Supporte l'imbrication multi-niveaux.
 */
export function parsePromptSections(prompt: string): PromptSection[] {
  if (!prompt) return []
  
  const sections: PromptSection[] = []
  // D'abord, détecter UNIQUEMENT les sections principales (### SECTION X)
  // Les sous-sections (--- TITRE ---) seront parsées récursivement dans le contenu
  const mainSectionRegex = /^### (SECTION \d+[A-Z]?\. .+?)$/gm
  
  // Trouver toutes les positions des sections principales
  const sectionMatches: Array<{ index: number; title: string }> = []
  let match
  while ((match = mainSectionRegex.exec(prompt)) !== null) {
    const title = match[1].trim()
    if (title) {
      sectionMatches.push({
        index: match.index,
        title,
      })
    }
  }
  
  // Si aucune section principale n'est trouvée, essayer le format alternatif --- SECTION ---
  if (sectionMatches.length === 0) {
    const altSectionRegex = /^--- (.+?) ---$/gm
    while ((match = altSectionRegex.exec(prompt)) !== null) {
      const title = match[1].trim()
      if (title && title.startsWith('SECTION')) {
        sectionMatches.push({
          index: match.index,
          title,
        })
      }
    }
  }
  // #region agent log
  fetch('http://127.0.0.1:7244/ingest/49f0dd36-7e15-4023-914a-f038d74c10fc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sessionId:'debug-session',runId:'run1',hypothesisId:'C',location:'frontend/src/hooks/usePromptPreview.ts:32',message:'Section regex matches',data:{total_matches:sectionMatches.length,matches:sectionMatches.map(m => ({index:m.index,title:m.title})),has_competences:sectionMatches.some(m => m.title.includes('COMPÉTENCES')),has_traits:sectionMatches.some(m => m.title.includes('TRAITS')),prompt_preview:prompt.substring(0,500)},timestamp:Date.now()})}).catch(()=>{});
  // #endregion
  
  if (sectionMatches.length === 0) {
    // Pas de sections, tout le contenu est une seule section "System Prompt"
    const trimmedPrompt = prompt.trim()
    return [{
      title: 'System Prompt',
      content: trimmedPrompt,
      hasJson: hasJsonContent(trimmedPrompt),
      tokenCount: estimateTokens(trimmedPrompt),
    }]
  }
  
  // Extraire le contenu avant la première section (System Prompt)
  if (sectionMatches[0].index > 0) {
    const systemPromptContent = prompt.substring(0, sectionMatches[0].index).trim()
    // #region agent log
    fetch('http://127.0.0.1:7244/ingest/49f0dd36-7e15-4023-914a-f038d74c10fc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sessionId:'debug-session',runId:'run1',hypothesisId:'B',location:'frontend/src/hooks/usePromptPreview.ts:54',message:'Extracting System Prompt content',data:{section0_index:sectionMatches[0].index,systemPromptContentLength:systemPromptContent.length,systemPromptContentPreview:systemPromptContent.substring(0,200),hasVocabInSystemPrompt:systemPromptContent.includes('[VOCABULAIRE ALTEIR]')},timestamp:Date.now()})}).catch(()=>{});
    // #endregion
    if (systemPromptContent) {
      sections.push({
        title: 'System Prompt',
        content: systemPromptContent,
        hasJson: hasJsonContent(systemPromptContent),
        tokenCount: estimateTokens(systemPromptContent),
      })
    }
  }
  
  // Extraire chaque section avec parsing récursif des sous-sections
  for (let i = 0; i < sectionMatches.length; i++) {
    const sectionStart = sectionMatches[i].index
    const sectionEnd = i < sectionMatches.length - 1 
      ? sectionMatches[i + 1].index 
      : prompt.length
    
    // Extraire le contenu de la section (après le marqueur)
    // Support pour les deux formats : --- SECTION --- et ### SECTION X. TITRE (avec support pour 2A, 2B, 2C)
    const sectionHeaderMatch = prompt.substring(sectionStart).match(/^(?:--- (.+?) ---|### (SECTION \d+[A-Z]?\. .+?))\s*\n?/m)
    if (sectionHeaderMatch) {
      const contentStart = sectionStart + sectionHeaderMatch[0].length
      const rawContent = prompt.substring(contentStart, sectionEnd).trim()
      // #region agent log
      const isCompetences = sectionMatches[i].title.includes('COMPÉTENCES'); const isTraits = sectionMatches[i].title.includes('TRAITS'); if (isCompetences || isTraits) { fetch('http://127.0.0.1:7244/ingest/49f0dd36-7e15-4023-914a-f038d74c10fc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sessionId:'debug-session',runId:'run1',hypothesisId:isCompetences?'B':'B',location:'frontend/src/hooks/usePromptPreview.ts:69',message:isCompetences?'Competences content extracted':'Traits content extracted',data:{title:sectionMatches[i].title,contentLength:rawContent.length,contentIsEmpty:!rawContent,contentPreview:rawContent.substring(0,100),sectionStart,sectionEnd,contentStart},timestamp:Date.now()})}).catch(()=>{}); }
      // #endregion
      
      if (rawContent) {
        // Parser récursivement les sous-sections
        const { children, remainingContent } = parseSubSections(rawContent)
        
        // Calculer le token count récursivement
        const childrenTokenCount = children.reduce((sum, child) => sum + (child.tokenCount || 0), 0)
        const contentTokenCount = estimateTokens(remainingContent)
        const totalTokenCount = childrenTokenCount + contentTokenCount
        
        sections.push({
          title: sectionMatches[i].title,
          content: remainingContent,
          hasJson: hasJsonContent(remainingContent),
          tokenCount: totalTokenCount,
          children: children.length > 0 ? children : undefined,
        })
        // #region agent log
        if (isCompetences || isTraits) { fetch('http://127.0.0.1:7244/ingest/49f0dd36-7e15-4023-914a-f038d74c10fc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sessionId:'debug-session',runId:'run1',hypothesisId:isCompetences?'B':'B',location:'frontend/src/hooks/usePromptPreview.ts:78',message:isCompetences?'Competences section added':'Traits section added',data:{title:sectionMatches[i].title,totalSections:sections.length},timestamp:Date.now()})}).catch(()=>{}); }
        // #endregion
      } else {
        // #region agent log
        if (isCompetences || isTraits) { fetch('http://127.0.0.1:7244/ingest/49f0dd36-7e15-4023-914a-f038d74c10fc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sessionId:'debug-session',runId:'run1',hypothesisId:'B',location:'frontend/src/hooks/usePromptPreview.ts:81',message:isCompetences?'Competences section REJECTED (empty content)':'Traits section REJECTED (empty content)',data:{title:sectionMatches[i].title,rawContentLength:prompt.substring(contentStart,sectionEnd).length},timestamp:Date.now()})}).catch(()=>{}); }
        // #endregion
      }
    }
  }
  
  return sections
}

export function usePromptPreview(promptText: string | null | undefined) {
  const formattedPrompt = useMemo(() => {
    if (!promptText) return ''
    // Pour l'instant, on retourne le texte tel quel
    // On pourrait ajouter de la coloration syntaxique ou du formatage ici
    return promptText
  }, [promptText])
  
  const sections = useMemo(() => {
    if (!promptText) return []
    return parsePromptSections(promptText)
  }, [promptText])

  return {
    formattedPrompt,
    sections,
    isEmpty: !promptText || promptText.trim().length === 0,
  }
}



