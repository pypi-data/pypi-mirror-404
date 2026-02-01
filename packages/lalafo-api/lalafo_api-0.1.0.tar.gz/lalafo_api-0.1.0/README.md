# Документация Lalafo API

Этот код был написан в крайне сжатые сроки (буквально за 2 дня). Изначально стоял выбор: потратить месяц на попытку написать «идеально» или быстро «навайбкодить» рабочее решение. Был выбран второй вариант, однако в дальнейшем была проведена работа над ошибками, чтобы исправить структуру и привести библиотеку к нормальной архитектуре.

Библиотека предоставляет удобный интерфейс для взаимодействия с API Lalafo, поддерживая как синхронный, так и асинхронный режимы работы.

Установка: pip install lalafo-api

## Основные возможности
* Синхронный (`LalafoClient`) и асинхронный (`AsyncLalafoClient`) клиенты.
* Полное покрытие моделей данных (объявления, категории, фильтры, пользователи).
* Удобный поиск с поддержкой пагинации и фильтров.
* Инструменты для парсинга данных напрямую из URL сайта Lalafo.
* Автоматическая обработка ошибок API.

## Быстрый старт

### Синхронный клиент
```python
from lalafo import LalafoClient, SearchRequest

client = LalafoClient()

# Поиск объявлений
request = SearchRequest(q="iPhone 15", price_to=100000)
results = client.search_ads(request)

for item in results.items:
    print(f"{item.title} - {item.price} {item.currency}")
```

### Асинхронный клиент
```python
import asyncio
from lalafo import AsyncLalafoClient

async def main():
    client = AsyncLalafoClient()
    ad = await client.get_ad_details(ad_id=12345678)
    print(ad.ad.title)
    print(ad.ad.description)

asyncio.run(main())
```

## Архитектура библиотеки

### 1. Клиенты (api/)
Библиотека использует два основных класса:
* **LalafoClient**: использует `httpx` для блокирующих запросов. Подходит для простых скриптов.
* **AsyncLalafoClient**: использует асинхронный `httpx`. Рекомендуется для ботов и веб-приложений.

Оба клиента поддерживают автоматические повторы запросов (retries) при таймаутах, которые настраиваются через `ClientConfig`.

### 2. Конфигурация (ClientConfig)
Вы можете настроить заголовки, версию приложения и параметры сети:
```python
from lalafo import ClientConfig, LalafoClient

config = ClientConfig(
    timeout=10.0,
    max_retries=5,
    language="ru_RU",
    user_agent="Custom Agent 1.0"
)
client = LalafoClient(config=config)
```

### 3. Поиск и фильтрация (SearchRequest)
Класс `SearchRequest` инкапсулирует все параметры поиска:
* `q`: текстовый запрос.
* `category_id`: ID категории.
* `city_id`: ID города.
* `price_from` / `price_to`: диапазон цен.
* `parameters`: словарь дополнительных параметров.

### 4. Модели данных (models/)
Все ответы API преобразуются в Pydantic-модели. Это дает подсказки в IDE и гарантирует корректность данных.
* **AdCompact**: краткая информация в результатах поиска.
* **AdDetail**: полная информация об объявлении (включая все параметры и статус).
* **Category**: модель дерева категорий.
* **SearchResponse**: содержит список элементов, метаданные пагинации и ссылки на следующую/предыдущую страницы.

### 5. Обработка исключений (exceptions.py)
Библиотека генерирует специфические исключения:
* `APIError`: базовая ошибка сервера.
* `RateLimitError`: (429) превышен лимит запросов.
* `AuthenticationError`: (401) ошибка доступа.
* `NotFoundError`: (404) ресурс не найден.
* `ValidationError`: ошибка во входных данных.

## Утилиты (utils/)

Библиотека умеет превращать обычные ссылки с сайта Lalafo в объекты, понятные коду:

* **fetch_ad_from_url(url)**: принимает ссылку на объявление и возвращает его детали.
* **get_search_request_from_url(url)**: анализирует ссылку поиска на сайте и создает готовый объект `SearchRequest` с примененными фильтрами (работает криво).

Пример:
```python
# Получаем объект запроса из ссылки поиска
request = client.get_search_request_from_url("https://lalafo.kg/bishkek/mobilnye-telefony-i-aksessuary/mobilnye-telefony?price[to]=2000")
# Выполняем поиск по этому запросу
results = client.search_ads(request)
```

## Работа с категориями
Вы можете получить полное дерево категорий и перемещаться по нему:
```python
tree = client.get_categories_tree()

# Поиск категории по ID
category = tree.find_by_id(123)

# Получение плоского списка всех подкатегорий
flat_list = tree.flatten()
```

## Информация о пагинации
`SearchResponse` предоставляет удобный доступ к навигации:
* `response.has_next_page`: есть ли еще результаты.
* `response.meta.totalCount`: общее количество найденных объявлений.
* Метод `search_ads_all_pages` в клиенте позволяет автоматически собрать объявления с нескольких страниц подряд.