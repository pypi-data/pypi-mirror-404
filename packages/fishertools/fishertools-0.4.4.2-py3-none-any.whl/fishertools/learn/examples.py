"""
Code example generation for learning.

This module contains functions to generate educational code examples
for common Python concepts that beginners need to learn.
"""

import json
import os
from typing import Dict, Optional


# Database of code examples for different Python concepts
CODE_EXAMPLES: Dict[str, Dict[str, str]] = {
    "variables": {
        "title": "Переменные и типы данных",
        "description": "Основы работы с переменными в Python",
        "code": '''# Основные типы данных в Python

# Строки (str)
name = "Анна"
message = 'Привет, мир!'
multiline = """Это многострочная
строка в Python"""

# Числа
age = 25                    # Целое число (int)
height = 1.75              # Число с плавающей точкой (float)
temperature = -5.5         # Отрицательное число

# Логические значения (bool)
is_student = True
is_working = False

# Вывод информации о переменных
print(f"Имя: {name}, тип: {type(name)}")
print(f"Возраст: {age}, тип: {type(age)}")
print(f"Рост: {height}, тип: {type(height)}")
print(f"Студент: {is_student}, тип: {type(is_student)}")

# Преобразование типов
age_str = str(age)         # Число в строку
height_int = int(height)   # Дробное в целое (обрезает дробную часть)
number_from_str = int("42") # Строка в число

print(f"Возраст как строка: '{age_str}'")
print(f"Рост как целое: {height_int}")
print(f"Число из строки: {number_from_str}")'''
    },
    
    "lists": {
        "title": "Списки и операции с ними",
        "description": "Работа со списками - основной структурой данных Python",
        "code": '''# Создание и работа со списками

# Создание списков
fruits = ["яблоко", "банан", "апельсин"]
numbers = [1, 2, 3, 4, 5]
mixed_list = ["текст", 42, True, 3.14]
empty_list = []

print("Исходный список фруктов:", fruits)

# Доступ к элементам (индексация начинается с 0)
first_fruit = fruits[0]      # Первый элемент
last_fruit = fruits[-1]      # Последний элемент
print(f"Первый фрукт: {first_fruit}")
print(f"Последний фрукт: {last_fruit}")

# Добавление элементов
fruits.append("груша")       # Добавить в конец
fruits.insert(1, "киви")     # Вставить на позицию 1
print("После добавления:", fruits)

# Удаление элементов
fruits.remove("банан")       # Удалить по значению
removed_fruit = fruits.pop() # Удалить и вернуть последний элемент
print(f"Удален фрукт: {removed_fruit}")
print("После удаления:", fruits)

# Полезные операции
print(f"Количество фруктов: {len(fruits)}")
print(f"Есть ли яблоко: {'яблоко' in fruits}")

# Срезы (slicing)
first_two = fruits[:2]       # Первые два элемента
last_two = fruits[-2:]       # Последние два элемента
print(f"Первые два: {first_two}")
print(f"Последние два: {last_two}")

# Итерация по списку
print("Все фрукты:")
for i, fruit in enumerate(fruits):
    print(f"{i + 1}. {fruit}")'''
    },
    
    "dictionaries": {
        "title": "Словари для хранения данных",
        "description": "Словари позволяют хранить данные в формате ключ-значение",
        "code": '''# Создание и работа со словарями

# Создание словаря
student = {
    "name": "Алексей",
    "age": 20,
    "course": 2,
    "subjects": ["математика", "физика", "программирование"]
}

print("Информация о студенте:")
print(student)

# Доступ к значениям
student_name = student["name"]           # Прямой доступ
student_age = student.get("age", 0)      # Безопасный доступ с значением по умолчанию
student_gpa = student.get("gpa")         # Вернет None, если ключа нет

print(f"Имя: {student_name}")
print(f"Возраст: {student_age}")
print(f"Средний балл: {student_gpa or 'не указан'}")

# Добавление и изменение данных
student["gpa"] = 4.5                     # Добавить новый ключ
student["age"] = 21                      # Изменить существующий
student["subjects"].append("английский") # Изменить список внутри словаря

print("\\nОбновленная информация:")
print(student)

# Проверка наличия ключей
if "email" in student:
    print(f"Email: {student['email']}")
else:
    print("Email не указан")

# Итерация по словарю
print("\\nВся информация о студенте:")
for key, value in student.items():
    if key == "subjects":
        print(f"{key}: {', '.join(value)}")
    else:
        print(f"{key}: {value}")

# Получение всех ключей и значений
all_keys = list(student.keys())
all_values = list(student.values())
print(f"\\nВсе ключи: {all_keys}")
print(f"Количество полей: {len(student)}")'''
    },
    
    "functions": {
        "title": "Функции для организации кода",
        "description": "Функции помогают организовать код и избежать повторений",
        "code": '''# Определение и использование функций

def greet(name):
    """Простая функция приветствия."""
    return f"Привет, {name}!"

def calculate_area(length, width):
    """Вычисляет площадь прямоугольника."""
    area = length * width
    return area

def create_user_profile(name, age, city="Не указан"):
    """
    Создает профиль пользователя.
    
    Args:
        name: Имя пользователя
        age: Возраст пользователя  
        city: Город (необязательный параметр)
    
    Returns:
        Словарь с информацией о пользователе
    """
    profile = {
        "name": name,
        "age": age,
        "city": city,
        "is_adult": age >= 18
    }
    return profile

# Использование функций
print(greet("Мария"))

room_area = calculate_area(5, 4)
print(f"Площадь комнаты: {room_area} кв.м")

# Создание профилей пользователей
user1 = create_user_profile("Иван", 25, "Москва")
user2 = create_user_profile("Анна", 17)  # Город не указан

print("\\nПрофиль пользователя 1:")
for key, value in user1.items():
    print(f"  {key}: {value}")

print("\\nПрофиль пользователя 2:")
for key, value in user2.items():
    print(f"  {key}: {value}")

# Функция с несколькими возвращаемыми значениями
def get_name_parts(full_name):
    """Разделяет полное имя на части."""
    parts = full_name.split()
    first_name = parts[0] if len(parts) > 0 else ""
    last_name = parts[-1] if len(parts) > 1 else ""
    return first_name, last_name

first, last = get_name_parts("Петр Иванович Сидоров")
print(f"\\nИмя: {first}, Фамилия: {last}")'''
    },
    
    "loops": {
        "title": "Циклы для повторения действий",
        "description": "Циклы позволяют выполнять код многократно",
        "code": '''# Различные виды циклов в Python

# Цикл for для итерации по последовательности
print("=== Цикл FOR ===")

# Итерация по списку
colors = ["красный", "зеленый", "синий"]
print("Цвета:")
for color in colors:
    print(f"  - {color}")

# Итерация по строке
word = "Python"
print(f"\\nБуквы в слове '{word}':")
for letter in word:
    print(f"  {letter}")

# Использование range() для числовых последовательностей
print("\\nЧисла от 1 до 5:")
for i in range(1, 6):
    print(f"  Число: {i}")

# Enumerate для получения индекса и значения
print("\\nЦвета с номерами:")
for index, color in enumerate(colors, 1):
    print(f"  {index}. {color}")

# Цикл while для повторения пока условие истинно
print("\\n=== Цикл WHILE ===")

count = 0
print("Обратный отсчет:")
while count < 5:
    print(f"  {5 - count}")
    count += 1
print("  Пуск!")

# Практический пример: поиск в списке
numbers = [2, 7, 1, 8, 3, 9, 4]
target = 8
found_index = -1

print(f"\\nПоиск числа {target} в списке {numbers}:")
for i, number in enumerate(numbers):
    if number == target:
        found_index = i
        break  # Прерываем цикл при нахождении

if found_index != -1:
    print(f"  Число {target} найдено на позиции {found_index}")
else:
    print(f"  Число {target} не найдено")

# Вложенные циклы
print("\\n=== Вложенные циклы ===")
print("Таблица умножения 3x3:")
for i in range(1, 4):
    for j in range(1, 4):
        result = i * j
        print(f"  {i} × {j} = {result}")
    print()  # Пустая строка после каждой строки таблицы'''
    },
    
    "conditionals": {
        "title": "Условные конструкции",
        "description": "Условия позволяют выполнять разный код в зависимости от ситуации",
        "code": '''# Условные конструкции в Python

# Простое условие if
age = 18
print("=== Простые условия ===")

if age >= 18:
    print("Вы совершеннолетний")
else:
    print("Вы несовершеннолетний")

# Множественные условия if-elif-else
score = 85
print(f"\\nОценка за тест: {score}")

if score >= 90:
    grade = "Отлично"
elif score >= 80:
    grade = "Хорошо"
elif score >= 70:
    grade = "Удовлетворительно"
else:
    grade = "Неудовлетворительно"

print(f"Результат: {grade}")

# Логические операторы
temperature = 22
is_sunny = True
print(f"\\nТемпература: {temperature}°C, Солнечно: {is_sunny}")

if temperature > 20 and is_sunny:
    print("Отличная погода для прогулки!")
elif temperature > 20 or is_sunny:
    print("Неплохая погода")
else:
    print("Лучше остаться дома")

# Проверка принадлежности
fruits = ["яблоко", "банан", "апельсин"]
user_choice = "банан"

if user_choice in fruits:
    print(f"\\n{user_choice} есть в наличии")
else:
    print(f"\\n{user_choice} нет в наличии")

# Проверка типа данных
value = "123"
print(f"\\nЗначение: '{value}'")

if isinstance(value, str):
    if value.isdigit():
        number = int(value)
        print(f"Это строка с числом: {number}")
    else:
        print("Это обычная строка")
elif isinstance(value, int):
    print("Это целое число")
else:
    print("Это что-то другое")

# Тернарный оператор (краткая форма if-else)
number = 7
result = "четное" if number % 2 == 0 else "нечетное"
print(f"\\nЧисло {number} - {result}")

# Практический пример: валидация пользовательского ввода
username = "user123"
password = "mypassword"

print(f"\\nПроверка данных пользователя:")
print(f"Логин: {username}")

# Проверка логина
if len(username) < 3:
    print("❌ Логин слишком короткий (минимум 3 символа)")
elif len(username) > 20:
    print("❌ Логин слишком длинный (максимум 20 символов)")
elif not username.isalnum():
    print("❌ Логин должен содержать только буквы и цифры")
else:
    print("✅ Логин корректный")

# Проверка пароля
if len(password) < 8:
    print("❌ Пароль слишком короткий (минимум 8 символов)")
elif password.lower() == password:
    print("⚠️  Пароль должен содержать заглавные буквы")
else:
    print("✅ Пароль достаточно сложный")'''
    },
    
    "file_operations": {
        "title": "Работа с файлами",
        "description": "Чтение и запись файлов - важная часть многих программ",
        "code": '''# Работа с файлами в Python

# Запись в файл
print("=== Запись в файл ===")

# Создание и запись текстового файла
filename = "example.txt"
content = """Это пример файла.
Он содержит несколько строк текста.
Python делает работу с файлами простой!"""

# Безопасная запись с автоматическим закрытием файла
with open(filename, 'w', encoding='utf-8') as file:
    file.write(content)
    
print(f"Файл '{filename}' создан и записан")

# Чтение файла
print("\\n=== Чтение файла ===")

try:
    with open(filename, 'r', encoding='utf-8') as file:
        file_content = file.read()
        print("Содержимое файла:")
        print(file_content)
except FileNotFoundError:
    print(f"Файл '{filename}' не найден")

# Чтение файла построчно
print("\\n=== Чтение по строкам ===")

try:
    with open(filename, 'r', encoding='utf-8') as file:
        line_number = 1
        for line in file:
            print(f"Строка {line_number}: {line.strip()}")
            line_number += 1
except FileNotFoundError:
    print(f"Файл '{filename}' не найден")

# Добавление в существующий файл
print("\\n=== Добавление в файл ===")

additional_content = "\\nЭта строка добавлена позже."

with open(filename, 'a', encoding='utf-8') as file:
    file.write(additional_content)
    
print("Содержимое добавлено в файл")

# Чтение обновленного файла
with open(filename, 'r', encoding='utf-8') as file:
    updated_content = file.read()
    print("\\nОбновленное содержимое:")
    print(updated_content)

# Работа с CSV-подобными данными
print("\\n=== Работа с данными ===")

# Создание файла с данными о студентах
students_data = """Имя,Возраст,Курс
Анна,20,2
Борис,19,1
Вера,21,3
Григорий,22,4"""

with open("students.txt", 'w', encoding='utf-8') as file:
    file.write(students_data)

# Чтение и обработка данных
print("Список студентов:")
with open("students.txt", 'r', encoding='utf-8') as file:
    lines = file.readlines()
    
    # Пропускаем заголовок (первую строку)
    for line in lines[1:]:
        name, age, course = line.strip().split(',')
        print(f"  {name}: {age} лет, {course} курс")

# Безопасная работа с файлами
print("\\n=== Безопасная работа ===")

def safe_read_file(filepath):
    """Безопасное чтение файла с обработкой ошибок."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return f"Ошибка: файл '{filepath}' не найден"
    except PermissionError:
        return f"Ошибка: нет прав для чтения файла '{filepath}'"
    except Exception as e:
        return f"Неожиданная ошибка: {e}"

# Тестирование безопасной функции
result1 = safe_read_file("example.txt")
result2 = safe_read_file("nonexistent.txt")

print("Результат чтения существующего файла:")
print(result1[:50] + "..." if len(result1) > 50 else result1)
print("\\nРезультат чтения несуществующего файла:")
print(result2)'''
    }
}


