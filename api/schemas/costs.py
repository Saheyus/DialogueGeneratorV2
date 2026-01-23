"""Schémas Pydantic pour les endpoints de cost governance."""
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class BudgetResponse(BaseModel):
    """Schéma de réponse pour le budget actuel."""
    quota: float = Field(..., ge=0.0, description="Quota mensuel en USD")
    amount: float = Field(..., ge=0.0, description="Montant dépensé en USD")
    percentage: float = Field(..., ge=0.0, le=100.0, description="Pourcentage du budget utilisé (0-100)")
    remaining: float = Field(..., ge=0.0, description="Montant restant en USD")
    
    model_config = ConfigDict()


class UpdateBudgetRequest(BaseModel):
    """Schéma de requête pour mettre à jour le quota budget."""
    quota: float = Field(..., ge=0.0, description="Nouveau quota mensuel en USD")
    
    model_config = ConfigDict()


class DailyCost(BaseModel):
    """Coût journalier."""
    date: str = Field(..., description="Date au format YYYY-MM-DD")
    cost: float = Field(..., ge=0.0, description="Coût total pour cette date en USD")
    
    model_config = ConfigDict()


class UsageResponse(BaseModel):
    """Schéma de réponse pour l'usage avec graphique."""
    daily_costs: List[DailyCost] = Field(..., description="Coûts quotidiens pour le graphique")
    total: float = Field(..., ge=0.0, description="Coût total du mois en USD")
    percentage: float = Field(..., ge=0.0, le=100.0, description="Pourcentage du budget utilisé")
    
    model_config = ConfigDict()
