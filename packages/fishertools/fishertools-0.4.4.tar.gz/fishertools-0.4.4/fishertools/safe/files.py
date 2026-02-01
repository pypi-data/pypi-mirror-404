"""
Safe file operations for beginners.

This module provides safe file handling utilities that prevent common
file-related errors and provide helpful error messages.
"""

import os
from pathlib import Path
from typing import Union, Optional, List


def safe_read_file(filepath: Union[str, Path], encoding: str = 'utf-8', default: str = '') -> str:
    """
    Safely read a file with comprehensive error handling.
    
    Предотвращает ошибки FileNotFoundError, PermissionError и UnicodeDecodeError,
    возвращая значение по умолчанию вместо исключения.
    
    Args:
        filepath: Путь к файлу (строка или Path объект)
        encoding: Кодировка файла (по умолчанию utf-8)
        default: Значение по умолчанию при ошибке чтения
        
    Returns:
        Содержимое файла или значение по умолчанию
        
    Raises:
        SafeUtilityError: If filepath is None or invalid type
        
    Examples:
        >>> safe_read_file("example.txt")
        'содержимое файла'
        >>> safe_read_file("несуществующий.txt", default="файл не найден")
        'файл не найден'
    """
    from ..errors.exceptions import SafeUtilityError
    
    if filepath is None:
        raise SafeUtilityError("Путь к файлу не может быть None", utility_name="safe_read_file")
    
    if not isinstance(filepath, (str, Path)):
        raise SafeUtilityError(f"Путь к файлу должен быть строкой или Path объектом, получен {type(filepath).__name__}", 
                             utility_name="safe_read_file")
    
    if not isinstance(encoding, str):
        raise SafeUtilityError(f"Кодировка должна быть строкой, получен {type(encoding).__name__}", 
                             utility_name="safe_read_file")
    
    try:
        with open(filepath, 'r', encoding=encoding) as file:
            return file.read()
    except FileNotFoundError:
        return default
    except PermissionError:
        return default
    except UnicodeDecodeError:
        return default
    except OSError:
        # Covers other OS-related errors
        return default


def safe_write_file(filepath: Union[str, Path], content: str, encoding: str = 'utf-8', 
                   create_dirs: bool = True) -> bool:
    """
    Safely write content to a file with error handling.
    
    Предотвращает ошибки при записи файла и может создавать директории.
    
    Args:
        filepath: Путь к файлу
        content: Содержимое для записи
        encoding: Кодировка файла
        create_dirs: Создавать ли директории если они не существуют
        
    Returns:
        True если запись успешна, False при ошибке
        
    Raises:
        SafeUtilityError: If arguments have invalid types
        
    Examples:
        >>> safe_write_file("output.txt", "Hello World")
        True
        >>> safe_write_file("/invalid/path/file.txt", "content", create_dirs=False)
        False
    """
    from ..errors.exceptions import SafeUtilityError
    
    if filepath is None:
        raise SafeUtilityError("Путь к файлу не может быть None", utility_name="safe_write_file")
    
    if not isinstance(filepath, (str, Path)):
        raise SafeUtilityError(f"Путь к файлу должен быть строкой или Path объектом, получен {type(filepath).__name__}", 
                             utility_name="safe_write_file")
    
    if not isinstance(content, str):
        raise SafeUtilityError(f"Содержимое должно быть строкой, получен {type(content).__name__}", 
                             utility_name="safe_write_file")
    
    if not isinstance(encoding, str):
        raise SafeUtilityError(f"Кодировка должна быть строкой, получен {type(encoding).__name__}", 
                             utility_name="safe_write_file")
    
    try:
        filepath = Path(filepath)
        
        # Create directories if requested
        if create_dirs and filepath.parent != filepath:
            filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding=encoding) as file:
            file.write(content)
        return True
    except (PermissionError, OSError, UnicodeEncodeError):
        return False


