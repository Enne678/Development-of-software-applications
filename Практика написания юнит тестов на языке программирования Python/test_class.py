"""
Тесты для класса Triangle с использованием pytest
"""

import pytest
from triangle_class import Triangle, IncorrectTriangleSides

class TestTriangleCreation:
    """Тесты создания объекта Triangle"""

    def test_valid_triangle_creation(self):
        """Тест создания корректного треугольника"""
        triangle = Triangle(3, 4, 5)
        assert triangle.a == 3
        assert triangle.b == 4
        assert triangle.c == 5

    def test_equilateral_triangle_creation(self):
        """Тест создания равностороннего треугольника"""
        triangle = Triangle(5, 5, 5)
        assert triangle.a == triangle.b == triangle.c == 5

    def test_negative_sides_creation(self):
        """Тест создания треугольника с отрицательными сторонами"""
        with pytest.raises(IncorrectTriangleSides):
            Triangle(-1, 2, 3)
        with pytest.raises(IncorrectTriangleSides):
            Triangle(1, -2, 3)
        with pytest.raises(IncorrectTriangleSides):
            Triangle(1, 2, -3)

    def test_zero_sides_creation(self):
        """Тест создания треугольника с нулевыми сторонами"""
        with pytest.raises(IncorrectTriangleSides):
            Triangle(0, 2, 3)
        with pytest.raises(IncorrectTriangleSides):
            Triangle(1, 0, 3)
        with pytest.raises(IncorrectTriangleSides):
            Triangle(1, 2, 0)

    def test_triangle_inequality_violation(self):
        """Тест нарушения неравенства треугольника"""
        with pytest.raises(IncorrectTriangleSides):
            Triangle(1, 1, 3)
        with pytest.raises(IncorrectTriangleSides):
            Triangle(2, 3, 6)
        with pytest.raises(IncorrectTriangleSides):
            Triangle(1, 2, 3)


class TestTriangleType:
    """Тесты метода triangle_type"""

    def test_equilateral_type(self):
        """Тест определения равностороннего треугольника"""
        triangle = Triangle(3, 3, 3)
        assert triangle.triangle_type() == "equilateral"

        triangle = Triangle(1, 1, 1)
        assert triangle.triangle_type() == "equilateral"

    def test_isosceles_type(self):
        """Тест определения равнобедренного треугольника"""
        triangle = Triangle(3, 3, 2)
        assert triangle.triangle_type() == "isosceles"

        triangle = Triangle(5, 4, 5)
        assert triangle.triangle_type() == "isosceles"

        triangle = Triangle(4, 7, 7)
        assert triangle.triangle_type() == "isosceles"

    def test_nonequilateral_type(self):
        """Тест определения разностороннего треугольника"""
        triangle = Triangle(3, 4, 5)
        assert triangle.triangle_type() == "nonequilateral"

        triangle = Triangle(2, 3, 4)
        assert triangle.triangle_type() == "nonequilateral"

        triangle = Triangle(6, 8, 10)
        assert triangle.triangle_type() == "nonequilateral"


class TestTrianglePerimeter:
    """Тесты метода perimeter"""

    def test_integer_perimeter(self):
        """Тест периметра с целыми числами"""
        triangle = Triangle(3, 4, 5)
        assert triangle.perimeter() == 12

        triangle = Triangle(2, 2, 3)
        assert triangle.perimeter() == 7

    def test_float_perimeter(self):
        """Тест периметра с дробными числами"""
        triangle = Triangle(1.5, 2.5, 3)
        assert triangle.perimeter() == 7.0

        triangle = Triangle(2.2, 3.3, 4.4)
        assert triangle.perimeter() == pytest.approx(9.9, rel=1e-9)

    def test_large_numbers_perimeter(self):
        """Тест периметра с большими числами"""
        triangle = Triangle(100, 200, 250)
        assert triangle.perimeter() == 550


class TestTriangleStringRepresentation:
    """Тесты строкового представления треугольника"""

    def test_str_representation(self):
        """Тест метода __str__"""
        triangle = Triangle(3, 4, 5)
        assert str(triangle) == "Triangle(3, 4, 5)"

    def test_repr_representation(self):
        """Тест метода __repr__"""
        triangle = Triangle(3, 4, 5)
        assert repr(triangle) == "Triangle(a=3, b=4, c=5)"


# Параметризованные тесты
@pytest.mark.parametrize("a,b,c,expected_type", [
    (3, 3, 3, "equilateral"),
    (1, 1, 1, "equilateral"),
    (3, 3, 2, "isosceles"),
    (5, 4, 5, "isosceles"),
    (4, 7, 7, "isosceles"),
    (3, 4, 5, "nonequilateral"),
    (2, 3, 4, "nonequilateral"),
    (6, 8, 10, "nonequilateral"),
])
def test_triangle_types_parametrized(a, b, c, expected_type):
    """Параметризованный тест типов треугольников"""
    triangle = Triangle(a, b, c)
    assert triangle.triangle_type() == expected_type


@pytest.mark.parametrize("a,b,c,expected_perimeter", [
    (3, 4, 5, 12),
    (2, 2, 3, 7),
    (1, 1, 1, 3),
    (10, 10, 15, 35),
])
def test_perimeter_parametrized(a, b, c, expected_perimeter):
    """Параметризованный тест периметра"""
    triangle = Triangle(a, b, c)
    assert triangle.perimeter() == expected_perimeter


@pytest.mark.parametrize("a,b,c", [
    (-1, 2, 3),
    (1, -2, 3),
    (1, 2, -3),
    (0, 2, 3),
    (1, 0, 3),
    (1, 2, 0),
    (1, 1, 3),
    (2, 3, 6),
    (1, 2, 3),
])
def test_invalid_triangles_parametrized(a, b, c):
    """Параметризованный тест некорректных треугольников"""
    with pytest.raises(IncorrectTriangleSides):
        Triangle(a, b, c)


# Фикстуры для повторного использования
@pytest.fixture
def equilateral_triangle():
    """Фикстура равностороннего треугольника"""
    return Triangle(5, 5, 5)


@pytest.fixture
def isosceles_triangle():
    """Фикстура равнобедренного треугольника"""
    return Triangle(3, 3, 2)


@pytest.fixture
def nonequilateral_triangle():
    """Фикстура разностороннего треугольника"""
    return Triangle(3, 4, 5)


def test_equilateral_with_fixture(equilateral_triangle):
    """Тест с использованием фикстуры равностороннего треугольника"""
    assert equilateral_triangle.triangle_type() == "equilateral"
    assert equilateral_triangle.perimeter() == 15


def test_isosceles_with_fixture(isosceles_triangle):
    """Тест с использованием фикстуры равнобедренного треугольника"""
    assert isosceles_triangle.triangle_type() == "isosceles"
    assert isosceles_triangle.perimeter() == 8


def test_nonequilateral_with_fixture(nonequilateral_triangle):
    """Тест с использованием фикстуры разностороннего треугольника"""
    assert nonequilateral_triangle.triangle_type() == "nonequilateral"
    assert nonequilateral_triangle.perimeter() == 12