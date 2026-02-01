from typing import Optional, Dict, Any


class LalafoError(Exception):
    """Базовое исключение для всей библиотеки"""
    pass


class APIError(LalafoError):
    """Ошибки, прилетевшие от сервера (4xx, 5xx)"""
    
    def __init__(self, message: str, status_code: int, response_data: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        self.message = message
        self.response_data = response_data
        super().__init__(f"Ошибка API ({status_code}): {message}")


class ValidationError(LalafoError):
    """Ошибка валидации входных параметров"""
    pass


class RateLimitError(APIError):
    """Превышен лимит запросов"""
    pass


class AuthenticationError(APIError):
    """Ошибка аутентификации"""
    pass


class NotFoundError(APIError):
    """Ресурс не найден"""
    pass