def safe_file_exists(filepath: Union[str, Path]) -> bool:
    """
    Safely check if a file exists.
    
    Предотвращает ошибки при проверке существования файла.
    
    Args:
        filepath: Путь к файлу
        
    Returns:
        True если файл существует, False иначе
        
    Raises:
        SafeUtilityError: If filepath is None or invalid type
        
    Examples:
        >>> safe_file_exists("example.txt")
        True
        >>> safe_file_exists("несуществующий.txt")
        False
    """
    from ..errors.exceptions import SafeUtilityError
    
    if filepath is None:
        raise SafeUtilityError("Путь к файлу не может быть None", utility_name="safe_file_exists")
    
    if not isinstance(filepath, (str, Path)):
        raise SafeUtilityError(f"Путь к файлу должен быть строкой или Path объектом, получен {type(filepath).__name__}", 
                             utility_name="safe_file_exists")
    
    try:
        return Path(filepath).exists() and Path(filepath).is_file()
    except (OSError, ValueError):
        return False


def safe_get_file_size(filepath: Union[str, Path], default: int = 0) -> int:
    """
    Safely get file size in bytes.
    
    Предотвращает ошибки при получении размера файла.
    
    Args:
        filepath: Путь к файлу
        default: Значение по умолчанию при ошибке
        
    Returns:
        Размер файла в байтах или значение по умолчанию
        
    Raises:
        SafeUtilityError: If filepath is None or invalid type
        
    Examples:
        >>> safe_get_file_size("example.txt")
        1024
        >>> safe_get_file_size("несуществующий.txt")
        0
    """
    from ..errors.exceptions import SafeUtilityError
    
    if filepath is None:
        raise SafeUtilityError("Путь к файлу не может быть None", utility_name="safe_get_file_size")
    
    if not isinstance(filepath, (str, Path)):
        raise SafeUtilityError(f"Путь к файлу должен быть строкой или Path объектом, получен {type(filepath).__name__}", 
                             utility_name="safe_get_file_size")
    
    try:
        return Path(filepath).stat().st_size
    except (OSError, FileNotFoundError):
        return default


def safe_list_files(directory: Union[str, Path], pattern: str = "*", default: Optional[List[str]] = None) -> List[str]:
    """
    Safely list files in a directory.
    
    Предотвращает ошибки при чтении содержимого директории.
    
    Args:
        directory: Путь к директории
        pattern: Паттерн для фильтрации файлов (например, "*.txt")
        default: Значение по умолчанию при ошибке
        
    Returns:
        Список имен файлов или значение по умолчанию
        
    Raises:
        SafeUtilityError: If directory is None or invalid type
        
    Examples:
        >>> safe_list_files(".")
        ['file1.txt', 'file2.py']
        >>> safe_list_files("несуществующая_папка")
        []
    """
    from ..errors.exceptions import SafeUtilityError
    
    if default is None:
        default = []
    
    if directory is None:
        raise SafeUtilityError("Путь к директории не может быть None", utility_name="safe_list_files")
    
    if not isinstance(directory, (str, Path)):
        raise SafeUtilityError(f"Путь к директории должен быть строкой или Path объектом, получен {type(directory).__name__}", 
                             utility_name="safe_list_files")
    
    if not isinstance(pattern, str):
        raise SafeUtilityError(f"Паттерн должен быть строкой, получен {type(pattern).__name__}", 
                             utility_name="safe_list_files")
    
    try:
        directory_path = Path(directory)
        if not directory_path.exists() or not directory_path.is_dir():
            return default
        
        files = [f.name for f in directory_path.glob(pattern) if f.is_file()]
        return sorted(files)
    except (OSError, ValueError):
        return default



def project_root(start_dir: Optional[Union[str, Path]] = None) -> str:
    """
    Detect and return the project root directory.
    
    Looks for markers: setup.py, pyproject.toml, .git, .gitignore
    
    Args:
        start_dir: Starting directory (default: current directory)
        
    Returns:
        Path to project root
        
    Raises:
        RuntimeError: If project root cannot be determined
        
    Examples:
        >>> root = project_root()
        >>> root = project_root("/path/to/subdir")
    """
    if start_dir is None:
        start_dir = Path.cwd()
    else:
        start_dir = Path(start_dir)
    
    # Markers that indicate project root
    markers = ['setup.py', 'pyproject.toml', '.git', '.gitignore']
    
    current = start_dir.resolve()
    
    # Walk up the directory tree
    while True:
        # Check if any marker exists in current directory
        for marker in markers:
            if (current / marker).exists():
                return str(current)
        
        # Move to parent directory
        parent = current.parent
        if parent == current:
            # Reached filesystem root without finding project root
            raise RuntimeError(f"Could not determine project root starting from {start_dir}")
        
        current = parent


