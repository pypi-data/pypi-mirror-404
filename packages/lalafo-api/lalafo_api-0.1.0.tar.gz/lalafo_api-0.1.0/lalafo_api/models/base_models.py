from typing import List, Optional, Any
from pydantic import BaseModel, Field, HttpUrl


class Image(BaseModel):
    """Модель изображения"""
    id: int
    is_main: bool = False
    thumbnail_url: Optional[HttpUrl] = None
    thumbnail_webp_url: Optional[HttpUrl] = None
    original_url: Optional[HttpUrl] = None
    original_webp_url: Optional[HttpUrl] = None
    width: Optional[int] = None
    height: Optional[int] = None
    is_cv_image: bool = False
    p_hash: Optional[str] = None


class User(BaseModel):
    """Модель пользователя"""
    id: int
    username: str
    pro: bool = False
    user_hash: Optional[str] = None
    response_rate: Optional[int] = None
    response_time: Optional[int] = None
    is_deleted: bool = False
    is_banned: bool = False
    hidden_delete: bool = False
    response_info: Optional[str] = None


class City(BaseModel):
    """Модель города"""
    id: int
    value: str
    alias: str
    selected: bool = False
    lat: Optional[float] = None
    lng: Optional[float] = None
    count: Optional[int] = None


class Cities(BaseModel):
    """Данные о городах в фильтре"""
    values: List[City]
    
    @property
    def selected_cities(self) -> List[City]:
        """Получить выбранные города"""
        return [city for city in self.values if city.selected]
    
    @property
    def city_ids(self) -> List[int]:
        """Получить список ID городов"""
        return [city.id for city in self.values]
    
    def get_city_by_id(self, city_id: int) -> Optional[City]:
        """Получить город по ID"""
        for city in self.values:
            if city.id == city_id:
                return city
        return None
    
    def get_city_by_alias(self, city_alias: str):
        """Получить город по названию"""
        for city in self.values:
            if city.alias == city_alias:
                return city
        return None


class CategoryCounter(BaseModel):
    """Счетчик категории"""
    category_id: int
    count: int
    order: int


class CountInfo(BaseModel):
    """Информация о количестве"""
    ads_count: str | int
    feed_name: str = Field(alias="feed-name")
    feed_id: int = Field(alias="feed-id")
    category_counter: Optional[List[CategoryCounter]] = None


class TrackingInfo(BaseModel):
    """Информация для трекинга"""
    name: str
    value: Any