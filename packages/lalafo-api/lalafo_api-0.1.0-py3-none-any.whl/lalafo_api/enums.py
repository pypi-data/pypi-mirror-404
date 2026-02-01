from enum import Enum


class Currency(str, Enum):
    """Валюта"""
    KGS = "KGS"
    USD = "USD"
    EUR = "EUR"
    RUB = "RUB"


class SortBy(str, Enum):
    """Типы сортировки"""
    DEFAULT = "default"
    NEWEST = "newest"
    PRICE_ASC = "price"
    PRICE_DESC = "-price"
    DISTANCE = "distance"


class FilterKind(str, Enum):
    """Типы фильтров"""
    LOCATION = "location"
    DROPDOWN = "dropdown"
    SLIDER = "slider"
    PRICE = "price"
    CURRENCY = "currency"
    SORT_BY = "sort_by"
    INPUT = "input"


class AdStatus(int, Enum):
    """Статусы объявлений"""
    MODERATION = 1
    ACTIVE = 2
    SOLD = 3
    DELETED = 4
    BLOCKED = 5
    DRAFT = 6