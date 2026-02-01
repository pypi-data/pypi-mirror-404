"""
Best practices and tips for learning Python.

This module contains functions to show Python best practices
for common programming concepts that beginners encounter.
"""

from typing import Dict, List


# Database of best practices for different Python topics
BEST_PRACTICES: Dict[str, Dict[str, str]] = {
    "variables": {
        "title": "Переменные в Python",
        "practices": """
🔹 Используйте описательные имена переменных:
   ❌ Плохо: x = 25
   ✅ Хорошо: age = 25

🔹 Используйте snake_case для имен переменных:
   ❌ Плохо: firstName = "Иван"
   ✅ Хорошо: first_name = "Иван"

🔹 Избегайте зарезервированных слов:
   ❌ Плохо: list = [1, 2, 3]
   ✅ Хорошо: numbers = [1, 2, 3]

🔹 Используйте константы для неизменяемых значений:
   ✅ MAX_ATTEMPTS = 3
   ✅ PI = 3.14159
        """,
        "example": """
# Хороший пример использования переменных
user_name = "Анна"
user_age = 28
is_active = True
MAX_LOGIN_ATTEMPTS = 3

print(f"Пользователь {user_name}, возраст {user_age}")
        """
    },
    
    "functions": {
        "title": "Функции в Python",
        "practices": """
🔹 Используйте docstring для документации:
   def calculate_area(radius):
       \"\"\"Вычисляет площадь круга по радиусу.\"\"\"
       return 3.14159 * radius ** 2

🔹 Используйте type hints для ясности:
   def greet(name: str) -> str:
       return f"Привет, {name}!"

🔹 Функции должны делать одну вещь хорошо:
   ❌ Плохо: функция, которая и читает файл, и обрабатывает данные
   ✅ Хорошо: отдельные функции для чтения и обработки

🔹 Используйте значения по умолчанию разумно:
   def create_user(name: str, role: str = "user"):
       return {"name": name, "role": role}
        """,
        "example": """
def calculate_discount(price: float, discount_percent: float = 10.0) -> float:
    \"\"\"
    Вычисляет цену со скидкой.
    
    Args:
        price: Исходная цена товара
        discount_percent: Процент скидки (по умолчанию 10%)
    
    Returns:
        Цена со скидкой
    \"\"\"
    if price < 0:
        raise ValueError("Цена не может быть отрицательной")
    
    discount_amount = price * (discount_percent / 100)
    return price - discount_amount

# Использование
final_price = calculate_discount(1000.0, 15.0)
print(f"Цена со скидкой: {final_price}")
        """
    },
    
    "lists": {
        "title": "Работа со списками",
        "practices": """
🔹 Используйте list comprehensions для простых операций:
   ✅ squares = [x**2 for x in range(10)]
   ❌ Избегайте сложных comprehensions

🔹 Проверяйте границы при доступе к элементам:
   if 0 <= index < len(my_list):
       value = my_list[index]

🔹 Используйте enumerate() для индекса и значения:
   for i, item in enumerate(items):
       print(f"{i}: {item}")

🔹 Используйте методы списков эффективно:
   ✅ items.append(new_item)  # Добавить в конец
   ✅ items.extend(other_list)  # Добавить несколько элементов
        """,
        "example": """
# Хорошие практики работы со списками
fruits = ["яблоко", "банан", "апельсин"]

# Безопасный доступ к элементам
def get_fruit(fruits_list: list, index: int) -> str:
    if 0 <= index < len(fruits_list):
        return fruits_list[index]
    return "Фрукт не найден"

# Использование enumerate
print("Список фруктов:")
for i, fruit in enumerate(fruits, 1):
    print(f"{i}. {fruit}")

# List comprehension для преобразования
uppercase_fruits = [fruit.upper() for fruit in fruits]
print(f"Заглавными буквами: {uppercase_fruits}")
        """
    },
    
    "dictionaries": {
        "title": "Работа со словарями",
        "practices": """
🔹 Используйте get() для безопасного доступа:
   ✅ value = my_dict.get("key", "default")
   ❌ value = my_dict["key"]  # Может вызвать KeyError

🔹 Проверяйте наличие ключей:
   if "key" in my_dict:
       # Безопасно использовать my_dict["key"]

🔹 Используйте items() для итерации:
   for key, value in my_dict.items():
       print(f"{key}: {value}")

🔹 Используйте dict comprehensions:
   ✅ squares = {x: x**2 for x in range(5)}
        """,
        "example": """
# Хорошие практики работы со словарями
student_grades = {
    "Анна": 85,
    "Борис": 92,
    "Вера": 78
}

# Безопасный доступ к значениям
def get_grade(students: dict, name: str) -> str:
    grade = students.get(name)
    if grade is not None:
        return f"Оценка {name}: {grade}"
    return f"Студент {name} не найден"

# Итерация по словарю
print("Все оценки:")
for student, grade in student_grades.items():
    status = "отлично" if grade >= 90 else "хорошо" if grade >= 80 else "удовлетворительно"
    print(f"{student}: {grade} ({status})")

# Добавление нового студента
student_grades["Григорий"] = 88
        """
    },
    
    "error_handling": {
        "title": "Обработка ошибок",
        "practices": """
🔹 Используйте конкретные типы исключений:
   ❌ except Exception:  # Слишком общее
   ✅ except ValueError:  # Конкретное исключение

🔹 Всегда обрабатывайте ошибки осмысленно:
   try:
       result = risky_operation()
   except ValueError as e:
       print(f"Ошибка значения: {e}")
       return None

🔹 Используйте finally для очистки ресурсов:
   try:
       file = open("data.txt")
       # работа с файлом
   finally:
       file.close()

🔹 Или лучше используйте контекстные менеджеры:
   with open("data.txt") as file:
       # файл автоматически закроется
        """,
        "example": """
def safe_divide(a: float, b: float) -> float:
    \"\"\"
    Безопасное деление с обработкой ошибок.
    \"\"\"
    try:
        if b == 0:
            raise ValueError("Деление на ноль невозможно")
        
        result = a / b
        return result
        
    except TypeError:
        print("Ошибка: аргументы должны быть числами")
        return 0.0
    except ValueError as e:
        print(f"Ошибка значения: {e}")
        return 0.0

# Использование
print(safe_divide(10, 2))    # 5.0
print(safe_divide(10, 0))    # Обработка деления на ноль
print(safe_divide("10", 2))  # Обработка неправильного типа
        """
    }
}


