"""Tests pour les utilitaires de pagination."""
import pytest
from api.utils.pagination import (
    PaginationParams,
    PaginatedResponse,
    paginate_list,
    get_pagination_params
)


class TestPaginationParams:
    """Tests pour PaginationParams."""
    
    def test_default_values(self):
        """Test les valeurs par défaut."""
        params = PaginationParams()
        assert params.page is None
        assert params.page_size == 50
        assert params.is_enabled is False
    
    def test_pagination_enabled(self):
        """Test que is_enabled est True quand page est fourni."""
        params = PaginationParams(page=1)
        assert params.is_enabled is True
    
    def test_offset_calculation(self):
        """Test le calcul de l'offset."""
        params = PaginationParams(page=1, page_size=10)
        assert params.offset == 0
        
        params = PaginationParams(page=2, page_size=10)
        assert params.offset == 10
        
        params = PaginationParams(page=3, page_size=20)
        assert params.offset == 40
    
    def test_limit(self):
        """Test que limit retourne page_size."""
        params = PaginationParams(page=1, page_size=25)
        assert params.limit == 25
    
    def test_page_size_max_limit(self):
        """Test que page_size est limité à max_page_size."""
        params = PaginationParams(page=1, page_size=200)  # > 100 (défaut)
        assert params.page_size == 100
    
    def test_page_size_min_limit(self):
        """Test que page_size est au minimum 1."""
        params = PaginationParams(page=1, page_size=0)
        assert params.page_size == 1
    
    def test_page_min_limit(self):
        """Test que page est au minimum 1."""
        params = PaginationParams(page=0, page_size=10)
        assert params.page == 1


class TestPaginatedResponse:
    """Tests pour PaginatedResponse."""
    
    def test_create_without_pagination(self):
        """Test création sans pagination."""
        items = [1, 2, 3, 4, 5]
        response = PaginatedResponse.create(items=items, total=5)
        
        assert response.items == items
        assert response.total == 5
        assert response.page is None
        assert response.page_size is None
        assert response.total_pages is None
    
    def test_create_with_pagination(self):
        """Test création avec pagination."""
        items = [1, 2, 3, 4, 5]
        pagination_params = PaginationParams(page=1, page_size=2)
        response = PaginatedResponse.create(items=items, total=5, pagination_params=pagination_params)
        
        assert response.items == items
        assert response.total == 5
        assert response.page == 1
        assert response.page_size == 2
        assert response.total_pages == 3  # 5 items / 2 par page = 3 pages
    
    def test_total_pages_calculation(self):
        """Test le calcul de total_pages."""
        # 10 items, 3 par page = 4 pages
        pagination_params = PaginationParams(page=1, page_size=3)
        response = PaginatedResponse.create(items=[1, 2, 3], total=10, pagination_params=pagination_params)
        assert response.total_pages == 4
        
        # 10 items, 5 par page = 2 pages
        pagination_params = PaginationParams(page=1, page_size=5)
        response = PaginatedResponse.create(items=[1, 2, 3, 4, 5], total=10, pagination_params=pagination_params)
        assert response.total_pages == 2


class TestPaginateList:
    """Tests pour paginate_list."""
    
    def test_paginate_list_no_pagination(self):
        """Test pagination désactivée."""
        items = [1, 2, 3, 4, 5]
        result = paginate_list(items, None)
        assert result == items
    
    def test_paginate_list_first_page(self):
        """Test première page."""
        items = list(range(1, 11))  # [1, 2, ..., 10]
        params = PaginationParams(page=1, page_size=3)
        result = paginate_list(items, params)
        
        assert result == [1, 2, 3]
    
    def test_paginate_list_middle_page(self):
        """Test page du milieu."""
        items = list(range(1, 11))  # [1, 2, ..., 10]
        params = PaginationParams(page=2, page_size=3)
        result = paginate_list(items, params)
        
        assert result == [4, 5, 6]
    
    def test_paginate_list_last_page(self):
        """Test dernière page (incomplète)."""
        items = list(range(1, 11))  # [1, 2, ..., 10]
        params = PaginationParams(page=4, page_size=3)
        result = paginate_list(items, params)
        
        assert result == [10]  # Seulement 1 item
    
    def test_paginate_list_empty(self):
        """Test avec liste vide."""
        items = []
        params = PaginationParams(page=1, page_size=10)
        result = paginate_list(items, params)
        
        assert result == []


class TestGetPaginationParams:
    """Tests pour get_pagination_params."""
    
    def test_with_page_and_page_size(self):
        """Test avec page et page_size."""
        params = get_pagination_params(page=2, page_size=25)
        assert params.page == 2
        assert params.page_size == 25
        assert params.is_enabled is True
    
    def test_without_page(self):
        """Test sans page (pagination désactivée)."""
        params = get_pagination_params(page=None, page_size=25)
        assert params.page is None
        assert params.is_enabled is False