def find_file(filename: str, start_dir: Optional[Union[str, Path]] = None) -> Optional[str]:
    """
    Search for a file in the project directory tree.
    
    Args:
        filename: Name of file to find
        start_dir: Starting directory (default: project root)
        
    Returns:
        Full path to file if found, None otherwise
        
    Examples:
        >>> path = find_file("setup.py")
        >>> path = find_file("config.json", "/path/to/start")
    """
    if start_dir is None:
        try:
            start_dir = project_root()
        except RuntimeError:
            start_dir = Path.cwd()
    else:
        start_dir = Path(start_dir)
    
    start_dir = Path(start_dir).resolve()
    
    # Search for the file
    for path in start_dir.rglob(filename):
        if path.is_file():
            return str(path)
    
    return None


def safe_open(filepath: Union[str, Path], mode: str = 'r', encoding: str = 'utf-8'):
    """
    Safely open a file with helpful error messages.
    
    Args:
        filepath: Path to file (relative or absolute)
        mode: File open mode ('r', 'w', 'a', etc.)
        encoding: Text encoding (default: utf-8)
        
    Returns:
        File object
        
    Raises:
        FileNotFoundError: With helpful suggestions if file not found
        PermissionError: With helpful suggestions if permission denied
        
    Examples:
        >>> with safe_open("data.txt") as f:
        ...     content = f.read()
    """
    from ..errors.exceptions import SafeUtilityError
    
    filepath = Path(filepath)
    
    # If relative path, try to resolve relative to project root
    if not filepath.is_absolute():
        try:
            root = project_root()
            filepath = Path(root) / filepath
        except RuntimeError:
            # If project root not found, use as-is
            pass
    
    try:
        return open(filepath, mode, encoding=encoding)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"File not found: {filepath}") from e
    except PermissionError as e:
        raise PermissionError(f"Permission denied: {filepath}") from e



# ============================================================================
# New file utility functions for fishertools-file-utils spec
# ============================================================================

