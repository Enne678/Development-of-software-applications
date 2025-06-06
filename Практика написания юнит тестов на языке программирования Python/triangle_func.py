"""
Тесты для функции get_triangle_type с использованием unittest
"""

import unittest
"""
Модуль для работы с треугольниками
Содержит функцию для определения типа треугольника
"""

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