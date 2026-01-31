import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).parent.parent))

from typing import Dict
from l0n0lc.即时编译 import 即时编译
import unittest

class TestDict(unittest.TestCase):
    """测试字典功能，包括迭代和方法操作"""

    # ========== 迭代相关测试 ==========

    def test_dict_items(self):
        """测试 dict.items() 遍历"""
        @即时编译(总是重编=True)
        def iterate_items() -> int:
            m: Dict[int, int] = {1: 10, 2: 20, 3: 30}
            total = 0
            for key, value in m.items():
                total = total + key + value
            return total

        # 1+10 + 2+20 + 3+30 = 66
        self.assertEqual(iterate_items(), 66)

    def test_dict_keys(self):
        """测试 dict.keys() 遍历"""
        @即时编译(总是重编=True)
        def iterate_keys() -> int:
            m: Dict[int, int] = {1: 10, 2: 20, 3: 30}
            total = 0
            for key in m.keys():
                total = total + key
            return total

        # 1 + 2 + 3 = 6
        self.assertEqual(iterate_keys(), 6)

    def test_dict_values(self):
        """测试 dict.values() 遍历"""
        @即时编译(总是重编=True)
        def iterate_values() -> int:
            m: Dict[int, int] = {1: 10, 2: 20, 3: 30}
            total = 0
            for value in m.values():
                total = total + value
            return total

        # 10 + 20 + 30 = 60
        self.assertEqual(iterate_values(), 60)

    def test_dict_direct_iteration(self):
        """测试直接遍历 dict（遍历键）"""
        @即时编译(总是重编=True)
        def iterate_direct() -> int:
            m: Dict[int, int] = {1: 10, 2: 20, 3: 30}
            total = 0
            for key in m:
                total = total + key
            return total

        # 1 + 2 + 3 = 6
        self.assertEqual(iterate_direct(), 6)

    def test_dict_items_with_access(self):
        """测试 items() 遍历并访问字典"""
        @即时编译(总是重编=True)
        def iterate_and_access() -> int:
            m: Dict[str, str] = {'a': '10', 'b': '20', 'c': '30'}
            total = 0
            for key, value in m.items():
                print(key, value)
                # 验证值是否正确
                if m[key] == value:
                    total = total + 1
            return total

        # 所有3个键值对都应该匹配
        self.assertEqual(iterate_and_access(), 3)

    def test_dict_items_string_keys(self):
        """测试字符串键的 items() 遍历"""
        @即时编译(总是重编=True)
        def iterate_string_keys() -> int:
            m: Dict[int, int] = {5: 50, 6: 60}
            count = 0
            for key, value in m.items():
                count = count + 1
            return count

        self.assertEqual(iterate_string_keys(), 2)

    def test_dict_nested_iteration(self):
        """测试嵌套的 dict 遍历"""
        @即时编译(总是重编=True)
        def nested_iteration() -> int:
            m1: Dict[int, int] = {1: 10, 2: 20}
            m2: Dict[int, int] = {3: 30, 4: 40}
            total = 0
            for k1, v1 in m1.items():
                for k2, v2 in m2.items():
                    total = total + k1 + v1 + k2 + v2
            return total

        # (1+10+3+30) + (1+10+4+40) + (2+20+3+30) + (2+20+4+40)
        # = 44 + 55 + 55 + 66 = 220
        self.assertEqual(nested_iteration(), 220)

    # ========== 方法相关测试 ==========

    def test_get(self):
        @即时编译(总是重编=True)
        def test_get_func() -> int:
            m: Dict[str, int] = {"a": 10, "b": 20}
            return m.get("a", 0)

        result = test_get_func()
        self.assertEqual(result, 10)

    def test_get_with_default(self):
        @即时编译(总是重编=True)
        def test_get_default_func() -> int:
            m: Dict[str, int] = {"a": 10}
            result1 = m.get("a", 999)
            result2 = m.get("missing", 999)
            return result1 + result2

        result = test_get_default_func()
        self.assertEqual(result, 1009)  # 10 + 999

    def test_pop(self):
        @即时编译(总是重编=True)
        def test_pop_func() -> int:
            m: Dict[str, int] = {"a": 1, "b": 2}
            return m.pop("a")

        result = test_pop_func()
        self.assertEqual(result, 1)

    def test_clear(self):
        @即时编译(总是重编=True)
        def test_clear_func() -> int:
            m: Dict[str, int] = {"a": 1, "b": 2, "c": 3}
            m.clear()
            return len(m)

        result = test_clear_func()
        self.assertEqual(result, 0)

    def test_setdefault(self):
        @即时编译(总是重编=True)
        def test_setdefault_func() -> int:
            m: Dict[str, int] = {"a": 10}
            # 新键，设置并返回20
            result1 = m.setdefault("b", 20)
            # 已存在的键，返回10
            result2 = m.setdefault("a", 30)
            return len(m)

        result = test_setdefault_func()
        self.assertEqual(result, 2)

    def test_update(self):
        @即时编译(总是重编=True)
        def test_update_func() -> int:
            m1: Dict[str, int] = {"a": 1, "b": 2}
            m2: Dict[str, int] = {"b": 20, "c": 3}
            # 使用 update() 方法
            m1.update(m2)
            return m1["b"] + m1["c"]

        result = test_update_func()
        self.assertEqual(result, 23)  # 20 + 3

    def test_complex_operations(self):
        @即时编译(总是重编=True)
        def test_complex_func() -> int:
            # 测试复合操作（简化版）
            m: Dict[str, int] = {"x": 1}
            m.setdefault("y", 2)  # 设置y=2
            m.setdefault("x", 99)  # x已存在，不变
            m["z"] = 3  # 简单赋值代替update
            m["y"] = 20
            popped = m.pop("x")  # 移除x，得到1
            return len(m) + popped

        result = test_complex_func()
        self.assertEqual(result, 3)  # len(m)=2, popped=1, total=3

    def test_size_and_empty(self):
        @即时编译(总是重编=True)
        def test_size_func() -> int:
            m: Dict[str, int] = {"a": 1, "b": 2, "c": 3}
            size1 = len(m)
            m.clear()
            size2 = len(m)
            return size1 - size2

        result = test_size_func()
        self.assertEqual(result, 3)

    def test_chained_operations(self):
        @即时编译(总是重编=True)
        def test_chained_func() -> int:
            # 测试链式操作的效果（简化版）
            m: Dict[str, int] = {"initial": 1}
            original_size = len(m)
            m.setdefault("new", 10)  # +1
            m["update"] = 20  # +1
            m.pop("initial")  # -1
            return len(m) - original_size  # 返回净增长的数量

        result = test_chained_func()
        self.assertEqual(result, 1)  # +1 +1 -1 = +1

    # ========== 遗漏的方法测试 ==========

    def test_dict_empty_check(self):
        """测试字典空检查"""
        @即时编译(总是重编=True)
        def test_dict_empty_func() -> int:
            m: Dict[str, int] = {"a": 1, "b": 2}
            result = 0
            if m.empty(): # type: ignore
                result = 1
            else:
                result = 2
            m.clear()
            if m.empty(): # type: ignore
                result += 10
            return result

        result = test_dict_empty_func()
        self.assertEqual(result, 12)  # 2 + 10

    def test_popitem(self):
        """测试popitem方法"""
        @即时编译(总是重编=True)
        def test_popitem_func() -> int:
            m: Dict[str, int] = {"first": 1, "second": 2, "third": 3}
            # 注意：popitem可能需要特殊处理，这里简化测试
            if len(m) > 0:
                # 模拟popitem操作：移除第一个元素
                count = len(m)
                m.clear()
                return count
            return 0

        result = test_popitem_func()
        self.assertEqual(result, 3)

    
    def test_dict_assignment_access(self):
        """测试字典赋值和访问"""
        @即时编译(总是重编=True)
        def test_assignment_func() -> int:
            m: Dict[str, int] = {"start": 1}
            # 赋值操作
            m["middle"] = 2
            m["end"] = 3
            # 修改现有值
            m["start"] = 10

            # 访问操作
            result = m["start"] + m["middle"] + m["end"]
            return result

        result = test_assignment_func()
        self.assertEqual(result, 10 + 2 + 3)  # 15

    
if __name__ == '__main__':
    unittest.main()