import hashlib


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Создаёт директорию рекурсивно, как os.makedirs с exist_ok=True.
    
    Args:
        path: Путь к директории (str или Path).
    
    Returns:
        Path: Объект pathlib.Path созданной директории.
    
    Raises:
        OSError: Если директория не может быть создана.
        PermissionError: Если нет прав доступа.
        
    Examples:
        >>> ensure_dir("/path/to/directory")
        PosixPath('/path/to/directory')
        >>> ensure_dir("./nested/dir/structure")
        PosixPath('./nested/dir/structure')
    """
    try:
        path_obj = Path(path)
        path_obj.mkdir(parents=True, exist_ok=True)
        return path_obj
    except PermissionError as e:
        raise PermissionError(f"Permission denied creating directory: {path}") from e
    except OSError as e:
        raise OSError(f"Failed to create directory: {path}") from e


def get_file_hash(
    file_path: Union[str, Path],
    algorithm: str = 'sha256'
) -> str:
    """
    Вычисляет хэш файла потоковым методом (8KB чанки).
    
    Args:
        file_path: Путь к файлу (str или Path).
        algorithm: Алгоритм хэширования (md5, sha1, sha256, sha512, blake2b).
    
    Returns:
        str: Хэш файла в hex формате.
    
    Raises:
        FileNotFoundError: Если файл не существует.
        ValueError: Если алгоритм не поддерживается.
        PermissionError: Если нет прав доступа на чтение.
        
    Examples:
        >>> get_file_hash("data.txt")
        'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
        >>> get_file_hash("data.txt", algorithm='md5')
        'd41d8cd98f00b204e9800998ecf8427e'
    """
    # Supported algorithms
    supported_algorithms = {'md5', 'sha1', 'sha256', 'sha512', 'blake2b'}
    
    # Validate algorithm
    if algorithm not in supported_algorithms:
        raise ValueError(
            f"Unsupported algorithm: {algorithm}. "
            f"Supported algorithms: {', '.join(sorted(supported_algorithms))}"
        )
    
    # Convert to Path object
    file_path_obj = Path(file_path)
    
    # Check if file exists
    if not file_path_obj.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Create hash object
    if algorithm == 'blake2b':
        hash_obj = hashlib.blake2b()
    else:
        hash_obj = hashlib.new(algorithm)
    
    # Read file in chunks and update hash
    chunk_size = 8192  # 8KB chunks
    try:
        with open(file_path_obj, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                hash_obj.update(chunk)
    except PermissionError as e:
        raise PermissionError(f"Permission denied reading file: {file_path}") from e
    except OSError as e:
        raise OSError(f"Error reading file: {file_path}") from e
    
    return hash_obj.hexdigest()


def read_last_lines(
    file_path: Union[str, Path],
    n: int = 10
) -> List[str]:
    """
    Читает последние N строк файла буферным алгоритмом от конца.
    
    Args:
        file_path: Путь к файлу (str или Path).
        n: Количество строк для чтения (по умолчанию 10).
    
    Returns:
        List[str]: Список последних N строк без символов новой строки.
    
    Raises:
        FileNotFoundError: Если файл не существует.
        PermissionError: Если нет прав доступа на чтение.
        
    Examples:
        >>> read_last_lines("log.txt", n=5)
        ['line 1', 'line 2', 'line 3', 'line 4', 'line 5']
        >>> read_last_lines("data.txt")
        ['last line']
    """
    # Convert to Path object
    file_path_obj = Path(file_path)
    
    # Check if file exists
    if not file_path_obj.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        with open(file_path_obj, 'rb') as f:
            # Get file size
            f.seek(0, 2)  # Seek to end
            file_size = f.tell()
            
            # If file is empty, return empty list
            if file_size == 0:
                return []
            
            # Buffer for reading from end
            buffer_size = 8192  # 8KB buffer
            lines = []
            position = file_size
            
            # Read file from end in chunks
            while position > 0 and len(lines) < n:
                # Calculate how much to read
                read_size = min(buffer_size, position)
                position -= read_size
                
                # Seek and read
                f.seek(position)
                chunk = f.read(read_size)
                
                # Decode chunk
                try:
                    text = chunk.decode('utf-8')
                except UnicodeDecodeError:
                    # Try with latin-1 as fallback
                    text = chunk.decode('latin-1', errors='replace')
                
                # Split by newlines and process
                chunk_lines = text.split('\n')
                
                # If we're not at the start of file, the first line is incomplete
                if position > 0:
                    # Keep the incomplete line for next iteration
                    incomplete_line = chunk_lines[0]
                    chunk_lines = chunk_lines[1:]
                else:
                    # At start of file, all lines are complete
                    incomplete_line = None
                
                # Add lines in reverse order (we're reading backwards)
                for line in reversed(chunk_lines):
                    if line or lines:  # Skip empty lines at the end
                        lines.insert(0, line)
                        if len(lines) >= n:
                            break
                
                # If we're at the start and have incomplete line, add it
                if position == 0 and incomplete_line:
                    lines.insert(0, incomplete_line)
            
            # Clean up: remove empty lines at the end and limit to n
            result = []
            for line in lines:
                # Strip newline characters
                cleaned = line.rstrip('\r\n')
                result.append(cleaned)
            
            # Return only the last n lines
            return result[-n:] if len(result) > n else result
    
    except PermissionError as e:
        raise PermissionError(f"Permission denied reading file: {file_path}") from e
    except OSError as e:
        raise OSError(f"Error reading file: {file_path}") from e


__all__ = ['ensure_dir', 'get_file_hash', 'read_last_lines']
