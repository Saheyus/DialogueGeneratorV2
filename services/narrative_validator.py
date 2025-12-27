"""Service pour valider la qualité narrative des dialogues générés."""
import logging
from typing import List, Dict, Any, Optional
from collections import Counter
import re

from models.dialogue_structure.interaction import Interaction
from models.dialogue_structure.dialogue_elements import DialogueLineElement

logger = logging.getLogger(__name__)


class NarrativeValidator:
    """Valide la qualité narrative des dialogues générés."""
    
    # Seuils de validation
    MIN_LINE_LENGTH_WORDS = 10  # Minimum de mots par réplique
    MAX_LINE_LENGTH_WORDS = 50  # Maximum de mots par réplique
    REPETITION_THRESHOLD = 3  # Nombre de répétitions d'un mot pour alerter
    
    def __init__(self):
        """Initialise le validateur."""
        pass
    
    def validate_interaction(
        self,
        interaction: Interaction,
        context: Optional[str] = None,
        vocabulary_terms: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """Valide une interaction complète et retourne une liste de warnings.
        
        Args:
            interaction: L'interaction à valider.
            context: Le contexte GDD utilisé (optionnel, pour vérifier l'utilisation des données de voix).
            vocabulary_terms: Liste des termes du vocabulaire Alteir (optionnel, pour validation vocabulaire).
            
        Returns:
            Liste de messages d'avertissement (vide si tout est OK).
        """
        warnings: List[str] = []
        
        # Valider chaque ligne de dialogue
        for element in interaction.elements:
            if isinstance(element, DialogueLineElement):
                line_warnings = self.validate_line_length(element.text)
                warnings.extend(line_warnings)
        
        # Détecter les répétitions dans l'interaction
        repetition_warnings = self.detect_repetitions(interaction)
        warnings.extend(repetition_warnings)
        
        # Vérifier l'utilisation de la caractérisation si le contexte est fourni
        if context:
            characterization_warnings = self.check_characterization_usage(interaction, context)
            warnings.extend(characterization_warnings)
        
        # Valider l'utilisation du vocabulaire si fourni
        if vocabulary_terms:
            vocab_warnings = self.validate_vocabulary_usage(interaction, vocabulary_terms)
            warnings.extend(vocab_warnings)
        
        return warnings
    
    def validate_line_length(self, replique: str) -> List[str]:
        """Valide la longueur d'une réplique.
        
        Args:
            replique: Le texte de la réplique.
            
        Returns:
            Liste de warnings (vide si la longueur est appropriée).
        """
        warnings: List[str] = []
        words = replique.split()
        word_count = len(words)
        
        if word_count < self.MIN_LINE_LENGTH_WORDS:
            warnings.append(
                f"Réplique très courte ({word_count} mots) : '{replique[:50]}...' "
                f"(minimum recommandé: {self.MIN_LINE_LENGTH_WORDS} mots)"
            )
        elif word_count > self.MAX_LINE_LENGTH_WORDS:
            warnings.append(
                f"Réplique très longue ({word_count} mots) : '{replique[:50]}...' "
                f"(maximum recommandé: {self.MAX_LINE_LENGTH_WORDS} mots)"
            )
        
        return warnings
    
    def detect_repetitions(self, interaction: Interaction) -> List[str]:
        """Détecte les répétitions de mots ou phrases dans une interaction.
        
        Args:
            interaction: L'interaction à analyser.
            
        Returns:
            Liste de warnings pour les répétitions détectées.
        """
        warnings: List[str] = []
        
        # Collecter tous les mots (minuscules, sans ponctuation)
        all_words: List[str] = []
        all_phrases: List[str] = []
        
        for element in interaction.elements:
            if isinstance(element, DialogueLineElement):
                text = element.text.lower()
                # Extraire les mots (sans ponctuation)
                words = re.findall(r'\b\w+\b', text)
                all_words.extend(words)
                
                # Extraire les phrases (séparées par . ! ?)
                phrases = re.split(r'[.!?]+', text)
                phrases = [p.strip() for p in phrases if len(p.strip()) > 10]  # Phrases de plus de 10 caractères
                all_phrases.extend(phrases)
        
        # Compter les répétitions de mots
        word_counts = Counter(all_words)
        repeated_words = [
            word for word, count in word_counts.items() 
            if count >= self.REPETITION_THRESHOLD and len(word) > 3  # Ignorer les mots très courts
        ]
        
        if repeated_words:
            warnings.append(
                f"Mots répétés fréquemment ({self.REPETITION_THRESHOLD}+ fois) : {', '.join(repeated_words[:5])}"
            )
        
        # Détecter les phrases identiques ou très similaires
        phrase_counts = Counter(all_phrases)
        repeated_phrases = [
            phrase for phrase, count in phrase_counts.items() 
            if count >= 2 and len(phrase) > 15
        ]
        
        if repeated_phrases:
            warnings.append(
                f"Phrases répétées détectées : '{repeated_phrases[0][:60]}...' (apparaît {phrase_counts[repeated_phrases[0]]} fois)"
            )
        
        return warnings
    
    def check_characterization_usage(self, interaction: Interaction, context: str) -> List[str]:
        """Vérifie si les données de caractérisation du contexte sont utilisées.
        
        Cette méthode utilise une heuristique basique : elle cherche des mots-clés
        du contexte dans les répliques. C'est une vérification approximative.
        
        Args:
            interaction: L'interaction à vérifier.
            context: Le contexte GDD utilisé pour la génération.
            
        Returns:
            Liste de warnings si la caractérisation semble sous-utilisée.
        """
        warnings: List[str] = []
        
        # Extraire les mots-clés du contexte (mots de 4+ caractères, non communs)
        common_words = {'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'et', 'ou', 'mais', 'pour', 'avec', 'sans', 'dans', 'sur', 'par', 'est', 'sont', 'était', 'étaient', 'être', 'avoir', 'a', 'ont', 'avait', 'avaient'}
        context_lower = context.lower()
        context_words = set(re.findall(r'\b\w{4,}\b', context_lower))
        context_keywords = context_words - common_words
        
        # Limiter aux 50 mots-clés les plus fréquents dans le contexte
        from collections import Counter
        context_word_counts = Counter(re.findall(r'\b\w{4,}\b', context_lower))
        top_keywords = [
            word for word, count in context_word_counts.most_common(50)
            if word not in common_words
        ][:20]  # Prendre les 20 premiers
        
        # Vérifier si ces mots-clés apparaissent dans les répliques
        all_dialogue_text = " ".join([
            element.text.lower() 
            for element in interaction.elements 
            if isinstance(element, DialogueLineElement)
        ])
        
        found_keywords = [kw for kw in top_keywords if kw in all_dialogue_text]
        
        # Si moins de 10% des mots-clés sont utilisés, alerter
        if top_keywords and len(found_keywords) / len(top_keywords) < 0.1:
            warnings.append(
                f"Peu de mots-clés du contexte utilisés ({len(found_keywords)}/{len(top_keywords)}). "
                f"Vérifiez que la caractérisation et la voix du personnage sont bien exploitées."
            )
        
        return warnings
    
    def validate_vocabulary_usage(
        self,
        interaction: Interaction,
        vocabulary_terms: List[Dict[str, Any]]
    ) -> List[str]:
        """Valide l'utilisation du vocabulaire Alteir dans l'interaction.
        
        Détecte les termes du vocabulaire utilisés et vérifie leur utilisation correcte.
        Génère des warnings si un terme est utilisé incorrectement ou absent alors qu'attendu.
        
        Args:
            interaction: L'interaction à valider.
            vocabulary_terms: Liste des termes du vocabulaire avec leurs définitions.
            
        Returns:
            Liste de warnings pour les problèmes de vocabulaire détectés.
        """
        warnings: List[str] = []
        
        if not vocabulary_terms:
            return warnings
        
        # Extraire tous les textes de dialogue
        all_dialogue_text = " ".join([
            element.text.lower()
            for element in interaction.elements
            if isinstance(element, DialogueLineElement)
        ])
        
        if not all_dialogue_text:
            return warnings
        
        # Créer un dictionnaire des termes par importance
        terms_by_importance = {}
        for term in vocabulary_terms:
            importance = term.get("importance", "Anecdotique")
            if importance not in terms_by_importance:
                terms_by_importance[importance] = []
            terms_by_importance[importance].append(term)
        
        # Vérifier l'utilisation des termes majeurs et importants
        important_terms = []
        for importance in ["Majeur", "Important"]:
            if importance in terms_by_importance:
                important_terms.extend(terms_by_importance[importance])
        
        # Détecter les termes utilisés
        used_terms = []
        for term in vocabulary_terms:
            terme = term.get("term", "").lower()
            if terme and terme in all_dialogue_text:
                used_terms.append(term)
        
        # Vérifier si des termes importants sont absents
        important_used = [t for t in used_terms if t.get("importance") in ["Majeur", "Important"]]
        if important_terms and len(important_used) == 0:
            # Ne pas alerter systématiquement, car tous les dialogues n'utilisent pas forcément le vocabulaire
            # Mais on peut suggérer d'utiliser des termes si le contexte s'y prête
            pass
        
        # Vérifier l'utilisation correcte (heuristique simple : présence du terme dans un contexte approprié)
        for term in used_terms:
            terme = term.get("term", "").lower()
            definition = term.get("definition", "").lower()
            
            # Vérifier si le terme apparaît dans un contexte qui semble approprié
            # (heuristique basique : présence de mots-clés de la définition à proximité)
            if definition:
                definition_keywords = set(re.findall(r'\b\w{4,}\b', definition))
                # Chercher si des mots-clés de la définition apparaissent près du terme
                # (dans un rayon de 50 caractères)
                term_positions = [m.start() for m in re.finditer(re.escape(terme), all_dialogue_text)]
                context_appropriate = False
                
                for pos in term_positions:
                    context_window = all_dialogue_text[max(0, pos - 50):pos + 50 + len(terme)]
                    context_keywords = set(re.findall(r'\b\w{4,}\b', context_window))
                    if definition_keywords & context_keywords:
                        context_appropriate = True
                        break
                
                # Si le terme est important et que le contexte ne semble pas approprié, alerter
                if term.get("importance") in ["Majeur", "Important"] and not context_appropriate:
                    warnings.append(
                        f"Terme important '{term.get('term')}' utilisé, mais le contexte ne semble pas "
                        f"correspondre à sa définition. Vérifiez l'utilisation correcte."
                    )
        
        # Statistiques (pour information, pas de warning)
        if used_terms:
            logger.debug(
                f"Validation vocabulaire: {len(used_terms)}/{len(vocabulary_terms)} termes utilisés "
                f"dans l'interaction"
            )
        
        return warnings

