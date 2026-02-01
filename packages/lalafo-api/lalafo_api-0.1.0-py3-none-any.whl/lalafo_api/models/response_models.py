from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from .category_models import Category
from .ad_models import AdCompact, AdDetail
from .filter_models import Filter
from .base_models import CountInfo


class PaginationLinks(BaseModel):
    """Ссылки пагинации"""
    self: Optional[Dict[str, str]] = None
    first: Optional[Dict[str, str]] = None
    last: Optional[Dict[str, str]] = None
    next: Optional[Dict[str, str]] = None


class PaginationMeta(BaseModel):
    """Метаданные пагинации"""
    totalCount: int
    pageCount: int
    currentPage: int
    perPage: int
    feed: Optional[str] = None
    feed_id: Optional[int] = None


class CategoriesResponse(BaseModel):
    """Ответ с категориями"""
    categories: List[Category]
    
    @classmethod
    def from_api_response(cls, data: List[Dict]) -> 'CategoriesResponse':
        categories = [Category(**item) for item in data]
        return cls(categories=categories)
    
    def __iter__(self):
        return iter(self.categories)
    
    def find_by_id(self, category_id: int) -> Optional[Category]:
        """
        Найти категорию по ID во всем дереве
        
        Args:
            category_id: ID категории
            
        Returns:
            Найденная категория или None
        """
        for category in self.categories:
            found = category.find_by_id(category_id)
            if found:
                return found
        return None
    
    def find_by_name(self, name: str, case_sensitive: bool = False) -> List[Category]:
        """
        Найти категории по названию во всем дереве
        
        Args:
            name: Название или часть названия
            case_sensitive: Учитывать регистр
            
        Returns:
            Список найденных категорий
        """
        results = []
        for category in self.categories:
            results.extend(category.find_by_name(name, case_sensitive))
        return results
    
    def find_by_alias(self, alias: str) -> List[Category]:
        """
        Найти категории по алиасу во всем дереве
        
        Args:
            alias: Алиас категории
            
        Returns:
            Список найденных категорий
        """
        results = []
        for category in self.categories:
            results.extend(category.find_by_alias(alias))
        return results
    
    def find_by_path(self, path: str) -> Optional[Category]:
        """
        Найти категорию по пути
        
        Args:
            path: Путь категории (например, 'elektronika/mobilnye-telefony')
            
        Returns:
            Найденная категория или None
        """
        path_parts = path.strip('/').split('/')
        
        current_categories = self.categories
        
        for part in path_parts:
            found = None
            for cat in current_categories:
                if cat.alias == part:
                    found = cat
                    break
            
            if not found:
                return None
            
            current_categories = found.children
        
        return found if found else None
    
    def flatten(self) -> List[Category]:
        """
        Получить плоский список всех категорий
        
        Returns:
            Плоский список категорий
        """
        result = []
        
        def collect(cats):
            for cat in cats:
                result.append(cat)
                if cat.children:
                    collect(cat.children)
        
        collect(self.categories)
        return result
    
    def get_category_path(self, category_id: int) -> List[Category]:
        """
        Получить путь к категории (все предки)
        
        Args:
            category_id: ID категории
            
        Returns:
            Список категорий от корня до указанной
        """
        category = self.find_by_id(category_id)
        if not category:
            return []
        
        def find_path(root_cats, target_id, path):
            for cat in root_cats:
                if cat.id == target_id:
                    return path + [cat]
                
                if cat.children:
                    result = find_path(cat.children, target_id, path + [cat])
                    if result:
                        return result
            
            return None
        
        for root in self.categories:
            path = find_path([root], category_id, [])
            if path:
                return path
        
        return []


class FiltersResponse(BaseModel):
    """Ответ с фильтрами"""
    count: CountInfo
    filters: List[Filter]


class ParamsFilterResponse(BaseModel):
    """Ответ с параметрами фильтров"""
    filters: List[Filter]
    
    @classmethod
    def from_api_response(cls, data: List[Dict]) -> 'ParamsFilterResponse':
        """Создает из API ответа"""
        filters = [Filter(**item) for item in data]
        return cls(filters=filters)


class AdDetailsResponse(BaseModel):
    """Ответ с деталями объявления"""
    ad: AdDetail
    
    @classmethod
    def from_api_response(cls, data: Dict) -> 'AdDetailsResponse':
        """Создает из API ответа"""
        return cls(ad=AdDetail(**data))


class SearchResponse(BaseModel):
    """Ответ поиска объявлений"""
    items: List[AdCompact]
    links: PaginationLinks = Field(alias="_links")
    meta: PaginationMeta = Field(alias="_meta")
    related_feed: Optional[Dict[str, Any]] = Field(alias="_relatedFeed", default=None)
    
    @property
    def has_next_page(self) -> bool:
        """Есть ли следующая страница"""
        return self.links.next is not None
    
    @property
    def has_previous_page(self) -> bool:
        """Есть ли предыдущая страница"""
        return self.meta.currentPage > 1
    
    @classmethod
    def from_api_response(cls, data: Dict) -> 'SearchResponse':
        """Создает из API ответа"""
        items = [AdCompact(**item) for item in data.get('items', [])]
        data['items'] = items
        return cls(**data)