import time
from typing import Optional, Dict, Any, List

import httpx
from ..enums import Currency
from ..models import (
    ClientConfig, SearchRequest, CategoriesResponse,
    FiltersResponse, ParamsFilterResponse, AdDetailsResponse,
    SearchResponse, AdCompact
)
from ..utils import parse_ad_url, parse_search_url
from ..exceptions import APIError
from .base_lalafo_client import BaseLalafoClient
from .clients import get_sync_client


class LalafoClient(BaseLalafoClient):
    """Синхронный клиент Lalafo API"""
    
    def __init__(
        self,
        config: Optional[ClientConfig] = None,
        logger: Optional[Any] = None
    ):
        super().__init__(config, logger)
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retries: int = None
    ) -> Dict[str, Any]:
        retries = retries or self.config.max_retries
        headers = self._prepare_headers(headers)
        
        for attempt in range(retries):
            try:
                self._log_request(method, endpoint, params)
                
                response = get_sync_client().request(
                    method=method,
                    url=endpoint,
                    params=params,
                    headers=headers
                )
                
                self._log_response(response)
                return self._handle_response(response)
                
            except httpx.TimeoutException as e:
                self.logger.warning(f"Таймаут запроса (попытка {attempt + 1}/{retries}): {e}")
                if attempt == retries - 1:
                    raise APIError(f"Таймаут запроса после {retries} попыток", 408)
                time.sleep(self.config.retry_delay * (attempt + 1))
                
            except httpx.RequestError as e:
                self.logger.error(f"Ошибка запроса: {e}")
                if attempt == retries - 1:
                    raise APIError(f"Ошибка сети: {str(e)}", 0)
                time.sleep(self.config.retry_delay * (attempt + 1))
    
    def get_categories_tree(self, with_duplicates: bool = True) -> CategoriesResponse:
        endpoint = "/v3/categories/tree"
        params = {"with_duplicates": 1 if with_duplicates else 0}
        
        data = self._make_request("GET", endpoint, params=params)
        return CategoriesResponse.from_api_response(data)
    
    def get_filters(
        self,
        category_id: Optional[int] = None,
        city_id: Optional[int] = None,
        currency: Currency = Currency.KGS,
        sort_by: str = "default",
        with_filters: bool = True,
        with_empty_values: bool = True,
        with_category_counter: bool = True,
        parameters: Optional[Dict[str, List[int]]] = None,
        price_from: Optional[int] = None,
        price_to: Optional[int] = None
    ) -> FiltersResponse:
        endpoint = "/v3/ads/filters"
        
        params = {
            "with_filters": str(with_filters).lower(),
            "with_empty_values": str(with_empty_values).lower(),
            "with_category_counter": str(with_category_counter).lower(),
            "currency": currency.value,
            "sort_by": sort_by
        }
        
        if category_id:
            params["category_id"] = category_id
        if city_id:
            params["city_id"] = city_id
        if price_from is not None:
            params["price[from]"] = price_from
        if price_to is not None:
            params["price[to]"] = price_to
        
        if parameters:
            for param_id, values in parameters.items():
                for i, value_id in enumerate(values):
                    params[f"parameters[{param_id}][{i}]"] = value_id
        
        data = self._make_request("GET", endpoint, params=params)
        return FiltersResponse(**data)
    
    def get_params_filter(
        self,
        category_id: int,
        city_id: Optional[int] = None,
        radius: int = 0,
        location_lat: Optional[float] = None,
        location_lng: Optional[float] = None
    ) -> ParamsFilterResponse:
        endpoint = "/v3/params/filter"
        
        params = {
            "category_id": category_id,
            "radius": radius
        }
        
        if city_id:
            params["city_id"] = city_id
        if location_lat:
            params["location[lat]"] = location_lat
        if location_lng:
            params["location[lng]"] = location_lng
        
        data = self._make_request("GET", endpoint, params=params)
        return ParamsFilterResponse.from_api_response(data)
    
    def get_ad_details(self, ad_id: int) -> AdDetailsResponse:
        endpoint = f"/v3/ads/details/{ad_id}"
        
        data = self._make_request("GET", endpoint)
        return AdDetailsResponse.from_api_response(data)
    
    def search_ads(self, search_request: SearchRequest) -> SearchResponse:
        endpoint = "/v3/ads/search"
        params = search_request.to_query_params()
        
        data = self._make_request("GET", endpoint, params=params)
        return SearchResponse.from_api_response(data)
    
    def search_ads_all_pages(
        self,
        search_request: SearchRequest,
        max_pages: int = 100,
        delay_between_pages: float = 0.5
    ) -> List[AdCompact]:
        all_items = []
        current_page = search_request.page
        
        for page_num in range(max_pages):
            search_request.page = current_page
            
            try:
                response = self.search_ads(search_request)
                all_items.extend(response.items)
                
                if not response.has_next_page:
                    break
                
                current_page += 1
                
                if delay_between_pages > 0:
                    import time
                    time.sleep(delay_between_pages)
                    
            except Exception as e:
                break
        
        return all_items
    
    def search_ads_simple(
        self,
        category_id: Optional[int] = None,
        city_id: Optional[int] = None,
        q: Optional[str] = None,
        price_from: Optional[int] = None,
        price_to: Optional[int] = None,
        page: int = 1,
        per_page: int = 40
    ) -> SearchResponse:
        search_request = SearchRequest(
            category_id=category_id,
            city_id=city_id,
            q=q,
            price_from=price_from,
            price_to=price_to,
            page=page,
            per_page=per_page
        )
        
        return self.search_ads(search_request)
    
    def get_user_ads(
        self,
        user_id: int,
        page: int = 1,
        per_page: int = 40
    ) -> SearchResponse:
        search_request = SearchRequest(
            user_id=user_id,
            page=page,
            per_page=per_page
        )
        
        return self.search_ads(search_request)
    
    def get_related_ads(
        self,
        ad_id: int,
        category_id: int,
        city_id: int,
        per_page: int = 40,
        vip_count: int = 2
    ) -> SearchResponse:
        endpoint = f"/v3/ads/related-items/{ad_id}"
        
        params = {
            "category_id": category_id,
            "city_id": city_id,
            "per-page": per_page,
            "vip-count": vip_count,
            "with_feed_banner": "true"
        }
        
        data = self._make_request("GET", endpoint, params=params)
        return SearchResponse.from_api_response(data)
    
    def get_feed_elements(self, category_id: int) -> Dict[str, Any]:
        endpoint = "/v3/feed-elements/scheme"
        params = {"category_id": category_id}
        
        return self._make_request("GET", endpoint, params=params)
    
    def get_user_status(self, user_ids: List[int]) -> List[Dict[str, Any]]:
        endpoint = "/v3/users/get-user-status"
        
        params = {}
        for i, user_id in enumerate(user_ids):
            params[f"userIds[{i}]"] = user_id
        
        return self._make_request("GET", endpoint, params=params)

    def fetch_ad_from_url(self, url: str) -> AdDetailsResponse:
        parsed = parse_ad_url(url)
        if not parsed or 'ad_id' not in parsed:
            raise ValueError(f"Не удалось извлечь ID объявления из URL: {url}")
        
        return self.get_ad_details(parsed['ad_id'])

    def get_search_request_from_url(
            self, url: str,
            currency: Currency = Currency.KGS
        ) -> Optional[SearchRequest]:
        parsed = parse_search_url(url, self.get_filters(currency=currency).filters[0].cities, self.get_categories_tree())
        if not parsed:
            return None
        return SearchRequest(**parsed)