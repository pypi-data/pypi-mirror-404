from __future__ import annotations
import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).parent.parent))

from l0n0lc import jit

class Vector2D:
    x: float
    y: float

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __add__(self, other: Vector2D) -> Vector2D:
        return Vector2D(self.x + other.x, self.y + other.y)

    def __eq__(self, other: Vector2D) -> bool:
        return self.x == other.x and self.y == other.y

@jit(总是重编=True)
def test_vector_add() -> bool:
    v1 = Vector2D(1.0, 2.0)
    v2 = Vector2D(3.0, 4.0)
    result = v1 + v2
    # 测试运算符是否工作：result.x应该等于4.0
    return result.x == 4.0

@jit(总是重编=True)
def test_vector_eq() -> bool:
    v1 = Vector2D(1.0, 2.0)
    v2 = Vector2D(1.0, 2.0)
    v3 = Vector2D(3.0, 4.0)
    return v1 == v2 and not (v1 == v3)

if __name__ == '__main__':
    result1 = test_vector_add()
    print(f"Vector add result: {result1}")

    result2 = test_vector_eq()
    print(f"Vector eq result: {result2}")