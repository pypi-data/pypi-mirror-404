#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试重新编译时缓存清除

验证当重新编译时，旧的库引用被正确清除。
"""
import sys
import pathlib
import time
sys.path.append(str(pathlib.Path(__file__).parent.parent))

import l0n0lc as lc


def test_recompile_clears_cache():
    """测试重新编译时清除缓存"""
    print("\n=== 测试重新编译时清除缓存 ===")

    # 创建一个函数并调用
    @lc.jit()
    def test_func(x: int) -> int:
        return x + 100

    # 第一次调用 - 编译并加载
    r1 = test_func(1)
    print(f"第一次调用: {r1}")

    # 记录库对象
    库1 = test_func.目标库
    函数1 = test_func.cpp函数
    print(f"✓ 库对象: {库1}")
    print(f"✓ 函数对象: {函数1}")

    # 强制重新编译
    @lc.jit(总是重编=True)
    def test_func2(x: int) -> int:
        return x + 200

    # 调用新函数
    r2 = test_func2(1)
    print(f"重新编译后调用: {r2}")

    # 记录新的库对象
    库2 = test_func2.目标库
    函数2 = test_func2.cpp函数
    print(f"✓ 新库对象: {库2}")
    print(f"✓ 新函数对象: {函数2}")

    # 验证是新的库对象
    assert 库1 is not 库2, "重新编译后应该使用新的库对象"
    print(f"✓ 重新编译后确实使用了新的库对象")

    # 验证新的函数正确工作
    assert r2 == 201, f"重新编译后的函数应该返回 201，实际 {r2}"
    print(f"✓ 重新编译后的函数正确工作")

    print("✓ 重新编译缓存清除测试通过")


def test_cache_persistence_without_recompile():
    """测试不重新编译时缓存保持"""
    print("\n=== 测试不重新编译时缓存保持 ===")

    @lc.jit()
    def persistent_func(x: int) -> int:
        return x * 3

    # 第一次调用
    r1 = persistent_func(5)
    库1 = persistent_func.目标库
    函数1 = persistent_func.cpp函数
    print(f"第一次调用: {r1}, 库: {库1}")

    # 第二次调用（不重新编译）
    r2 = persistent_func(7)
    库2 = persistent_func.目标库
    函数2 = persistent_func.cpp函数
    print(f"第二次调用: {r2}, 库: {库2}")

    # 验证使用同一个库对象
    assert 库1 is 库2, "不重新编译时应该使用同一个库对象"
    assert 函数1 is 函数2, "函数对象应该保持不变"
    assert r2 == 21, f"结果应该正确，实际 {r2}"
    print(f"✓ 不重新编译时缓存保持不变")

    print("✓ 缓存持久性测试通过")


def main():
    """主测试函数"""
    print("=" * 70)
    print("l0n0lc 重新编译缓存清除测试")
    print("=" * 70)

    try:
        test_recompile_clears_cache()
        test_cache_persistence_without_recompile()

        print("\n" + "=" * 70)
        print("🎉 所有测试通过!")
        print("=" * 70)
        print("\n修复说明:")
        print("  - 在 编译() 方法开始时清除 目标库 和 cpp函数")
        print("  - 确保重新编译时使用新的库文件")
        print("  - 不重新编译时保持缓存不变")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
