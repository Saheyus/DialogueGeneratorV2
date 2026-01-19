"""Repository pour le stockage des budgets LLM."""
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Protocol

logger = logging.getLogger(__name__)


class ICostBudgetRepository(Protocol):
    """Interface pour le repository de budgets LLM."""
    
    def get_budget(self, user_id: str, month: str) -> Optional[Dict]:
        """Récupère le budget pour un utilisateur et un mois.
        
        Args:
            user_id: ID de l'utilisateur.
            month: Mois au format "YYYY-MM" (ex: "2026-01").
            
        Returns:
            Dictionnaire avec les clés: month, amount, quota, updated_at.
            Retourne None si le budget n'existe pas.
        """
        ...
    
    def update_budget(self, user_id: str, month: str, amount: float, quota: float) -> None:
        """Met à jour le budget pour un utilisateur et un mois.
        
        Args:
            user_id: ID de l'utilisateur.
            month: Mois au format "YYYY-MM".
            amount: Montant dépensé.
            quota: Quota mensuel.
        """
        ...
    
    def reset_month(self, user_id: str, new_month: str) -> None:
        """Réinitialise le budget pour un nouveau mois.
        
        Args:
            user_id: ID de l'utilisateur.
            new_month: Nouveau mois au format "YYYY-MM".
        """
        ...


class FileCostBudgetRepository:
    """Repository de budgets LLM basé sur fichier JSON.
    
    Stocke les budgets dans un fichier JSON unique.
    Format: data/cost_budgets.json
    Structure: {user_id: {month: "2026-01", amount: 90.0, quota: 100.0, updated_at: timestamp}}
    """
    
    def __init__(self, storage_file: str):
        """Initialise le repository avec un fichier de stockage.
        
        Args:
            storage_file: Chemin vers le fichier JSON de stockage.
        """
        self.storage_file = Path(storage_file)
        # Créer le dossier parent si nécessaire
        os.makedirs(self.storage_file.parent, exist_ok=True)
        logger.info(f"FileCostBudgetRepository initialisé avec le fichier: {self.storage_file.absolute()}")
    
    def _load_all_budgets(self) -> Dict[str, Dict]:
        """Charge tous les budgets depuis le fichier.
        
        Returns:
            Dictionnaire {user_id: {month, amount, quota, updated_at}}
        """
        if not self.storage_file.exists():
            return {}
        
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("budgets", {})
        except (json.JSONDecodeError, KeyError, IOError) as e:
            logger.error(f"Erreur lors du chargement de {self.storage_file}: {e}")
            return {}
    
    def _save_all_budgets(self, budgets: Dict[str, Dict]) -> None:
        """Sauvegarde tous les budgets dans le fichier.
        
        Args:
            budgets: Dictionnaire {user_id: {month, amount, quota, updated_at}}
        """
        data = {
            "budgets": budgets
        }
        
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            logger.debug(f"Budgets sauvegardés dans {self.storage_file}")
        except IOError as e:
            logger.error(f"Erreur lors de la sauvegarde dans {self.storage_file}: {e}")
            raise
    
    def get_budget(self, user_id: str, month: str) -> Optional[Dict]:
        """Récupère le budget pour un utilisateur et un mois.
        
        Args:
            user_id: ID de l'utilisateur.
            month: Mois au format "YYYY-MM" (ex: "2026-01").
            
        Returns:
            Dictionnaire avec les clés: month, amount, quota, updated_at.
            Retourne None si le budget n'existe pas.
        """
        budgets = self._load_all_budgets()
        user_budget = budgets.get(user_id)
        
        if user_budget is None:
            return None
        
        # Vérifier si le budget correspond au mois demandé
        if user_budget.get("month") == month:
            return user_budget
        
        # Si le mois ne correspond pas, retourner None (le service gérera le reset)
        return None
    
    def update_budget(self, user_id: str, month: str, amount: float, quota: float) -> None:
        """Met à jour le budget pour un utilisateur et un mois.
        
        Args:
            user_id: ID de l'utilisateur.
            month: Mois au format "YYYY-MM".
            amount: Montant dépensé.
            quota: Quota mensuel.
        """
        budgets = self._load_all_budgets()
        
        budgets[user_id] = {
            "month": month,
            "amount": amount,
            "quota": quota,
            "updated_at": datetime.now().isoformat()
        }
        
        self._save_all_budgets(budgets)
        logger.debug(f"Budget mis à jour pour {user_id} ({month}): {amount:.2f}€ / {quota:.2f}€")
    
    def reset_month(self, user_id: str, new_month: str) -> None:
        """Réinitialise le budget pour un nouveau mois.
        
        Args:
            user_id: ID de l'utilisateur.
            new_month: Nouveau mois au format "YYYY-MM".
        """
        budgets = self._load_all_budgets()
        user_budget = budgets.get(user_id)
        
        if user_budget is None:
            # Pas de budget existant, créer un nouveau avec quota=0
            budgets[user_id] = {
                "month": new_month,
                "amount": 0.0,
                "quota": 0.0,
                "updated_at": datetime.now().isoformat()
            }
        else:
            # Préserver le quota, reset amount à 0
            budgets[user_id] = {
                "month": new_month,
                "amount": 0.0,
                "quota": user_budget.get("quota", 0.0),
                "updated_at": datetime.now().isoformat()
            }
        
        self._save_all_budgets(budgets)
        logger.debug(f"Budget reseté pour {user_id} vers {new_month}")
