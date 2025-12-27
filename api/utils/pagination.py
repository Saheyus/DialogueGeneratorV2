"""Utilitaires pour la pagination des réponses API."""
import os
from typing import TypeVar, Generic, List, Optional
from pydantic import BaseModel, Field

T = TypeVar('T')


class PaginationParams:
    """Paramètres de pagination depuis la requête."""
    
    def __init__(self, page: Optional[int] = None, page_size: Optional[int] = None):
        """Initialise les paramètres de pagination.
        
        Args:
            page: Numéro de page (1-indexed). Si None, pas de pagination.
            page_size: Taille de page. Si None, utilise la valeur par défaut.
        """
        self.page = page
        self.max_page_size = int(os.getenv("PAGINATION_MAX_PAGE_SIZE", "100"))
        
        # Déterminer page_size avec gestion de None et 0
        if page_size is None:
            self.page_size = int(os.getenv("PAGINATION_DEFAULT_PAGE_SIZE", "50"))
        else:
            self.page_size = page_size
        
        # Valider et ajuster
        if self.page_size > self.max_page_size:
            self.page_size = self.max_page_size
        if self.page_size < 1:
            self.page_size = 1
        
        if self.page is not None and self.page < 1:
            self.page = 1
    
    @property
    def is_enabled(self) -> bool:
        """Indique si la pagination est activée.
        
        Returns:
            True si page est fourni, False sinon.
        """
        return self.page is not None
    
    @property
    def offset(self) -> int:
        """Calcule l'offset pour la pagination.
        
        Returns:
            Offset (0-indexed).
        """
        if not self.is_enabled:
            return 0
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Retourne la limite pour la pagination.
        
        Returns:
            Nombre d'éléments à retourner.
        """
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Réponse paginée générique."""
    
    items: List[T] = Field(..., description="Liste des éléments de la page")
    total: int = Field(..., description="Nombre total d'éléments")
    page: Optional[int] = Field(None, description="Numéro de page actuelle (1-indexed)")
    page_size: Optional[int] = Field(None, description="Taille de la page")
    total_pages: Optional[int] = Field(None, description="Nombre total de pages")
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        pagination_params: Optional[PaginationParams] = None
    ) -> "PaginatedResponse[T]":
        """Crée une réponse paginée.
        
        Args:
            items: Liste des éléments de la page.
            total: Nombre total d'éléments.
            pagination_params: Paramètres de pagination (optionnel).
            
        Returns:
            Réponse paginée.
        """
        if pagination_params and pagination_params.is_enabled:
            total_pages = (total + pagination_params.page_size - 1) // pagination_params.page_size
            return cls(
                items=items,
                total=total,
                page=pagination_params.page,
                page_size=pagination_params.page_size,
                total_pages=total_pages
            )
        else:
            # Pas de pagination : retourner toutes les données
            return cls(
                items=items,
                total=total,
                page=None,
                page_size=None,
                total_pages=None
            )


def paginate_list(
    items: List[T],
    pagination_params: Optional[PaginationParams]
) -> List[T]:
    """Pagine une liste d'éléments.
    
    Args:
        items: Liste complète d'éléments.
        pagination_params: Paramètres de pagination (optionnel).
        
    Returns:
        Liste paginée (ou complète si pagination désactivée).
    """
    if not pagination_params or not pagination_params.is_enabled:
        return items
    
    start = pagination_params.offset
    end = start + pagination_params.limit
    
    return items[start:end]


def get_pagination_params(
    page: Optional[int] = None,
    page_size: Optional[int] = None
) -> PaginationParams:
    """Crée des paramètres de pagination depuis les arguments.
    
    Args:
        page: Numéro de page (1-indexed).
        page_size: Taille de page.
        
    Returns:
        Paramètres de pagination.
    """
    return PaginationParams(page=page, page_size=page_size)

