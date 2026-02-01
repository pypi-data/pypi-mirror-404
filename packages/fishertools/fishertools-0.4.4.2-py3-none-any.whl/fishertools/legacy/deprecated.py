"""
Deprecated functions from original fishertools library

These functions are retained for backward compatibility and align with the new
mission of making Python more convenient and safer for beginners. All functions
maintain identical behavior to the original implementation.
"""

import json
import os
import time
import re
import hashlib
import random
import string
import functools
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable


# File and directory utilities - helpful for beginners
def read_json(filepath: str) -> Dict[str, Any]:
    """Читает JSON файл и возвращает словарь"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_json(data: Dict[str, Any], filepath: str, indent: int = 2) -> None:
    """Записывает данные в JSON файл"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def ensure_dir(path: str) -> None:
    """Создает директорию если она не существует"""
    Path(path).mkdir(parents=True, exist_ok=True)


def get_file_size(filepath: str) -> int:
    """Возвращает размер файла в байтах"""
    return os.path.getsize(filepath)


def list_files(directory: str, extension: Optional[str] = None) -> List[str]:
    """Возвращает список файлов в директории с опциональной фильтрацией по расширению"""
    path = Path(directory)
    if extension:
        pattern = f"*.{extension.lstrip('.')}"
        return [str(f) for f in path.glob(pattern)]
    return [str(f) for f in path.iterdir() if f.is_file()]


def timestamp() -> str:
    """Возвращает текущую временную метку в читаемом формате"""
    return time.strftime("%Y-%m-%d %H:%M:%S")


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Превращает вложенный словарь в плоский"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


# String utilities - common beginner needs
def validate_email(email: str) -> bool:
    """Проверяет корректность email адреса"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def clean_string(text: str) -> str:
    """Очищает строку от лишних пробелов и символов"""
    # Убираем лишние пробелы
    text = re.sub(r'\s+', ' ', text.strip())
    # Убираем специальные символы (оставляем только буквы, цифры, пробелы и основную пунктуацию)
    text = re.sub(r'[^\w\s.,!?-]', '', text)
    return text


# Data utilities - safe operations for beginners
def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Разбивает список на части заданного размера"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Объединяет несколько словарей в один"""
    result = {}
    for d in dicts:
        result.update(d)
    return result


# Security utilities - helpful for beginners
def generate_password(length: int = 12, include_symbols: bool = True) -> str:
    """Генерирует случайный пароль"""
    chars = string.ascii_letters + string.digits
    if include_symbols:
        chars += "!@#$%^&*"
    
    return ''.join(random.choice(chars) for _ in range(length))


def hash_string(text: str, algorithm: str = 'sha256') -> str:
    """Хеширует строку указанным алгоритмом"""
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(text.encode('utf-8'))
    return hash_obj.hexdigest()


# Helper classes - simplified for beginners
class QuickConfig:
    """Простой класс для работы с конфигурацией"""
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        self._config = config_dict or {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Получить значение по ключу с поддержкой точечной нотации"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Установить значение по ключу с поддержкой точечной нотации"""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Вернуть конфигурацию как словарь"""
        return self._config.copy()


class SimpleLogger:
    """Простой логгер для быстрой отладки"""
    
    def __init__(self, name: str = "MyDevTools"):
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


# Educational decorators - help beginners understand code behavior
def timer(func: Callable) -> Callable:
    """Декоратор для измерения времени выполнения функции"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} выполнилась за {end_time - start_time:.4f} секунд")
        return result
    return wrapper


def debug(func: Callable) -> Callable:
    """Декоратор для отладки - выводит аргументы и результат функции"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Вызов {func.__name__} с аргументами: args={args}, kwargs={kwargs}")
        result = func(*args, **kwargs)
        print(f"{func.__name__} вернула: {result}")
        return result
    return wrapper


def retry(max_attempts: int = 3, delay: float = 1.0):
    """Декоратор для повторных попыток выполнения функции при ошибке"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise e
                    print(f"Попытка {attempt + 1} не удалась: {e}. Повтор через {delay} сек...")
                    time.sleep(delay)
        return wrapper
    return decorator


def cache_result(func: Callable) -> Callable:
    """Простой декоратор для кеширования результатов функции"""
    cache = {}
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Создаем ключ из аргументов
        key = str(args) + str(sorted(kwargs.items()))
        
        if key in cache:
            print(f"Результат {func.__name__} взят из кеша")
            return cache[key]
        
        result = func(*args, **kwargs)
        cache[key] = result
        return result
    
    return wrapper


def validate_types(**expected_types):
    """Декоратор для проверки типов аргументов функции"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Получаем имена параметров функции
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Проверяем типы
            for param_name, expected_type in expected_types.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if not isinstance(value, expected_type):
                        raise TypeError(
                            f"Параметр '{param_name}' должен быть типа {expected_type.__name__}, "
                            f"получен {type(value).__name__}"
                        )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator