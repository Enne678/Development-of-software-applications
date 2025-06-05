"""
Тесты для функции get_triangle_type с использованием unittest
"""

import unittest
from triangle_func import get_triangle_type, IncorrectTriangleSides

class TestGetTriangleType(unittest.TestCase):
    """Класс для тестирования функции get_triangle_type"""

    def test_equilateral_triangle(self):
        """Тест равностороннего треугольника"""
        self.assertEqual(get_triangle_type(3, 3, 3), "equilateral")
        self.assertEqual(get_triangle_type(1, 1, 1), "equilateral")
        self.assertEqual(get_triangle_type(5.5, 5.5, 5.5), "equilateral")

    def test_isosceles_triangle(self):
        """Тест равнобедренного треугольника"""
        self.assertEqual(get_triangle_type(3, 3, 2), "isosceles")
        self.assertEqual(get_triangle_type(5, 4, 5), "isosceles")
        self.assertEqual(get_triangle_type(4, 7, 7), "isosceles")
        self.assertEqual(get_triangle_type(2.5, 2.5, 4), "isosceles")

    def test_nonequilateral_triangle(self):
        """Тест разностороннего треугольника"""
        self.assertEqual(get_triangle_type(3, 4, 5), "nonequilateral")
        self.assertEqual(get_triangle_type(2, 3, 4), "nonequilateral")
        self.assertEqual(get_triangle_type(6, 8, 10), "nonequilateral")
        self.assertEqual(get_triangle_type(1.5, 2.5, 3), "nonequilateral")

    def test_triangle_inequality_violation(self):
        """Тест нарушения неравенства треугольника"""
        with self.assertRaises(IncorrectTriangleSides):
            get_triangle_type(1, 1, 3)
        with self.assertRaises(IncorrectTriangleSides):
            get_triangle_type(2, 3, 6)
        with self.assertRaises(IncorrectTriangleSides):
            get_triangle_type(1, 2, 3)

    def test_negative_sides(self):
        """Тест отрицательных сторон"""
        with self.assertRaises(IncorrectTriangleSides):
            get_triangle_type(-1, 2, 3)
        with self.assertRaises(IncorrectTriangleSides):
            get_triangle_type(1, -2, 3)
        with self.assertRaises(IncorrectTriangleSides):
            get_triangle_type(1, 2, -3)
        with self.assertRaises(IncorrectTriangleSides):
            get_triangle_type(-1, -2, -3)

    def test_zero_sides(self):
        """Тест нулевых сторон"""
        with self.assertRaises(IncorrectTriangleSides):
            get_triangle_type(0, 2, 3)
        with self.assertRaises(IncorrectTriangleSides):
            get_triangle_type(1, 0, 3)
        with self.assertRaises(IncorrectTriangleSides):
            get_triangle_type(1, 2, 0)
        with self.assertRaises(IncorrectTriangleSides):
            get_triangle_type(0, 0, 0)

    def test_degenerate_triangle(self):
        """Тест вырожденного треугольника"""
        with self.assertRaises(IncorrectTriangleSides):
            get_triangle_type(1, 1, 2)
        with self.assertRaises(IncorrectTriangleSides):
            get_triangle_type(2, 3, 5)

if __name__ == '__main__':
    unittest.main()