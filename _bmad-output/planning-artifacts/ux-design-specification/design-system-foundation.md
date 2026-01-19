# Design System Foundation

## 1.1 Design System Choice

**Custom Design System** - Système de design personnalisé déjà en place, à structurer et documenter davantage.

## Rationale for Selection

**1. Cohérence avec l'existant**
   - Le système de thème custom (`theme.ts`) est déjà fonctionnel et aligné avec l'identité visuelle actuelle
   - Les composants custom (ResizablePanels, Tabs, etc.) sont intégrés dans le workflow
   - Migration vers une bibliothèque externe nécessiterait une refonte majeure, incompatible avec l'approche brownfield

**2. Contrôle total sur l'expérience**
   - Adaptation fine aux contraintes spécifiques (graphes complexes, espace limité, mode sombre)
   - Personnalisation complète des composants pour les besoins uniques (barre 4 résultats, nodes ReactFlow custom)
   - Pas de dépendance à des patterns externes qui pourraient limiter la flexibilité

**3. Itération progressive**
   - Approche brownfield : améliorer l'existant sans casser le workflow
   - Structuration progressive des design tokens et composants
   - Pas de migration risquée, évolution continue

**4. Équipe et maintenance**
   - Petite équipe (Marc + Mathieu) : maintenance maîtrisable d'un système custom
   - Besoin de différenciation : outil spécialisé nécessite une identité visuelle unique
   - Pas de contrainte de vitesse de développement (timeline itérative)

## Implementation Approach

**Phase 1 : Structuration des Design Tokens**

1. **Organisation du fichier `theme.ts`**
   - Séparer les tokens par catégories (couleurs, espacements, typographie, ombres, animations)
   - Créer des tokens sémantiques (primary, secondary, error, success) plutôt que des valeurs brutes
   - Documenter chaque token avec son usage et ses variantes

2. **Extension des tokens existants**
   - Ajouter tokens pour espacements (spacing scale : 4px, 8px, 12px, 16px, 24px, 32px, 48px)
   - Définir typographie (font families, sizes, weights, line heights)
   - Ajouter tokens pour animations (durations, easings)
   - Tokens pour z-index (layers : modal, dropdown, tooltip, base)

3. **Mode sombre comme base**
   - Le thème actuel est optimisé pour le mode sombre (fond #1a1a1a)
   - Conserver cette approche, pas besoin de mode clair pour l'instant
   - Tokens de couleur avec variantes (hover, active, disabled)

**Phase 2 : Bibliothèque de Composants Réutilisables**

1. **Composants de base**
   - Button (variants : default, primary, secondary, danger)
   - Input (text, textarea, select, checkbox, radio)
   - Modal / Dialog (pour génération, confirmations)
   - Tooltip (pour infobulles barre 4 résultats)
   - Toast / Notification (feedback actions)

2. **Composants layout**
   - ResizablePanels (déjà existant, documenter)
   - Tabs (déjà existant, documenter)
   - Card / Panel (conteneurs avec header, body, footer)
   - Divider / Separator

3. **Composants spécialisés**
   - GraphNode (DialogueNode, TestNode, EndNode) - déjà custom pour ReactFlow
   - Barre 4 résultats (hub visuel custom)
   - ContextSelector (sélecteur de contexte)
   - NodeEditorPanel (panel d'édition contextuel)

**Phase 3 : Documentation et Guidelines**

1. **Style Guide**
   - Documenter les patterns de couleur (usage, contrastes, accessibilité)
   - Guidelines d'espacement (marges, paddings, gaps)
   - Typographie (hiérarchie, lisibilité)

2. **Component Library**
   - Storybook ou documentation markdown pour chaque composant
   - Exemples d'usage, props, variantes
   - Do's and Don'ts pour chaque composant

3. **Design Patterns**
   - Patterns d'interaction (hover, selection, focus)
   - Patterns de feedback (loading, success, error)
   - Patterns de navigation (breadcrumbs, tabs, panels)

## Customization Strategy

**1. Design Tokens comme source de vérité**
   - Tous les styles dérivent des tokens (pas de valeurs hardcodées)
   - Tokens accessibles via `theme` object (déjà en place)
   - Facilite les changements globaux (ex: ajuster toutes les couleurs primaires)

**2. Composants comme briques réutilisables**
   - Composants de base pour 80% des cas d'usage
   - Composants spécialisés pour les 20% (graphe, génération IA)
   - Props cohérentes entre composants similaires

**3. Extension progressive**
   - Ajouter de nouveaux tokens/composants au besoin
   - Pas de sur-engineering : créer seulement ce qui est nécessaire
   - Itérer basé sur les besoins réels (stories, feedback utilisateurs)

**4. Intégration avec ReactFlow**
   - ReactFlow a son propre système de styling (nodes, edges, controls)
   - Adapter les tokens du design system pour ReactFlow (couleurs, espacements)
   - Nodes custom utilisent les tokens du design system (couleurs, typographie)

**5. Accessibilité**
   - Contraste suffisant (WCAG AA minimum)
   - Focus visible (outline avec `theme.border.focus`)
   - Navigation clavier (déjà en place via `useKeyboardShortcuts`)
   - Labels ARIA pour composants interactifs