def show_best_practice(topic: str) -> None:
    """
    Show best practices for a specific Python topic.
    
    Args:
        topic: The Python topic to show best practices for.
               Available topics: variables, functions, lists, dictionaries, error_handling
    
    Displays formatted best practices with examples to the console.
    """
    topic_lower = topic.lower().strip()
    
    if topic_lower not in BEST_PRACTICES:
        available_topics = ", ".join(BEST_PRACTICES.keys())
        print(f"❌ Тема '{topic}' не найдена.")
        print(f"📚 Доступные темы: {available_topics}")
        return
    
    practice_data = BEST_PRACTICES[topic_lower]
    
    print("=" * 60)
    print(f"📖 {practice_data['title']}")
    print("=" * 60)
    print()
    print("🎯 ЛУЧШИЕ ПРАКТИКИ:")
    print(practice_data['practices'])
    print()
    print("💡 ПРИМЕР КОДА:")
    print(practice_data['example'])
    print("=" * 60)


def list_available_topics() -> List[str]:
    """
    Get a list of all available best practice topics.
    
    Returns:
        List of available topic names
    """
    return list(BEST_PRACTICES.keys())


def get_topic_summary(topic: str) -> str:
    """
    Get a brief summary of a best practice topic.
    
    Args:
        topic: The topic to get summary for
        
    Returns:
        Brief summary string or error message
    """
    topic_lower = topic.lower().strip()
    
    if topic_lower not in BEST_PRACTICES:
        return f"Тема '{topic}' не найдена"
    
    return BEST_PRACTICES[topic_lower]['title']