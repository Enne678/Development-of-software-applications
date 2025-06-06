"""
Модуль с классом Triangle для работы с треугольниками
"""


class IncorrectTriangleSides(Exception):
    """Исключение для некорректных сторон треугольника"""
    pass


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