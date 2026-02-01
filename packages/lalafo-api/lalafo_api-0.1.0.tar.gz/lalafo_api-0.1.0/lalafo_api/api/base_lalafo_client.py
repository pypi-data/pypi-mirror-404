from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import logging

import httpx

from ..enums import Currency
from ..models import (
    ClientConfig, SearchRequest, CategoriesResponse,
    FiltersResponse, ParamsFilterResponse, AdDetailsResponse,
    SearchResponse, AdCompact
)
from ..exceptions import (
    APIError, RateLimitError, AuthenticationError,
    NotFoundError
)


class BaseLalafoClient(ABC):
    """Базовый класс клиента Lalafo API"""
    
    def __init__(
        self,
        config: Optional[ClientConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Инициализация клиента
        
        Args:
            config: Конфигурация клиента
            logger: Логгер для записи событий
        """
        self.config = config or ClientConfig()
        self.logger = logger or logging.getLogger(__name__)
        self._setup_logger()
    
    def _setup_logger(self):
        """Настройка логгера"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    @property
    def _headers(self) -> dict:
        raw_headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "App-Version": self.config.app_version,
            "Content-Type": "application/json",
            "Country-Id": str(self.config.country_id) if self.config.country_id is not None else None,
            "Device": self.config.device,
            "experiment": self.config.experiment,
            "Host": "api.lalafo.com",
            "Language": self.config.language,
            "Theme": self.config.theme,
            "User-Agent": self.config.user_agent,
        }
        
        return {k: v for k, v in raw_headers.items() if v is not None}
    
    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        Обработка ответа от API
        
        Args:
            response: Ответ от сервера
            
        Returns:
            Распарсенный JSON
            
        Raises:
            APIError: Ошибка API
            RateLimitError: Превышен лимит запросов
            AuthenticationError: Ошибка аутентификации
            NotFoundError: Ресурс не найден
        """
        if response.status_code == 429:
            raise RateLimitError(
                "Превышен лимит запросов",
                response.status_code,
                response.json() if response.content else None
            )
        
        if response.status_code == 401:
            raise AuthenticationError(
                "Ошибка аутентификации",
                response.status_code,
                response.json() if response.content else None
            )
        
        if response.status_code == 404:
            raise NotFoundError(
                "Ресурс не найден",
                response.status_code,
                response.json() if response.content else None
            )
        
        if response.status_code >= 400:
            error_data = None
            try:
                error_data = response.json()
                error_msg = error_data.get('message', response.text)
            except Exception:
                error_msg = response.text
            
            raise APIError(
                error_msg,
                response.status_code,
                error_data
            )
        
        try:
            return response.json()
        except Exception as e:
            self.logger.error(f"Ошибка парсинга JSON: {e}")
            raise APIError(
                f"Ошибка парсинга ответа: {str(e)}",
                response.status_code
            )
    
    def _build_request_id(self) -> str:
        """Генерация Request-Id"""
        import uuid
        return f"android_{uuid.uuid4().hex[:32]}"
    
    def _add_request_id(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Добавление Request-Id в заголовки"""
        headers["Request-Id"] = self._build_request_id()
        if self.config.user_hash:
            headers["User-Hash"] = self.config.user_hash
        return headers
    
    def _prepare_headers(self, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Подготовка заголовков запроса"""
        headers = self._headers.copy()
        headers = self._add_request_id(headers)
        
        if extra_headers:
            headers.update(extra_headers)
        
        return headers
    
    def _log_request(self, method: str, url: str, params: Optional[Dict] = None):
        """Логирование запроса"""
        self.logger.debug(f"Запрос: {method} {url}")
        if params:
            self.logger.debug(f"Параметры: {params}")
    
    def _log_response(self, response: httpx.Response):
        """Логирование ответа"""
        self.logger.debug(f"Ответ: {response.status_code}")
        if response.headers.get('X-Cache'):
            self.logger.debug(f"Кэш: {response.headers['X-Cache']}")
    
    @abstractmethod
    def get_categories_tree(self, with_duplicates: bool = True) -> CategoriesResponse:
        """
        Получить дерево категорий
        
        Args:
            with_duplicates: Включать дубликаты
            
        Returns:
            Дерево категорий
        """
        pass
    
    @abstractmethod
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
        """
        Получить фильтры
        
        Args:
            category_id: ID категории
            city_id: ID города
            currency: Валюта
            sort_by: Сортировка
            with_filters: Включать фильтры
            with_empty_values: Включать пустые значения
            with_category_counter: Включать счетчики категорий
            parameters: Параметры фильтров
            price_from: Цена от
            price_to: Цена до
            
        Returns:
            Фильтры
        """
        pass
    
    @abstractmethod
    def get_params_filter(
        self,
        category_id: int,
        city_id: Optional[int] = None,
        radius: int = 0,
        location_lat: Optional[float] = None,
        location_lng: Optional[float] = None
    ) -> ParamsFilterResponse:
        """
        Получить параметры фильтров
        
        Args:
            category_id: ID категории
            city_id: ID города
            radius: Радиус поиска
            location_lat: Широта
            location_lng: Долгота
            
        Returns:
            Параметры фильтров
        """
        pass
    
    @abstractmethod
    def get_ad_details(self, ad_id: int) -> AdDetailsResponse:
        """
        Получить детали объявления
        
        Args:
            ad_id: ID объявления
            
        Returns:
            Детали объявления
        """
        pass
    
    @abstractmethod
    def search_ads(self, search_request: SearchRequest) -> SearchResponse:
        """
        Поиск объявлений
        
        Args:
            search_request: Параметры поиска
            
        Returns:
            Результаты поиска
        """
        pass

    @abstractmethod
    def search_ads_all_pages(
        self,
        search_request: SearchRequest,
        max_pages: int = 100,
        delay_between_pages: float = 0.5
    ) -> List[AdCompact]:
        """
        Поиск объявлений по всем страницам
        
        Args:
            search_request: Параметры поиска
            max_pages: Максимальное количество страниц для загрузки
            delay_between_pages: Задержка между запросами (в секундах)
            
        Returns:
            Список всех объявлений
        """
        pass
    
    @abstractmethod
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
        """
        Упрощенный поиск объявлений
        
        Args:
            category_id: ID категории
            city_id: ID города
            q: Текст поиска
            price_from: Цена от
            price_to: Цена до
            page: Страница
            per_page: Количество на странице
            
        Returns:
            Результаты поиска
        """
        pass

    @abstractmethod
    def get_user_ads(
        self,
        user_id: int,
        page: int = 1,
        per_page: int = 40
    ) -> SearchResponse:
        """
        Получить объявления пользователя
        
        Args:
            user_id: ID пользователя
            page: Страница
            per_page: Количество на странице
            
        Returns:
            Объявления пользователя
        """
        pass

    @abstractmethod
    def get_related_ads(
        self,
        ad_id: int,
        category_id: int,
        city_id: int,
        per_page: int = 40,
        vip_count: int = 2
    ) -> SearchResponse:
        """
        Получить похожие объявления
        
        Args:
            ad_id: ID объявления
            category_id: ID категории
            city_id: ID города
            per_page: Количество на странице
            vip_count: Количество VIP объявлений
            
        Returns:
            Похожие объявления
        """
        pass

    @abstractmethod
    def get_feed_elements(self, category_id: int) -> Dict[str, Any]:
        """
        Получить элементы ленты
        
        Args:
            category_id: ID категории
            
        Returns:
            Элементы ленты
        """
        pass

    @abstractmethod
    def get_user_status(self, user_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Получить статус пользователей
        
        Args:
            user_ids: Список ID пользователей
            
        Returns:
            Статусы пользователей
        """
        pass

    @abstractmethod
    def fetch_ad_from_url(self, url: str) -> AdDetailsResponse:
        """
        Получить объявление по его URL
        
        Args:
            url: URL объявления Lalafo
            
        Returns:
            Детали объявления
            
        Raises:
            ValueError: Если URL не является ссылкой на объявление
            APIError: Ошибка API
        """
        pass
        
    @abstractmethod
    def get_search_request_from_url(
            self, url: str,
            currency: Currency = Currency.KGS
        ) -> Optional[SearchRequest]:
        """
        Создает объект SearchRequest из URL поиска Lalafo.
        """
        pass
    
    def validate_category_id(self, category_id: int, categories: Optional[List] = None) -> bool:
        """
        Проверка существования категории
        
        Args:
            category_id: ID категории
            categories: Список категорий (если None, будет загружен)
            
        Returns:
            Существует ли категория
        """
        if not categories:
            response = self.get_categories_tree()
            categories = response.categories
        
        def search_category(cats, target_id):
            for cat in cats:
                if cat.id == target_id:
                    return True
                if cat.children and search_category(cat.children, target_id):
                    return True
            return False
        
        return search_category(categories, category_id)
    
    def get_category_path(self, category_id: int) -> List[str]:
        """
        Получить путь категории
        
        Args:
            category_id: ID категории
            
        Returns:
            Список названий категорий от корня до целевой
        """
        response = self.get_categories_tree()
        
        def find_path(cats, target_id, path):
            for cat in cats:
                new_path = path + [cat.name]
                if cat.id == target_id:
                    return new_path
                if cat.children:
                    result = find_path(cat.children, target_id, new_path)
                    if result:
                        return result
            return None
        
        path = find_path(response.categories, category_id, [])
        return path or []