"""测试 Array 固定大小数组类型"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from l0n0lc import jit, Array, int16

# 测试 1: 一维数组
@jit()
def test_array_basic() -> int:
    a = Array(int16, 3, [1, 2, 3])
    return a[0] + a[1] + a[2]

# 测试 2: 初始化列表长度小于数组大小（C++ 默认行为）
@jit()
def test_array_partial_init() -> int:
    a = Array(int, 5, [1, 2])
    # 剩余元素应该被初始化为 0
    return a[0] + a[1] + a[2] + a[3] + a[4]

# 测试 3: 单个值初始化
@jit()
def test_array_single_init() -> int:
    a = Array(int, 3, [0])
    return a[0] + a[1] + a[2]

# 测试 4: 数组元素修改
@jit()
def test_array_modify() -> int:
    a = Array(int, 3, [1, 2, 3])
    a[1] = 10
    return a[0] + a[1] + a[2]

# 测试 5: float 类型数组
@jit()
def test_array_float() -> float:
    a = Array(float, 3, [1.5, 2.5, 3.5])
    return a[0] + a[1] + a[2]

# 测试 6: 二维数组
@jit()
def test_array_2d() -> int:
    a = Array(Array(int, 3), 2, [[1, 2, 3], [4, 5, 6]])
    return a[0][0] + a[0][1] + a[0][2] + a[1][0] + a[1][1] + a[1][2]

# 测试 7: 不提供初始化列表（空数组）
@jit()
def test_array_no_init() -> int:
    a = Array(int, 3)
    return a[0] + a[1] + a[2]

if __name__ == "__main__":
    print("测试 1: 一维数组 Array(int16, 3, [1, 2, 3])")
    result = test_array_basic()
    print(f"  结果: {result} (期望: 6)")
    assert result == 6, f"测试 1 失败: 得到 {result}，期望 6"

    print("测试 2: 部分初始化 Array(int, 5, [1, 2])")
    result = test_array_partial_init()
    print(f"  结果: {result} (期望: 3)")
    assert result == 3, f"测试 2 失败: 得到 {result}，期望 3"

    print("测试 3: 单个值初始化 Array(int, 3, [0])")
    result = test_array_single_init()
    print(f"  结果: {result} (期望: 0)")
    assert result == 0, f"测试 3 失败: 得到 {result}，期望 0"

    print("测试 4: 数组元素修改")
    result = test_array_modify()
    print(f"  结果: {result} (期望: 14)")
    assert result == 14, f"测试 4 失败: 得到 {result}，期望 14"

    print("测试 5: float 类型数组")
    result = test_array_float()
    print(f"  结果: {result} (期望: 7.5)")
    assert abs(result - 7.5) < 0.001, f"测试 5 失败: 得到 {result}，期望 7.5"

    print("测试 6: 二维数组")
    result = test_array_2d()
    print(f"  结果: {result} (期望: 21)")
    assert result == 21, f"测试 6 失败: 得到 {result}，期望 21"

    print("测试 7: 不提供初始化列表（空数组）")
    result = test_array_no_init()
    print(f"  结果: {result} (期望: 随机)")

    print("\n所有测试通过!")
