"""
Полезные декораторы для отладки, профилирования и других задач
"""

import time
import functools
from typing import Any, Callable, TypeVar, ParamSpec

P = ParamSpec('P')
R = TypeVar('R')


def timer(func: Callable[P, R]) -> Callable[P, R]:
    """Декоратор для измерения времени выполнения функции"""
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start_time = time.time()
        result: R = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} выполнилась за {end_time - start_time:.4f} секунд")
        return result
    return wrapper


def debug(func: Callable[P, R]) -> Callable[P, R]:
    """Декоратор для отладки - выводит аргументы и результат функции"""
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"Вызов {func.__name__} с аргументами: args={args}, kwargs={kwargs}")
        result: R = func(*args, **kwargs)
        print(f"{func.__name__} вернула: {result}")
        return result
    return wrapper


def retry(max_attempts: int = 3, delay: float = 1.0) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Декоратор для повторных попыток выполнения функции при ошибке"""
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise e
                    print(f"Попытка {attempt + 1} не удалась: {e}. Повтор через {delay} сек...")
                    time.sleep(delay)
            # This line should never be reached, but added for type safety
            raise RuntimeError("Unexpected error in retry decorator")
        return wrapper
    return decorator


def cache_result(func: Callable[P, R]) -> Callable[P, R]:
    """Простой декоратор для кеширования результатов функции"""
    cache: dict[str, R] = {}
    
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        # Создаем ключ из аргументов
        key = str(args) + str(sorted(kwargs.items()))
        
        if key in cache:
            print(f"Результат {func.__name__} взят из кеша")
            return cache[key]
        
        result: R = func(*args, **kwargs)
        cache[key] = result
        return result
    
    return wrapper


def validate_types(**expected_types: type) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Декоратор для проверки типов аргументов функции"""
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
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
