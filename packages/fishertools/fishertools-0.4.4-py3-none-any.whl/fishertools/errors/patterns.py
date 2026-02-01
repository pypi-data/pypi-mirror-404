"""
Error patterns database.

This module contains predefined patterns for common Python exceptions
with Russian explanations for beginners.
"""

from .models import ErrorPattern


# Error patterns for common Python exceptions
DEFAULT_PATTERNS = [
    # TypeError patterns
    ErrorPattern(
        error_type=TypeError,
        error_keywords=["unsupported operand type", "can't multiply", "can't add", "not supported between"],
        explanation="Вы пытаетесь выполнить операцию между несовместимыми типами данных. Например, нельзя сложить число и строку.",
        tip="Убедитесь, что все операнды имеют совместимые типы. Используйте функции преобразования типов (int(), str(), float()) если нужно.",
        example="# Неправильно:\n# result = 5 + '3'  # TypeError\n\n# Правильно:\nresult = 5 + int('3')  # 8\n# или\nresult = str(5) + '3'  # '53'",
        common_causes=["смешивание чисел и строк", "неправильные типы аргументов функции", "операции с None"]
    ),
    
    ErrorPattern(
        error_type=TypeError,
        error_keywords=["takes", "positional argument", "got", "missing", "required positional argument"],
        explanation="Функция вызвана с неправильным количеством аргументов. Либо передано слишком много, либо слишком мало параметров.",
        tip="Проверьте определение функции и убедитесь, что передаете правильное количество аргументов в правильном порядке.",
        example="# Неправильно:\n# def greet(name, age):\n#     return f'Привет, {name}! Тебе {age} лет.'\n# greet('Анна')  # TypeError - не хватает аргумента\n\n# Правильно:\ndef greet(name, age):\n    return f'Привет, {name}! Тебе {age} лет.'\nresult = greet('Анна', 25)",
        common_causes=["забыли передать аргумент", "передали лишний аргумент", "неправильный порядок аргументов"]
    ),
    
    ErrorPattern(
        error_type=TypeError,
        error_keywords=["not callable", "object is not callable"],
        explanation="Вы пытаетесь вызвать как функцию объект, который функцией не является. Возможно, забыли скобки или перепутали переменную с функцией.",
        tip="Проверьте, что вызываете именно функцию. Убедитесь, что не перезаписали имя функции переменной.",
        example="# Неправильно:\n# my_list = [1, 2, 3]\n# result = my_list()  # TypeError - список не функция\n\n# Правильно:\nmy_list = [1, 2, 3]\nresult = len(my_list)  # вызываем функцию len()",
        common_causes=["вызов переменной как функции", "перезапись имени функции", "опечатка в имени функции"]
    ),
    
    # ValueError patterns
    ErrorPattern(
        error_type=ValueError,
        error_keywords=["invalid literal", "could not convert", "base"],
        explanation="Не удалось преобразовать строку в число, потому что строка содержит недопустимые символы для числа.",
        tip="Убедитесь, что строка содержит только цифры (и точку для float). Проверьте входные данные перед преобразованием.",
        example="# Неправильно:\n# number = int('abc')  # ValueError\n\n# Правильно:\nuser_input = '123'\nif user_input.isdigit():\n    number = int(user_input)\nelse:\n    print('Введите корректное число')",
        common_causes=["ввод текста вместо числа", "лишние пробелы в строке", "неправильный формат числа"]
    ),
    
    ErrorPattern(
        error_type=ValueError,
        error_keywords=["not enough values to unpack", "too many values to unpack"],
        explanation="Количество переменных не соответствует количеству значений при распаковке. Либо переменных больше чем значений, либо наоборот.",
        tip="Убедитесь, что количество переменных слева от знака = равно количеству элементов в последовательности справа.",
        example="# Неправильно:\n# a, b = [1, 2, 3]  # слишком много значений\n# x, y, z = [1, 2]  # не хватает значений\n\n# Правильно:\na, b, c = [1, 2, 3]  # количество совпадает\n# или используйте индексы:\ndata = [1, 2, 3]\na = data[0]\nb = data[1]",
        common_causes=["неправильное количество переменных", "изменился размер списка", "ошибка в логике программы"]
    ),
    
    # AttributeError patterns
    ErrorPattern(
        error_type=AttributeError,
        error_keywords=["has no attribute", "object has no attribute"],
        explanation="Вы пытаетесь обратиться к атрибуту или методу, которого не существует у данного объекта.",
        tip="Проверьте правильность написания имени атрибута или метода. Убедитесь, что объект имеет нужный атрибут. Используйте dir() для просмотра доступных атрибутов.",
        example="# Неправильно:\n# my_string = 'привет'\n# my_string.append('!')  # у строк нет метода append\n\n# Правильно:\nmy_string = 'привет'\nmy_string = my_string + '!'  # конкатенация строк\n# или для списков:\nmy_list = ['привет']\nmy_list.append('!')",
        common_causes=["опечатка в имени метода", "неправильный тип объекта", "объект не инициализирован"]
    ),
    
    # IndexError patterns
    ErrorPattern(
        error_type=IndexError,
        error_keywords=["list index out of range", "string index out of range"],
        explanation="Вы пытаетесь обратиться к элементу списка или строки по индексу, который не существует. Индекс слишком большой или отрицательный.",
        tip="Проверьте длину списка/строки с помощью len(). Помните, что индексы начинаются с 0 и заканчиваются на len()-1.",
        example="# Неправильно:\n# my_list = [1, 2, 3]\n# print(my_list[5])  # IndexError - индекс 5 не существует\n\n# Правильно:\nmy_list = [1, 2, 3]\nif len(my_list) > 2:\n    print(my_list[2])  # проверяем длину перед обращением\n# или используйте безопасный доступ:\nindex = 2\nif 0 <= index < len(my_list):\n    print(my_list[index])",
        common_causes=["неправильный расчет индекса", "пустой список", "цикл выходит за границы"]
    ),
    
    # KeyError patterns
    ErrorPattern(
        error_type=KeyError,
        error_keywords=[""],  # KeyError messages are often just the key name, so match any KeyError
        explanation="Вы пытаетесь получить значение из словаря по ключу, которого в словаре не существует.",
        tip="Проверьте, существует ли ключ в словаре с помощью 'in' или используйте метод get() с значением по умолчанию.",
        example="# Неправильно:\n# my_dict = {'имя': 'Анна', 'возраст': 25}\n# print(my_dict['город'])  # KeyError - ключа 'город' нет\n\n# Правильно:\nmy_dict = {'имя': 'Анна', 'возраст': 25}\n# Способ 1: проверка существования ключа\nif 'город' in my_dict:\n    print(my_dict['город'])\nelse:\n    print('Город не указан')\n# Способ 2: использование get()\nprint(my_dict.get('город', 'Не указан'))",
        common_causes=["опечатка в имени ключа", "ключ не был добавлен в словарь", "неправильный тип ключа"]
    ),
    
    # ImportError patterns
    ErrorPattern(
        error_type=ImportError,
        error_keywords=["No module named", "cannot import name"],
        explanation="Python не может найти модуль или функцию, которую вы пытаетесь импортировать. Возможно, модуль не установлен или имя написано неправильно.",
        tip="Убедитесь, что модуль установлен (pip install имя_модуля) и имя написано правильно. Проверьте, что файл находится в правильной папке.",
        example="# Если модуль не установлен:\n# pip install requests\n\n# Правильный импорт:\nimport os  # встроенный модуль\nfrom datetime import datetime  # импорт конкретной функции\n\n# Для собственных модулей:\n# убедитесь, что файл my_module.py находится в той же папке\n# import my_module",
        common_causes=["модуль не установлен", "опечатка в имени", "неправильный путь к файлу", "проблемы с виртуальным окружением"]
    ),
    
    # SyntaxError patterns
    ErrorPattern(
        error_type=SyntaxError,
        error_keywords=["invalid syntax", "unexpected EOF", "unmatched", "expected"],
        explanation="В коде есть синтаксическая ошибка - нарушены правила написания кода Python. Это может быть незакрытая скобка, неправильный отступ или опечатка.",
        tip="Внимательно проверьте строку, указанную в ошибке. Убедитесь, что все скобки закрыты, отступы правильные, и нет опечаток в ключевых словах.",
        example="# Неправильно:\n# if x > 5  # забыли двоеточие\n#     print('больше 5')\n# print('привет'  # незакрытая скобка\n\n# Правильно:\nif x > 5:  # двоеточие обязательно\n    print('больше 5')  # правильный отступ\nprint('привет')  # закрытая скобка",
        common_causes=["забыли двоеточие после if/for/def", "незакрытые скобки", "неправильные отступы", "опечатки в ключевых словах"]
    ),
    
    # FileNotFoundError patterns
    ErrorPattern(
        error_type=FileNotFoundError,
        error_keywords=["No such file or directory", "cannot find the file"],
        explanation="Файл, который вы пытаетесь открыть, не существует. Возможно, неправильно указан путь к файлу или файл находится в другой папке.",
        tip="Проверьте правильность пути к файлу. Убедитесь, что файл существует в указанной папке. Используйте абсолютный путь или проверьте текущую рабочую папку.",
        example="# Неправильно:\n# with open('data.txt', 'r') as f:  # файл может не существовать\n#     data = f.read()\n\n# Правильно:\nimport os\nfilepath = 'data.txt'\nif os.path.exists(filepath):\n    with open(filepath, 'r') as f:\n        data = f.read()\nelse:\n    print(f'Файл {filepath} не найден')",
        common_causes=["неправильный путь к файлу", "файл не существует", "неправильная рабочая папка", "опечатка в имени файла"]
    ),
    
    # PermissionError patterns
    ErrorPattern(
        error_type=PermissionError,
        error_keywords=["Permission denied", "access denied"],
        explanation="У вас нет прав доступа для выполнения этой операции с файлом. Это может быть файл, защищенный от записи, или папка, к которой нет доступа.",
        tip="Проверьте права доступа к файлу. Попробуйте запустить программу с правами администратора. Убедитесь, что файл не открыт в другой программе.",
        example="# Неправильно:\n# with open('protected_file.txt', 'w') as f:  # может быть защищен\n#     f.write('data')\n\n# Правильно:\nimport os\nfilepath = 'protected_file.txt'\nif os.access(filepath, os.W_OK):\n    with open(filepath, 'w') as f:\n        f.write('data')\nelse:\n    print(f'Нет прав доступа к файлу {filepath}')",
        common_causes=["файл защищен от записи", "недостаточно прав доступа", "файл открыт в другой программе", "папка защищена"]
    ),
    
    # ZeroDivisionError patterns
    ErrorPattern(
        error_type=ZeroDivisionError,
        error_keywords=["division by zero", "integer division or modulo by zero"],
        explanation="Вы пытаетесь разделить число на ноль, что математически невозможно. Это может быть деление или операция модуля (%).",
        tip="Проверьте, что делитель не равен нулю перед выполнением операции деления. Используйте условие if для проверки.",
        example="# Неправильно:\n# result = 10 / 0  # ZeroDivisionError\n\n# Правильно:\ndivisor = 0\nif divisor != 0:\n    result = 10 / divisor\nelse:\n    print('Нельзя делить на ноль')\n    result = None",
        common_causes=["деление на ноль", "модуль по нулю", "переменная содержит ноль неожиданно", "ошибка в расчетах"]
    ),
    
    # NameError patterns
    ErrorPattern(
        error_type=NameError,
        error_keywords=["is not defined", "name"],
        explanation="Вы используете переменную или функцию, которая не была определена. Возможно, опечатка в имени или переменная определена в другой области видимости.",
        tip="Проверьте правильность написания имени переменной. Убедитесь, что переменная определена перед использованием. Проверьте область видимости переменной.",
        example="# Неправильно:\n# print(my_variable)  # NameError - переменная не определена\n\n# Правильно:\nmy_variable = 'Hello'  # определяем переменную\nprint(my_variable)  # теперь можно использовать\n\n# Или проверяем область видимости:\nif True:\n    local_var = 'local'\nprint(local_var)  # NameError - переменная локальная",
        common_causes=["опечатка в имени переменной", "переменная не определена", "переменная в другой области видимости", "забыли импортировать модуль"]
    )
]


def load_default_patterns():
    """
    Load default error patterns for common Python exceptions.
    
    Returns:
        List of ErrorPattern objects for common Python exceptions
    """
    return DEFAULT_PATTERNS.copy()