def generate_example(concept: str) -> str:
    """
    Generate a code example for a Python concept.
    
    Args:
        concept: The Python concept to generate an example for.
                Available concepts: variables, lists, dictionaries, functions, 
                loops, conditionals, file_operations
    
    Returns:
        A formatted code example as a string, or an error message if concept not found.
    """
    concept_lower = concept.lower().strip()
    
    if concept_lower not in CODE_EXAMPLES:
        available_concepts = ", ".join(CODE_EXAMPLES.keys())
        return f"❌ Концепция '{concept}' не найдена.\n📚 Доступные концепции: {available_concepts}"
    
    example_data = CODE_EXAMPLES[concept_lower]
    
    result = f"""
{'=' * 60}
📖 {example_data['title']}
{'=' * 60}

📝 Описание: {example_data['description']}

💻 Пример кода:

{example_data['code']}

{'=' * 60}
💡 Совет: Попробуйте запустить этот код и поэкспериментировать с ним!
{'=' * 60}
"""
    return result.strip()


def list_available_concepts() -> list:
    """
    Get a list of all available code example concepts.
    
    Returns:
        List of available concept names
    """
    return list(CODE_EXAMPLES.keys())


def get_concept_info(concept: str) -> Optional[Dict[str, str]]:
    """
    Get information about a specific concept.
    
    Args:
        concept: The concept to get information for
        
    Returns:
        Dictionary with concept information or None if not found
    """
    concept_lower = concept.lower().strip()
    
    if concept_lower not in CODE_EXAMPLES:
        return None
    
    return {
        "title": CODE_EXAMPLES[concept_lower]["title"],
        "description": CODE_EXAMPLES[concept_lower]["description"]
    }



