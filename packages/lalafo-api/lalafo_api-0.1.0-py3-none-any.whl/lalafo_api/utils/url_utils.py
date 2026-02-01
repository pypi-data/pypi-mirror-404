from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs, unquote
import re

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..models import Cities, CategoriesResponse


def parse_lalafo_url(url: str) -> Dict[str, Any]:
    """
    Парсинг URL объявления Lalafo
    
    Args:
        url: URL объявления
        
    Returns:
        Словарь с разобранными компонентами
    """
    parsed = urlparse(url)
    
    path_parts = parsed.path.strip('/').split('/')
    ad_id = None
    
    for part in path_parts:
        if part.startswith('id-'):
            ad_id = int(part.split('-')[-1])
            break
    
    city_alias = path_parts[0] if path_parts else None
    
    return {
        'ad_id': ad_id,
        'city_alias': city_alias,
        'full_url': url,
        'domain': parsed.netloc
    }


def get_image_url(image_path: str, size: str = "original") -> str:
    """
    Получение URL изображения
    
    Args:
        image_path: Путь к изображению (например, "/38/1b/7c/filename.jpg")
        size: Размер (original, thumbnail, api)
        
    Returns:
        Полный URL изображения
    """
    base_url = "https://img5.lalafo.com/i/posters"
    
    if size == "original":
        return f"{base_url}/original{image_path}"
    elif size == "thumbnail" or size == "api":
        return f"{base_url}/api{image_path}"
    else:
        return f"{base_url}/{size}{image_path}"


from urllib.parse import urlparse, parse_qs, unquote
from typing import Dict, Any, Optional, Tuple
import re

def parse_ad_url(url: str) -> Optional[Dict[str, Any]]:
    """
    Парсит URL объявления Lalafo и извлекает параметры
    
    Args:
        url: URL объявления (например, https://lalafo.kg/bishkek/ads/mobilnyj-telefon-nokia-...)
        
    Returns:
        Словарь с параметрами или None если URL не валиден
    """
    try:
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        ad_id = None
        for part in path_parts:
            if part.startswith('id-'):
                ad_id = int(part.split('-')[-1])
                break
        
        if not ad_id:
            match = re.search(r'id-(\d+)', url)
            if match:
                ad_id = int(match.group(1))
        
        if not ad_id:
            return None
        
        query_params = parse_qs(parsed.query)
        
        simple_params = {}
        for key, value in query_params.items():
            if value and len(value) == 1:
                simple_params[key] = value[0]
            else:
                simple_params[key] = value
        
        return {
            'ad_id': ad_id,
            'city_alias': path_parts[0] if path_parts else None,
            'url_type': 'ad',
            'query_params': simple_params
        }
        
    except Exception as e:
        return None


def parse_search_url(url: str, cities: "Cities", categories: "CategoriesResponse") -> Optional[Dict[str, Any]]:
    """
    Парсит URL поиска Lalafo и извлекает параметры
    
    Args:
        url: URL поиска (например, https://lalafo.kg/kyrgyzstan/mobilnye-telefony-i-aksessuary/...)
        
    Returns:
        Словарь с параметрами для SearchRequest
    """
    try:
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        city_alias = path_parts[0] if path_parts else None
        city = cities.get_city_by_alias(city_alias)
        city_id = None
        if city:
            city_id = city.id
        
        category_id = None
        for part in path_parts[:0:-1]:
            category = categories.find_by_alias(part)
            if category:
                category_id = category[0].id
                break
        
        query_params = parse_qs(parsed.query)
        
        search_params = {}
        
        if "q-" in path_parts[-1]:
            search_params['q'] = path_parts[-1].replace("q-", "")
        
        if 'price[from]' in query_params:
            try:
                search_params['price_from'] = int(query_params['price[from]'][0])
            except (ValueError, TypeError):
                pass
        
        if 'price[to]' in query_params:
            try:
                search_params['price_to'] = int(query_params['price[to]'][0])
            except (ValueError, TypeError):
                pass
        
        if 'page' in query_params:
            try:
                search_params['page'] = int(query_params['page'][0])
            except (ValueError, TypeError):
                pass
        
        if 'per-page' in query_params:
            try:
                search_params['per_page'] = int(query_params['per-page'][0])
            except (ValueError, TypeError):
                pass
        
        if 'listing_category_id' in query_params:
            try:
                category_id = int(query_params['listing_category_id'][0])
            except (ValueError, TypeError):
                pass
        
        if category_id:
            search_params['category_id'] = category_id
        
        if city_id:
            search_params['city_id'] = city_id
        
        return search_params
        
    except Exception as e:
        return None


def is_ad_url(url: str) -> bool:
    """Проверяет, является ли URL ссылкой на объявление"""
    patterns = [
        r'/ads/',
        r'id-\d+',
        r'/item/',
    ]
    
    for pattern in patterns:
        if re.search(pattern, url):
            return True
    return False


def is_search_url(url: str) -> bool:
    """Проверяет, является ли URL ссылкой на поиск"""
    patterns = [
        r'/category/',
        r'/search\?',
        r'\?q=',
        r'\?price\[from\]=',
    ]
    
    for pattern in patterns:
        if re.search(pattern, url):
            return True
    
    parsed = urlparse(url)
    path = parsed.path
    if path and not is_ad_url(url):
        if parsed.query:
            return True
        if len(path.strip('/').split('/')) > 1:
            return True
    
    return False