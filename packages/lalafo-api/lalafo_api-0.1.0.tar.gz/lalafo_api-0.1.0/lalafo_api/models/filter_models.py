from typing import List, Optional, Dict, Union
from pydantic import BaseModel, HttpUrl

from ..enums import FilterKind
from .base_models import Cities


class FilterValue(BaseModel):
    """Значение фильтра"""
    value: str
    id: Optional[int] = None
    name: Optional[str] = None
    selected: bool = False
    count: Optional[int] = None
    is_popular: bool = False
    is_bottom: bool = False
    alias: Optional[str] = None
    image: Optional[HttpUrl] = None


class Filter(BaseModel):
    """Модель фильтра"""
    name: str
    kind: FilterKind
    id: Optional[int] = None
    is_range: bool = False
    is_multi_select: bool = False
    values: Optional[List[FilterValue]] = None
    cities: Optional[Cities] = None
    label_from: Optional[str] = None
    label_to: Optional[str] = None
    min: Optional[Union[int, float]] = None
    max: Optional[Union[int, float]] = None
    is_on_feed: bool = False
    feed_order_id: Optional[int] = None
    
    model_config = {
        "arbitrary_types_allowed": True
    }

    @property
    def has_values(self) -> bool:
        """Есть ли значения фильтра"""
        return self.values is not None and len(self.values) > 0
    
    @property
    def selected_values(self) -> List[FilterValue]:
        """Получить выбранные значения"""
        if not self.values:
            return []
        return [value for value in self.values if value.selected]
    
    def get_value_by_id(self, value_id: int) -> Optional[FilterValue]:
        """Получить значение по ID"""
        if not self.values:
            return None
        for value in self.values:
            if value.id == value_id:
                return value
        return None


class ParameterLink(BaseModel):
    """Ссылка параметра для фильтрации"""
    is_bottom: bool = False
    is_popular: bool = False
    value_id: Optional[int] = None
    value: Union[str, int]
    url: Optional[str] = None


class AdParameter(BaseModel):
    """Параметр объявления"""
    id: int
    name: str
    value: Union[int, str]
    value_id: Optional[int] = None
    links: List[ParameterLink] = []