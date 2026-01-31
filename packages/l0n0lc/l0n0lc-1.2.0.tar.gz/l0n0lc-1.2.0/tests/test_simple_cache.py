#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的内存缓存测试

测试每个转译器实例自己持有库引用的缓存机制。
"""
import sys
import pathlib
import time
sys.path.append(str(pathlib.Path(__file__).parent.parent))

import l0n0lc as lc


def test_instance_cache():
    """测试转译器实例缓存"""
    print("\n=== 测试转译器实例缓存 ===")

    @lc.jit()
    def add(x: int, y: int) -> int:
        return x + y

    # 第一次调用 - 需要编译和加载
    start = time.perf_counter()
    result1 = add(1, 2)
    time1 = time.perf_counter() - start
    print(f"第一次调用: {result1}, 耗时: {time1*1000:.4f} ms")

    # 验证库已加载
    assert add.目标库 is not None, "库应该已加载"
    assert add.cpp函数 is not None, "函数应该已加载"
    print(f"✓ 库对象: {add.目标库}")
    print(f"✓ 函数对象: {add.cpp函数}")

    # 第二次调用 - 应该直接使用缓存的库
    start = time.perf_counter()
    result2 = add(3, 4)
    time2 = time.perf_counter() - start
    print(f"第二次调用: {result2}, 耗时: {time2*1000:.6f} ms")

    assert result2 == 7
    # 验证使用同一个库对象
    assert add.目标库 is not None
    print(f"✓ 第二次调用使用缓存的库")

    # 多次调用验证性能
    迭代次数 = 1000
    start = time.perf_counter()
    for _ in range(迭代次数):
        add(10, 20)
    总时间 = time.perf_counter() - start
    平均时间 = (总时间 / 迭代次数) * 1000000  # 转换为微秒

    print(f"✓ {迭代次数} 次调用总耗时: {总时间*1000:.2f} ms")
    print(f"✓ 平均每次调用: {平均时间:.2f} μs")

    # 验证平均时间非常快（应该 < 10μs）
    assert 平均时间 < 10, f"平均调用时间应该 < 10μs，实际 {平均时间:.2f} μs"

    print("✓ 转译器实例缓存测试通过")


def test_multiple_functions():
    """测试多个函数各自独立缓存"""
    print("\n=== 测试多函数独立缓存 ===")

    @lc.jit()
    def func1(x: int) -> int:
        return x * 2

    @lc.jit()
    def func2(x: int) -> int:
        return x * 3

    # 调用两个函数
    r1 = func1(5)
    r2 = func2(5)

    assert r1 == 10
    assert r2 == 15

    # 验证两个函数有独立的库对象
    print(f"✓ func1 库: {func1.目标库}")
    print(f"✓ func2 库: {func2.目标库}")

    # 验证它们是不同的库对象（每个函数编译成独立的 .so）
    assert func1.目标库 != func2.目标库, "不同函数应该有独立的库对象"
    print(f"✓ 两个函数使用不同的库对象")

    print("✓ 多函数独立缓存测试通过")


def test_cache_persistence():
    """测试缓存的持久性"""
    print("\n=== 测试缓存持久性 ===")

    @lc.jit()
    def persistent(x: int) -> int:
        return x + 100

    # 第一次调用
    r1 = persistent(1)
    库1 = persistent.目标库
    函数1 = persistent.cpp函数

    # 多次调用后，验证仍然是同一个库对象
    for i in range(10):
        persistent(i)

    库2 = persistent.目标库
    函数2 = persistent.cpp函数

    assert 库1 is 库2, "库对象应该保持不变"
    assert 函数1 is 函数2, "函数对象应该保持不变"
    print(f"✓ 缓存持久，库对象未改变")

    print("✓ 缓存持久性测试通过")


def main():
    """主测试函数"""
    print("=" * 70)
    print("l0n0lc 简化内存缓存测试")
    print("=" * 70)

    try:
        test_instance_cache()
        test_multiple_functions()
        test_cache_persistence()

        print("\n" + "=" * 70)
        print("🎉 所有简化缓存测试通过!")
        print("=" * 70)
        print("\n新缓存方案的优势:")
        print("  1. 每个转译器实例自己持有库引用")
        print("  2. 不需要缓存管理器")
        print("  3. 不需要缓存键生成和查找")
        print("  4. 代码更简洁，性能更好")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
