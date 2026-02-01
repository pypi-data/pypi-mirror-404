"""
Утилиты для работы с файлами, данными и другими частыми задачами
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


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