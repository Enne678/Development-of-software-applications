# РАЗДЕЛ I. ФУНКЦИЯ get_triangle_type И КЛАСС Triangle


class IncorrectTriangleSides(Exception):
    """Исключение для некорректных сторон треугольника"""
    pass


def get_triangle_type(a, b, c):
    """
    Определяет тип треугольника по длинам сторон

    Args:
        a, b, c (float): Длины сторон треугольника

    Returns:
        str: Тип треугольника ("equilateral", "isosceles", "nonequilateral")

    Raises:
        IncorrectTriangleSides: Если стороны не образуют треугольник
    """
    # Проверка на положительность сторон
    if a <= 0 or b <= 0 or c <= 0:
        raise IncorrectTriangleSides("Стороны треугольника должны быть положительными")

    # Проверка неравенства треугольника
    if a + b <= c or a + c <= b or b + c <= a:
        raise IncorrectTriangleSides("Стороны не удовлетворяют неравенству треугольника")

    # Определение типа треугольника
    if a == b == c:
        return "equilateral"
    elif a == b or b == c or a == c:
        return "isosceles"
    else:
        return "nonequilateral"


class Triangle:
    """Класс для работы с треугольником"""

    def __init__(self, a, b, c):
        """
        Конструктор треугольника

        Args:
            a, b, c (float): Длины сторон треугольника

        Raises:
            IncorrectTriangleSides: Если стороны не образуют треугольник
        """
        # Проверка на положительность сторон
        if a <= 0 or b <= 0 or c <= 0:
            raise IncorrectTriangleSides("Стороны треугольника должны быть положительными")

        # Проверка неравенства треугольника
        if a + b <= c or a + c <= b or b + c <= a:
            raise IncorrectTriangleSides("Стороны не удовлетворяют неравенству треугольника")

        self.a = a
        self.b = b
        self.c = c

    def triangle_type(self):
        """
        Определяет тип треугольника

        Returns:
            str: Тип треугольника ("equilateral", "isosceles", "nonequilateral")
        """
        if self.a == self.b == self.c:
            return "equilateral"
        elif self.a == self.b or self.b == self.c or self.a == self.c:
            return "isosceles"
        else:
            return "nonequilateral"

    def perimeter(self):
        """
        Вычисляет периметр треугольника

        Returns:
            float: Периметр треугольника
        """
        return self.a + self.b + self.c

    def __str__(self):
        """Строковое представление треугольника"""
        return f"Triangle({self.a}, {self.b}, {self.c})"

    def __repr__(self):
        """Представление для отладки"""
        return f"Triangle(a={self.a}, b={self.b}, c={self.c})"


# РАЗДЕЛ II. ДЕМОНСТРАЦИЯ РАБОТЫ

def demonstrate_function():
    """Демонстрация работы функции get_triangle_type"""
    print("=== Демонстрация функции get_triangle_type ===")

    test_cases = [
        (3, 3, 3),  # равносторонний
        (3, 3, 2),  # равнобедренный
        (3, 4, 5),  # разносторонний
        (1, 1, 3),  # некорректный
        (-1, 2, 3),  # отрицательная сторона
    ]

    for a, b, c in test_cases:
        try:
            result = get_triangle_type(a, b, c)
            print(f"get_triangle_type({a}, {b}, {c}) = {result}")
        except IncorrectTriangleSides as e:
            print(f"get_triangle_type({a}, {b}, {c}) вызвал исключение: {e}")


def demonstrate_class():
    """Демонстрация работы класса Triangle"""
    print("\n=== Демонстрация класса Triangle ===")

    try:
        # Создание корректных треугольников
        triangles = [
            Triangle(3, 3, 3),  # равносторонний
            Triangle(3, 3, 2),  # равнобедренный
            Triangle(3, 4, 5),  # разносторонний
        ]

        for triangle in triangles:
            print(f"Треугольник: {triangle}")
            print(f" Тип: {triangle.triangle_type()}")
            print(f" Периметр: {triangle.perimeter()}")
            print()

        # Попытка создания некорректного треугольника
        try:
            invalid_triangle = Triangle(1, 1, 3)
        except IncorrectTriangleSides as e:
            print(f"Ошибка при создании Triangle(1, 1, 3): {e}")

    except Exception as e:
        print(f"Ошибка: {e}")


# РАЗДЕЛ III. ОСНОВНАЯ ПРОГРАММА

if __name__ == "__main__":
    print("Лабораторная работа №7: Практика написания юнит тестов на языке программирования Python")
    print("=" * 60)

    demonstrate_function()
    demonstrate_class()

    print("\n=== Информация о файлах ===")
    print("1. triangle_func.py - содержит функцию get_triangle_type")
    print("2. triangle_class.py - содержит класс Triangle")
    print("3. test_func.py - тесты функции с использованием unittest")
    print("4. test_class.py - тесты класса с использованием pytest")
    print("5. check.txt - чек-лист для тестирования")
    print("\nДля запуска тестов:")
    print(" unittest: python -m test_func.py")
    print(" pytest: pytest test_class.py -v")