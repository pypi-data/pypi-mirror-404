"""
Помощники для частых задач разработки
"""

import re
import hashlib
import random
import string
from typing import List, Dict, Any, Optional

# Компилируем регулярные выражения один раз для производительности
_WHITESPACE_PATTERN = re.compile(r'\s+')
_SPECIAL_CHARS_PATTERN = re.compile(r'[^\w\s.,!?-]')
_EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


class QuickConfig:
    """Простой класс для работы с конфигурацией"""
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None) -> None:
        self._config: Dict[str, Any] = config_dict or {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Получить значение по ключу с поддержкой точечной нотации"""
        keys = key.split('.')
        value: Any = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Установить значение по ключу с поддержкой точечной нотации"""
        keys = key.split('.')
        config: Dict[str, Any] = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Вернуть конфигурацию как словарь"""
        return self._config.copy()


def generate_password(length: int = 12, include_symbols: bool = True) -> str:
    """
    Генерирует случайный пароль.
    
    Args:
        length: Длина пароля (по умолчанию 12)
        include_symbols: Включать ли специальные символы
        
    Returns:
        Случайно сгенерированный пароль
        
    Raises:
        ValueError: Если length < 1
    """
    if length < 1:
        raise ValueError("Password length must be at least 1")
    
    chars = string.ascii_letters + string.digits
    if include_symbols:
        chars += "!@#$%^&*"
    
    return ''.join(random.choice(chars) for _ in range(length))


def hash_string(text: str, algorithm: str = 'sha256') -> str:
    """
    Хеширует строку указанным алгоритмом.
    
    Args:
        text: Строка для хеширования
        algorithm: Алгоритм хеширования (sha256, md5, sha1, sha512)
        
    Returns:
        Хеш в виде hex-строки
        
    Raises:
        ValueError: Если алгоритм не поддерживается
    """
    try:
        hash_obj = hashlib.new(algorithm)
        hash_obj.update(text.encode('utf-8'))
        return hash_obj.hexdigest()
    except ValueError as e:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}") from e


def validate_email(email: Optional[str]) -> bool:
    """
    Проверяет корректность email адреса.
    
    Args:
        email: Email адрес для проверки
        
    Returns:
        True если email валиден, False иначе
    """
    if not email:
        return False
    
    try:
        return bool(_EMAIL_PATTERN.match(email))
    except (TypeError, AttributeError):
        return False


def clean_string(text: Optional[str], default: str = '') -> str:
    """
    Очищает строку от лишних пробелов и символов.
    
    Args:
        text: Строка для очистки
        default: Значение по умолчанию если text is None
        
    Returns:
        Очищенная строка
    """
    if text is None:
        return default
    
    try:
        # Убираем лишние пробелы (используем предкомпилированный паттерн)
        text = _WHITESPACE_PATTERN.sub(' ', str(text).strip())
        # Убираем специальные символы
        text = _SPECIAL_CHARS_PATTERN.sub('', text)
        return text
    except (TypeError, AttributeError):
        return default


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Разбивает список на части заданного размера.
    
    Args:
        lst: Список для разбиения
        chunk_size: Размер каждой части
        
    Returns:
        Список списков (chunks)
        
    Raises:
        ValueError: Если chunk_size < 1
    """
    if chunk_size < 1:
        raise ValueError("Chunk size must be at least 1")
    
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Объединяет несколько словарей в один.
    
    Args:
        *dicts: Словари для объединения
        
    Returns:
        Объединенный словарь (последующие значения перезаписывают предыдущие)
    """
    result: Dict[str, Any] = {}
    for d in dicts:
        result.update(d)
    return result


class SimpleLogger:
    """Простой логгер для быстрой отладки"""
    
    def __init__(self, name: str = "MyDevTools") -> None:
        self.name = name
    
    def info(self, message: str) -> None:
        """Информационное сообщение"""
        print(f"[{self.name}] INFO: {message}")
    
    def warning(self, message: str) -> None:
        """Предупреждение"""
        print(f"[{self.name}] WARNING: {message}")
    
    def error(self, message: str) -> None:
        """Ошибка"""
        print(f"[{self.name}] ERROR: {message}")
    
    def debug(self, message: str) -> None:
        """Отладочное сообщение"""
        print(f"[{self.name}] DEBUG: {message}")


# Создаем глобальный экземпляр логгера
logger = SimpleLogger()
