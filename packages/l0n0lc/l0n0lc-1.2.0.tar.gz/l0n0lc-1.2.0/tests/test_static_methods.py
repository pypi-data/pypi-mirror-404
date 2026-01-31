from __future__ import annotations
import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).parent.parent))

from l0n0lc import jit

class Math:
    @staticmethod
    def add(a: int, b: int) -> int:
        return a + b

    @staticmethod
    def multiply(a: int, b: int) -> int:
        return a * b

    @staticmethod
    def get_class_name() -> str:
        return "Math"

class Counter:
    count: int
    _instances: int = 0

    def __init__(self):
        self.count = 0
        Counter._instances += 1

    @staticmethod
    def get_instance_count() -> int:
        return Counter._instances

@jit(总是重编=True)
def test_static_methods() -> int:
    result1 = Math.add(5, 3)
    result2 = Math.multiply(2, 4)
    return result1 + result2  # Should be 8 + 8 = 16

@jit(总是重编=True)
def test_class_method() -> int:
    c1 = Counter()
    c2 = Counter()
    return Counter.get_instance_count()  # Should be 2

@jit(总是重编=True)
def test_class_name() -> str:
    return Math.get_class_name()  # Should return "Math"

if __name__ == '__main__':
    result1 = test_static_methods()
    print(f"Static methods result: {result1}")

    result2 = test_class_method()
    print(f"Class method result: {result2}")

    result3 = test_class_name()
    # const char* 返回 bytes，需要解码为 str
    result3_decoded = result3.decode() if isinstance(result3, bytes) else result3
    print(f"Class name result: {result3_decoded}")
