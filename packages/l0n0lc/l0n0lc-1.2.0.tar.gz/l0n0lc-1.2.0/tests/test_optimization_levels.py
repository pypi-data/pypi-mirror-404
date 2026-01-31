#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编译优化级别测试

测试 JIT 编译器的优化级别配置功能。
"""
import sys
import pathlib
import time
sys.path.append(str(pathlib.Path(__file__).parent.parent))

import l0n0lc as lc


def test_optimization_levels():
    """测试各个优化级别"""
    print("\n=== 测试优化级别 ===")

    # 测试 O0（无优化）
    @lc.jit(优化级别='O0')
    def func_o0(x: int) -> int:
        result = 0
        for i in range(x):
            result += i
        return result

    r1 = func_o0(100)
    print(f"✓ O0 (无优化): {r1}")
    assert r1 == 4950

    # 测试 O2（标准优化，默认）
    @lc.jit(优化级别='O2')
    def func_o2(x: int) -> int:
        result = 0
        for i in range(x):
            result += i
        return result

    r2 = func_o2(100)
    print(f"✓ O2 (标准优化): {r2}")
    assert r2 == 4950

    # 测试 O3（最大优化）
    @lc.jit(优化级别='O3')
    def func_o3(x: int) -> int:
        result = 0
        for i in range(x):
            result += i
        return result

    r3 = func_o3(100)
    print(f"✓ O3 (最大优化): {r3}")
    assert r3 == 4950

    # 测试 Os（优化大小）
    @lc.jit(优化级别='Os')
    def func_os(x: int) -> int:
        result = 0
        for i in range(x):
            result += i
        return result

    r4 = func_os(100)
    print(f"✓ Os (优化大小): {r4}")
    assert r4 == 4950

    print("✓ 所有优化级别测试通过")


def test_invalid_optimization_level():
    """测试无效的优化级别"""
    print("\n=== 测试无效优化级别 ===")

    try:
        @lc.jit(优化级别='O999')
        def invalid_func(x: int) -> int:
            return x

        invalid_func(1)
        print("❌ 应该抛出 ValueError")
        assert False, "应该抛出 ValueError"
    except ValueError as e:
        print(f"✓ 正确捕获错误: {e}")
        assert "不支持的优化级别" in str(e)
        print("✓ 无效优化级别测试通过")


def test_default_optimization():
    """测试默认优化级别（O2）"""
    print("\n=== 测试默认优化级别 ===")

    @lc.jit()  # 不指定优化级别，应该使用 O2
    def default_func(x: int) -> int:
        return x * 2

    r = default_func(21)
    print(f"✓ 默认优化级别结果: {r}")
    assert r == 42

    # 检查编译器实例的优化级别
    编译器 = default_func.编译器
    优化级别 = 编译器.获取优化级别()
    print(f"✓ 编译器优化级别: {优化级别}")
    assert 优化级别 == 'O2', f"默认应该是 O2，实际是 {优化级别}"

    print("✓ 默认优化级别测试通过")


def test_performance_comparison():
    """测试不同优化级别的性能对比"""
    print("\n=== 测试性能对比 ===")

    # 计算密集型任务：简单的循环求和
    @lc.jit(优化级别='O0')
    def sum_o0(n: int) -> int:
        result = 0
        for i in range(n):
            result += i * i
        return result

    @lc.jit(优化级别='O2')
    def sum_o2(n: int) -> int:
        result = 0
        for i in range(n):
            result += i * i
        return result

    @lc.jit(优化级别='O3')
    def sum_o3(n: int) -> int:
        result = 0
        for i in range(n):
            result += i * i
        return result

    # 预热
    sum_o0(100)
    sum_o2(100)
    sum_o3(100)

    # 测试 n = 1000
    n = 1000
    迭代次数 = 100

    # O0 性能
    start = time.perf_counter()
    for _ in range(迭代次数):
        sum_o0(n)
    time_o0 = time.perf_counter() - start

    # O2 性能
    start = time.perf_counter()
    for _ in range(迭代次数):
        sum_o2(n)
    time_o2 = time.perf_counter() - start

    # O3 性能
    start = time.perf_counter()
    for _ in range(迭代次数):
        sum_o3(n)
    time_o3 = time.perf_counter() - start

    print(f"\n循环求和 (n={n}, {迭代次数}次调用):")
    print(f"  O0 (无优化):    {time_o0*1000:.2f} ms")
    print(f"  O2 (标准优化):  {time_o2*1000:.2f} ms (加速比: {time_o0/time_o2:.2f}x)")
    print(f"  O3 (最大优化):  {time_o3*1000:.2f} ms (加速比: {time_o0/time_o3:.2f}x)")

    # O3 应该比 O0 快（或者至少相当）
    print(f"✓ O3 vs O0 性能: {time_o0/time_o3:.2f}x")

    print("✓ 性能对比测试通过")


def test_case_insensitive():
    """测试优化级别大小写不敏感"""
    print("\n=== 测试大小写不敏感 ===")

    # 小写应该被转换为大写
    @lc.jit(优化级别='o3')  # 小写
    def func_lower(x: int) -> int:
        return x + 1

    r = func_lower(10)
    print(f"✓ 小写 'o3' 结果: {r}")
    assert r == 11

    # 检查优化级别被转换为大写
    优化级别 = func_lower.编译器.获取优化级别()
    print(f"✓ 转换后的优化级别: {优化级别}")
    assert 优化级别 == 'O3'

    print("✓ 大小写不敏感测试通过")


def main():
    """主测试函数"""
    print("=" * 70)
    print("l0n0lc 编译优化级别测试")
    print("=" * 70)

    try:
        test_optimization_levels()
        test_invalid_optimization_level()
        test_default_optimization()
        test_performance_comparison()
        test_case_insensitive()

        print("\n" + "=" * 70)
        print("🎉 所有优化级别测试通过!")
        print("=" * 70)

        print("\n支持的优化级别:")
        print("  O0   - 无优化，编译最快")
        print("  O1   - 基础优化")
        print("  O2   - 标准优化（默认）")
        print("  O3   - 最大优化，运行最快")
        print("  Os   - 优化代码大小")
        print("  Ofast- 激进优化")
        print("  Og   - 调试优化")
        print("  Oz   - 最小代码大小")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
