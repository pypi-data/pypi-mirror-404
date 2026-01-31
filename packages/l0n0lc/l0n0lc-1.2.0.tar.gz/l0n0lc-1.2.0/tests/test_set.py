import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).parent.parent))

from typing import Set
from l0n0lc import jit
from l0n0lc.即时编译 import 即时编译
import unittest

class TestSet(unittest.TestCase):
    """测试集合功能，包括基础操作、元组支持和迭代"""

    # ========== 基础操作测试 ==========

    def test_set_creation(self):
        @即时编译(总是重编=True)
        def create_set() -> int:
            s = {1, 2, 3}
            return len(s)

        self.assertEqual(create_set(), 3)

    def test_set_add(self):
        @即时编译(总是重编=True)
        def test_add() -> int:
            s = {1, 2, 3}
            s.add(4)
            return len(s)

        self.assertEqual(test_add(), 4)

    def test_set_membership(self):
        @即时编译(总是重编=True)
        def test_membership() -> int:
            s = {1, 2, 3, 4, 5}
            count = 0
            if 1 in s:
                count += 1
            if 5 not in s:
                count += 10
            return count

        self.assertEqual(test_membership(), 1)

    def test_set_discard(self):
        @即时编译(总是重编=True)
        def test_discard() -> int:
            s = {1, 2, 3, 4, 5}
            # 测试 discard 方法
            s.discard(10)  # 不存在的元素
            s.discard(1)   # 存在的元素
            return len(s)

        self.assertEqual(test_discard(), 4)

    def test_set_pop(self):
        @即时编译(总是重编=True)
        def test_pop() -> int:
            s = {1, 2, 3}
            if len(s) > 0:
                popped = s.pop()
                return len(s)
            return len(s)

        # 集合pop后长度减1
        self.assertEqual(test_pop(), 2)

    def test_set_clear(self):
        @即时编译(总是重编=True)
        def test_clear() -> int:
            s = {1, 2, 3, 4, 5}
            s.clear()
            return len(s)

        self.assertEqual(test_clear(), 0)

    # ========== 集合方法测试 ==========

    def test_set_remove(self):
        @jit(总是重编=True)
        def test_remove_func() -> int:
            s = {1, 2, 3, 4, 5}
            s.remove(1)
            return len(s)

        result = test_remove_func()
        self.assertEqual(result, 4)

    def test_set_copy(self):
        @jit(总是重编=True)
        def test_copy_func() -> int:
            s = {1, 2, 3, 4, 5}
            s_copy = s.copy()
            return len(s_copy)

        result = test_copy_func()
        self.assertEqual(result, 5)

    # ========== 迭代测试 ==========

    def test_set_iteration(self):
        @即时编译(总是重编=True)
        def test_iteration() -> int:
            s = {1, 2, 3, 4, 5}
            count = 0
            for item in s:
                count += 1
            return count

        self.assertEqual(test_iteration(), 5)

    def test_set_iterations_mixed(self):
        @jit(总是重编=True)
        def test_set_iterations() -> int:
            """测试集合迭代功能"""
            s_int = {1, 2, 3, 4, 5}
            s_mixed = {10, 20, 30}

            count = 0
            for item in s_int:
                count += 1

            for item in s_mixed:
                count += 1

            return count

        result = test_set_iterations()
        self.assertEqual(result, 8)  # 5 + 3

    # ========== 复合操作测试 ==========

    def test_set_complex_operations(self):
        @jit(总是重编=True)
        def test_enhanced_set_methods() -> int:
            """测试新添加的集合方法"""
            s = {1, 2, 3, 4, 5}
            s.add(6)
            s.remove(1)
            s.discard(100)  # 不存在的元素
            s.discard(2)    # 存在的元素

            if len(s) > 0:
                s.pop()

            s_copy = s.copy()
            s.clear()

            return len(s_copy)

        result = test_enhanced_set_methods()
        # 原始5个，add(6)=6, remove(1)=5, discard(2)=4, pop()=3, copy()=3, clear()=0
        self.assertEqual(result, 3)

    def test_set_edge_cases(self):
        @jit(总是重编=True)
        def test_set_edge_cases() -> int:
            """测试集合边界情况"""
            # 测试单个元素
            single = {99}

            # 测试重复元素（自动去重）
            duplicates = {1, 1, 2, 2, 3}

            # 测试多个集合操作
            set_a = {10, 20, 30}
            set_b = {20, 30, 40}
            set_c = {30, 40, 50}

            # 测试集合元素遍历
            test_set = {100, 200, 300}
            count = 0
            for item in test_set:
                count += 1

            return len(single) + len(duplicates) + len(set_a) + len(set_b) + len(set_c) + count

        result = test_set_edge_cases()
        self.assertEqual(result, 1 + 3 + 3 + 3 + 3 + 3)  # 16

    # ========== 元组支持测试 ==========

    def test_tuple_support(self):
        @jit(总是重编=True)
        def test_tuple() -> int:
            t = (1, 2)
            result = t[0] + t[1]
            t2 = (1, "hello")
            return result

        self.assertEqual(test_tuple(), 3)

    def test_tuple_operations_basic(self):
        @即时编译(总是重编=True)
        def test_set_tuple() -> int:
            # Test Set
            s = {1, 2, 3}
            s.add(4)

            if 1 in s:
                print("1 is in set")
            else:
                print("1 is not in set")

            if 5 in s:
                print("5 is in set")
            else:
                print("5 is not in set")

            # 测试集合大小
            print("Set size:", len(s))

            # 测试 discard 方法
            s.discard(10)  # 不存在的元素
            s.discard(1)   # 存在的元素
            print("After discard(1), set size:", len(s))

            # 测试 pop 方法
            if len(s) > 0:
                popped = s.pop()
                print("Popped element:", popped)
                print("Remaining set size:", len(s))

            # 测试 clear 方法
            s.clear()
            print("After clear, set size:", len(s))

            # 重新创建集合进行集合运算测试
            s1 = {1, 2, 3, 4}
            s2 = {3, 4, 5, 6}

            t = (1, 2)
            print("Tuple (vector) element 0:", t[0])
            t2 = (1, "hello")

            return 0

        # 这里只是验证函数能正确编译和运行
        self.assertEqual(test_set_tuple(), 0)

    # ========== 集合操作测试 ==========

    def test_set_operations_basic(self):
        @jit(总是重编=True)
        def test_set_operations_basic() -> int:
            """测试基本集合操作"""
            # 创建测试集合
            set1 = {1, 2, 3, 4, 5}
            set2 = {3, 4, 5, 6, 7}

            count = 0
            # 测试成员检查
            test_values = [1, 3, 5, 7]
            for val in test_values:
                if val in set1:
                    count += 1
                if val in set2:
                    count += 1

            return count

        result = test_set_operations_basic()
        # 1: 在set1中, 3: 在两个集合中, 5: 在两个集合中, 7: 在set2中 = 1+2+2+1 = 6
        self.assertEqual(result, 6)

    def test_set_modifications(self):
        @jit(总是重编=True)
        def test_set_modifications() -> int:
            """测试集合修改操作"""
            # 测试 add
            s = {1, 2, 3}
            s.add(4)

            # 测试 remove
            s.remove(1)

            # 测试 discard
            s.discard(10)  # 不存在的元素
            s.discard(2)   # 存在的元素

            # 测试 pop
            if len(s) > 0:
                s.pop()

            # 测试 clear
            s.clear()

            return len(s)

        result = test_set_modifications()
        self.assertEqual(result, 0)

    # ========== 遗漏的方法测试 ==========

    def test_set_empty_check(self):
        """测试集合空检查"""
        @即时编译(总是重编=True)
        def test_set_empty_func() -> int:
            s = {1, 2, 3}
            result = 0
            if s.empty(): # type: ignore
                result = 1
            else:
                result = 2
            s.clear()
            if s.empty(): # type: ignore
                result += 10
            return result

        result = test_set_empty_func()
        self.assertEqual(result, 12)  # 2 + 10

    def test_set_operations_union(self):
        """测试集合并集操作"""
        @即时编译(总是重编=True)
        def test_union_func() -> int:
            s1 = {1, 2, 3}
            s2 = {3, 4, 5}
            # 使用 union() 方法（不修改原集合）
            union_set = s1.union(s2)
            return len(union_set)

        result = test_union_func()
        self.assertEqual(result, 5)  # {1, 2, 3, 4, 5}

    def test_set_operations_update(self):
        """测试集合update操作（就地修改）"""
        @即时编译(总是重编=True)
        def test_update_func() -> int:
            s1 = {1, 2, 3}
            s2 = {3, 4, 5}
            # 使用 update() 方法（修改原集合）
            s1.update(s2)
            return len(s1)

        result = test_update_func()
        self.assertEqual(result, 5)  # {1, 2, 3, 4, 5}

    def test_set_operations_intersection(self):
        """测试集合交集操作"""
        @即时编译(总是重编=True)
        def test_intersection_func() -> int:
            s1 = {1, 2, 3, 4}
            s2 = {3, 4, 5, 6}
            # 使用 intersection() 方法
            intersection_set = s1.intersection(s2)
            return len(intersection_set)

        result = test_intersection_func()
        self.assertEqual(result, 2)  # {3, 4}

    def test_set_operations_difference(self):
        """测试集合差集操作"""
        @即时编译(总是重编=True)
        def test_difference_func() -> int:
            s1 = {1, 2, 3, 4}
            s2 = {3, 4, 5, 6}
            # 使用 difference() 方法
            difference_set = s1.difference(s2)
            return len(difference_set)

        result = test_difference_func()
        self.assertEqual(result, 2)  # {1, 2}

    def test_set_relationships(self):
        """测试集合关系操作"""
        @即时编译(总是重编=True)
        def test_relationships_func() -> int:
            s1 = {1, 2}
            s2 = {1, 2, 3, 4}
            s3 = {5, 6}

            result = 0

            # 使用 issubset() 方法检查子集关系
            if s1.issubset(s2):
                result += 1

            # 使用 isdisjoint() 方法检查不相交关系
            if s1.isdisjoint(s3):
                result += 10

            return result

        result = test_relationships_func()
        self.assertEqual(result, 11)  # 1 + 10

if __name__ == '__main__':
    unittest.main()