from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field

from ..enums import Currency, SortBy


class SearchRequest(BaseModel):
    """Модель запроса поиска"""
    category_id: Optional[int] = None
    city_id: Optional[int] = None
    q: Optional[str] = None
    price_from: Optional[int] = Field(None, alias="price[from]")
    price_to: Optional[int] = Field(None, alias="price[to]")
    currency: Currency = Currency.KGS
    sort_by: SortBy = SortBy.DEFAULT
    radius: Optional[int] = None
    location_lat: Optional[float] = Field(None, alias="location[lat]")
    location_lng: Optional[float] = Field(None, alias="location[lng]")
    per_page: int = Field(40, alias="per-page")
    page: int = 1
    vip_count: int = Field(0, alias="vip_count")
    user_id: Optional[int] = None
    parameters: Optional[Dict[str, List[int]]] = None
    with_feed_banner: bool = True
    without_negotiable: bool = False
    is_payment: Optional[bool] = None
    
    model_config = {
        "populate_by_name": True
    }
    
    def to_query_params(self) -> Dict[str, Any]:
        """Преобразует в параметры запроса"""
        params = {}
        
        if self.category_id:
            params['category_id'] = self.category_id
        if self.city_id:
            params['city_id'] = self.city_id
        if self.q:
            params['q'] = self.q
        if self.price_from is not None:
            params['price[from]'] = self.price_from
        if self.price_to is not None:
            params['price[to]'] = self.price_to
        if self.currency:
            params['currency'] = self.currency.value
        if self.sort_by:
            params['sort_by'] = self.sort_by.value
        if self.radius:
            params['radius'] = self.radius
        if self.location_lat:
            params['location[lat]'] = self.location_lat
        if self.location_lng:
            params['location[lng]'] = self.location_lng
        
        params['per-page'] = self.per_page
        params['page'] = self.page
        params['vip_count'] = self.vip_count
        
        if self.user_id:
            params['user_id'] = self.user_id
        if self.with_feed_banner:
            params['with_feed_banner'] = 'true'
        if self.without_negotiable:
            params['without_negotiable'] = 'true'
        if self.is_payment is not None:
            params['is_payment'] = 'true' if self.is_payment else 'false'
        
        if self.parameters:
            for param_id, values in self.parameters.items():
                for i, value_id in enumerate(values):
                    params[f'parameters[{param_id}][{i}]'] = value_id
        
        return params


class ClientConfig(BaseModel):
    """Конфигурация клиента"""
    app_version: str = "21633"
    country_id: int = 12
    language: str = "ru_RU"
    device: str = "android"
    experiment: str = "newadui-feed2601-partition-2"
    theme: str = "light"
    user_agent: str = "LalafoAPIClient/1.0.0"
    user_hash: Optional[str] = None
    max_retries: int = 3
    retry_delay: float = 1.0