def explain(topic: str) -> Dict[str, str]:
    """
    Get a structured explanation for a Python topic.
    
    This function loads explanations from the explanations.json file and returns
    a dictionary containing a description, usage guidance, and code example for
    the requested topic.
    
    Parameters
    ----------
    topic : str
        The name of the Python topic to explain (e.g., 'list', 'for', 'lambda').
        Topic names are case-insensitive.
    
    Returns
    -------
    dict
        A dictionary with the following keys:
        - 'description' (str): A clear, concise explanation of what the topic is
        - 'when_to_use' (str): Practical guidance on when to use this topic
        - 'example' (str): Valid, runnable Python code demonstrating the topic
    
    Raises
    ------
    ValueError
        If the topic is not found in the explanations database. The error message
        includes a helpful list of all available topics.
    FileNotFoundError
        If the explanations.json file cannot be found.
    json.JSONDecodeError
        If the explanations.json file is corrupted or invalid.
    
    Examples
    --------
    >>> explanation = explain('list')
    >>> print(explanation['description'])
    Ordered collection of items that can be of different types...
    
    >>> explanation = explain('lambda')
    >>> print(explanation['example'])
    square = lambda x: x ** 2
    print(square(5))
    
    >>> try:
    ...     explain('invalid_topic')
    ... except ValueError as e:
    ...     print(str(e))
    Topic 'invalid_topic' not found. Available topics: int, float, str, ...
    """
    # Normalize the topic name
    topic_normalized = topic.strip().lower()
    
    # Get the path to the explanations.json file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    explanations_path = os.path.join(current_dir, 'explanations.json')
    
    # Load the explanations from JSON file
    try:
        with open(explanations_path, 'r', encoding='utf-8') as f:
            explanations = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Explanations file not found at {explanations_path}. "
            "Please ensure explanations.json is in the fishertools/learn/ directory."
        )
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Failed to parse explanations.json: {e.msg}",
            e.doc,
            e.pos
        )
    
    # Check if the topic exists
    if topic_normalized not in explanations:
        available_topics = sorted(explanations.keys())
        topics_str = ", ".join(available_topics)
        raise ValueError(
            f"Topic '{topic}' not found. Available topics: {topics_str}"
        )
    
    # Return the explanation dictionary
    return explanations[topic_normalized]
