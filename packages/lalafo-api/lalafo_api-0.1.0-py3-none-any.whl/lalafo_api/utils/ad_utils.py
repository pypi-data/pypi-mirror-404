from typing import List, Dict


def calculate_discount_percent(price: int, old_price: int) -> int:
    """
    Расчет процента скидки
    
    Args:
        price: Текущая цена
        old_price: Старая цена
        
    Returns:
        Процент скидки
    """
    if old_price <= 0:
        return 0
    
    discount = ((old_price - price) / old_price) * 100
    return int(discount)


def filter_ads_by_price(ads: List[Dict], min_price: int, max_price: int) -> List[Dict]:
    """
    Фильтрация объявлений по цене
    
    Args:
        ads: Список объявлений
        min_price: Минимальная цена
        max_price: Максимальная цена
        
    Returns:
        Отфильтрованные объявления
    """
    filtered = []
    
    for ad in ads:
        price = ad.get('price', 0)
        if min_price <= price <= max_price:
            filtered.append(ad)
    
    return filtered


def group_ads_by_category(ads: List[Dict]) -> Dict[int, List[Dict]]:
    """
    Группировка объявлений по категориям
    
    Args:
        ads: Список объявлений
        
    Returns:
        Словарь {category_id: [ads]}
    """
    grouped = {}
    
    for ad in ads:
        category_id = ad.get('category_id')
        if category_id not in grouped:
            grouped[category_id] = []
        grouped[category_id].append(ad)
    
    return grouped