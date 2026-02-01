from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, HttpUrl

from .base_models import Image, User, TrackingInfo
from .filter_models import AdParameter
from ..enums import Currency, AdStatus


class AdCompact(BaseModel):
    """Компактная модель объявления (для поиска)"""
    id: int
    title: str
    description: Optional[str] = None
    hide_phone: Optional[bool] = None
    price: Optional[int] = None
    old_price: Optional[int] = None
    currency: Currency
    city: str
    city_id: int
    city_alias: Optional[str] = None
    category_id: int
    images: List[Image] = []
    user: User
    is_vip: bool = False
    is_premium: bool = False
    is_negotiable: bool = False
    views: int = 0
    impressions: int = 0
    favorite_count: int = 0
    callers_count: int = 0
    writers_count: int = 0
    created_time: int
    updated_time: int
    score_order: Optional[int] = None
    last_push_up: Optional[int] = None
    mobile: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    tracking_info: List[TrackingInfo] = []
    campaign_show: bool = False
    is_ppv: bool = False
    
    @property
    def created_at(self) -> datetime:
        """Время создания в datetime"""
        return datetime.fromtimestamp(self.created_time)
    
    @property
    def updated_at(self) -> datetime:
        """Время обновления в datetime"""
        return datetime.fromtimestamp(self.updated_time)
    
    @property
    def has_old_price(self) -> bool:
        """Есть ли старая цена"""
        return self.old_price is not None and self.old_price > 0
    
    @property
    def discount_percent(self) -> Optional[int]:
        """Процент скидки"""
        if not self.has_old_price:
            return None
        return int((1 - self.price / self.old_price) * 100)


class AdDetail(AdCompact):
    """Полная модель объявления"""
    params: List[AdParameter] = []
    email: Optional[str] = None
    status_id: AdStatus
    can_free_push: bool = False
    paid_features: List[int] = []
    paid_packages: List[str] = []
    url: Optional[HttpUrl] = None
    is_freedom: bool = False
    response_type: int = 0
    decoration_mask: int = 0
    price_type: int = 1
    ad_label: Optional[str] = None
    national_price: Optional[int] = None
    national_old_price: Optional[int] = None
    is_identity: bool = False
    page_visibility_info: Dict[str, bool] = {}
    available_campaign_types: List[str] = []
    is_paid_posting: bool = False
    campaign: List[Any] = []
    
    @property
    def main_image(self) -> Optional[Image]:
        """Главное изображение"""
        for img in self.images:
            if img.is_main:
                return img
        return self.images[0] if self.images else None
    
    @property
    def parameter_dict(self) -> Dict[str, str]:
        """Параметры в виде словаря"""
        return {param.name: param.value for param in self.params}