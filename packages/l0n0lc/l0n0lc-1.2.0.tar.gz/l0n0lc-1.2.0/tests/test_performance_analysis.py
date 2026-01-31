#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能分析测试脚本 - 全面分析 l0n0lc JIT 编译器的性能表现

该脚本通过多种计算密集型任务来比较 Python 原生实现与 JIT 编译后的性能，
包括编译开销分析、不同类型计算的性能对比以及内存使用分析。
"""
import sys
import pathlib
import time
import gc
import statistics
from typing import Callable, Dict, List, Tuple, Any
sys.path.append(str(pathlib.Path(__file__).parent.parent))

import l0n0lc as lc


class PerformanceAnalyzer:
    """性能分析器类"""

    def __init__(self, warmup_iterations: int = 3, test_iterations: int = 100):
        self.warmup_iterations = warmup_iterations
        self.test_iterations = test_iterations
        self.results = {}

    def benchmark_function(self, func: Callable, *args, **kwargs) -> Dict[str, float]:
        """
        对函数进行性能基准测试

        Args:
            func: 要测试的函数
            *args, **kwargs: 函数参数

        Returns:
            包含各种性能指标的字典
        """
        # 预热
        for _ in range(self.warmup_iterations):
            func(*args, **kwargs)

        # 强制垃圾回收
        gc.collect()

        # 实际测试
        times = []
        for _ in range(self.test_iterations):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            times.append(end_time - start_time)

        # 计算统计信息
        return {
            'mean_time': statistics.mean(times),
            'median_time': statistics.median(times),
            'min_time': min(times),
            'max_time': max(times),
            'std_dev': statistics.stdev(times) if len(times) > 1 else 0,
            'total_time': sum(times),
            'result': result
        }

    def compare_functions(self, py_func: Callable, jit_func: Callable,
                         *args, **kwargs) -> Dict[str, Any]:
        """
        比较Python原生函数和JIT编译函数的性能

        Args:
            py_func: Python原生函数
            jit_func: JIT编译函数
            *args, **kwargs: 函数参数

        Returns:
            包含比较结果的字典
        """
        print(f"正在测试函数: {py_func.__name__}")

        # 测试Python版本
        py_stats = self.benchmark_function(py_func, *args, **kwargs)

        # 测试JIT版本（注意：JIT函数可能需要不同的调用方式）
        try:
            jit_stats = self.benchmark_function(jit_func, *args, **kwargs)
        except TypeError:
            # 如果参数数量不匹配，尝试通过__call__方式调用
            jit_wrapper = lambda *a, **k: jit_func(*a, **k)
            jit_stats = self.benchmark_function(jit_wrapper, *args, **kwargs)

        # 计算性能提升
        speedup = py_stats['mean_time'] / jit_stats['mean_time'] if jit_stats['mean_time'] > 0 else 0

        # 验证结果一致性
        results_match = abs(py_stats['result'] - jit_stats['result']) < 1e-10 if isinstance(py_stats['result'], (int, float)) else py_stats['result'] == jit_stats['result']

        comparison = {
            'function_name': py_func.__name__,
            'python_stats': py_stats,
            'jit_stats': jit_stats,
            'speedup': speedup,
            'results_match': results_match,
            'python_result': py_stats['result'],
            'jit_result': jit_stats['result']
        }

        self.results[py_func.__name__] = comparison
        return comparison

    def print_comparison(self, comparison: Dict[str, Any]):
        """打印性能比较结果"""
        name = comparison['function_name']
        py_stats = comparison['python_stats']
        jit_stats = comparison['jit_stats']
        speedup = comparison['speedup']

        print(f"\n{'='*60}")
        print(f"函数: {name}")
        print(f"{'='*60}")
        print(f"Python 平均时间: {py_stats['mean_time']*1000:.4f} ms")
        print(f"JIT 平均时间:    {jit_stats['mean_time']*1000:.4f} ms")
        print(f"性能提升:        {speedup:.2f}x")
        print(f"结果一致性:      {'✓' if comparison['results_match'] else '✗'}")
        if not comparison['results_match']:
            print(f"Python 结果: {comparison['python_result']}")
            print(f"JIT 结果:    {comparison['jit_result']}")
        print(f"Python 标准差:  {py_stats['std_dev']*1000:.4f} ms")
        print(f"JIT 标准差:     {jit_stats['std_dev']*1000:.4f} ms")

    def print_summary(self):
        """打印所有测试的总结"""
        print(f"\n{'='*80}")
        print("性能测试总结")
        print(f"{'='*80}")

        total_speedups = []
        for name, result in self.results.items():
            speedup = result['speedup']
            total_speedups.append(speedup)
            status = "✓" if result['results_match'] else "✗"
            print(f"{name:<30} | 性能提升: {speedup:>6.2f}x | 结果: {status}")

        if total_speedups:
            avg_speedup = statistics.mean(total_speedups)
            print(f"\n平均性能提升: {avg_speedup:.2f}x")
            print(f"最大性能提升: {max(total_speedups):.2f}x")
            print(f"最小性能提升: {min(total_speedups):.2f}x")


# ==================== 测试函数定义 ====================

# 1. 数学计算函数

def fibonacci_iterative_py(n: int) -> int:
    """Python实现的迭代斐波那契数列"""
    if n <= 1:
        return n
    a = 0
    b = 1
    for i in range(2, n + 1):
        temp = a + b
        a = b
        b = temp
    return b

@lc.jit()
def fibonacci_iterative_jit(n: int) -> int:
    """JIT实现的迭代斐波那契数列"""
    if n <= 1:
        return n
    a = 0
    b = 1
    for i in range(2, n + 1):
        temp = a + b
        a = b
        b = temp
    return b

def factorial_iterative_py(n: int) -> int:
    """Python实现的迭代阶乘"""
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

@lc.jit()
def factorial_iterative_jit(n: int) -> int:
    """JIT实现的迭代阶乘"""
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

def simple_prime_count_py(n: int) -> int:
    """Python实现的简单素数计数"""
    count = 0
    for i in range(2, n + 1):
        is_prime = True
        for j in range(2, i):
            if j * j > i:
                break
            if i % j == 0:
                is_prime = False
                break
        if is_prime:
            count += 1
    return count

@lc.jit()
def simple_prime_count_jit(n: int) -> int:
    """JIT实现的简单素数计数"""
    count = 0
    for i in range(2, n + 1):
        is_prime = True
        for j in range(2, i):
            if j * j > i:
                break
            if i % j == 0:
                is_prime = False
                break
        if is_prime:
            count += 1
    return count

# 2. 数组操作函数

def array_sum_py(data: List[int]) -> int:
    """Python实现的数组求和"""
    total = 0
    for x in data:
        total += x
    return total

@lc.jit()
def array_sum_jit(data: List[int]) -> int:
    """JIT实现的数组求和"""
    total = 0
    for x in data:
        total += x
    return total

def array_max_py(data: List[int]) -> int:
    """Python实现的数组最大值"""
    # 假设数组不为空以避免JIT兼容性问题
    max_val = data[0]
    for i in range(1, len(data)):
        x = data[i]
        if x > max_val:
            max_val = x
    return max_val

@lc.jit()
def array_max_jit(data: List[int]) -> int:
    """JIT实现的数组最大值"""
    # 假设数组不为空以避免JIT兼容性问题
    max_val = data[0]
    for i in range(1, len(data)):
        x = data[i]
        if x > max_val:
            max_val = x
    return max_val

# 3. 字符串操作函数
def char_count_py(text: bytes) -> int:
    """Python实现的字符计数"""
    return len(text)

@lc.映射函数到('strlen({v})', ['<cstring>'])
def strlen(v:bytes)->int:
    return 0

@lc.jit()
def char_count_jit(text: bytes) -> int:
    """JIT实现的字符计数（简化版本）"""
    # 由于JIT限制，使用简单的字符串长度计算
    return strlen(text)

# 4. 循环密集型函数

def nested_loops_py(n: int) -> int:
    """Python实现的嵌套循环"""
    count = 0
    for i in range(n):
        for j in range(n):
            count += i * j
    return count

@lc.jit()
def nested_loops_jit(n: int) -> int:
    """JIT实现的嵌套循环"""
    count = 0
    for i in range(n):
        for j in range(n):
            count += i * j
    return count

# 5. 数学计算密集型函数
def mathematical_computation_py(n: int) -> float:
    """Python实现的数学计算"""
    result = 0.0
    for i in range(1, n + 1):
        result += 1.0 / (i * i)
    return result

@lc.jit()
def mathematical_computation_jit(n: int) -> float:
    """JIT实现的数学计算"""
    result = 0.0
    for i in range(1, n + 1):
        result += 1.0 / (i * i)
    return result

# 5. 更高强度的计算密集型函数

def matrix_multiply_py(n: int) -> int:
    """Python实现的矩阵乘法（简化版）"""
    # 创建两个 n×n 矩阵并计算乘积的迹
    result = 0
    for i in range(n):
        for j in range(n):
            for k in range(n):
                result += (i + j) * (j + k)  # 模拟矩阵乘法
    return result

@lc.jit()
def matrix_multiply_jit(n: int) -> int:
    """JIT实现的矩阵乘法（简化版）"""
    result = 0
    for i in range(n):
        for j in range(n):
            for k in range(n):
                result += (i + j) * (j + k)
    return result

# 注释掉有问题的排序模拟函数，专注于其他可正常工作的测试
# def sorting_simulation_py(n: int) -> int:
#     """Python实现的排序模拟（选择排序）"""
#     pass

# @lc.jit()
# def sorting_simulation_jit(n: int) -> int:
#     """JIT实现的排序模拟（选择排序）"""
#     pass


# ==================== 编译开销分析 ====================

def analyze_compilation_overhead():
    """分析编译开销"""
    print(f"\n{'='*80}")
    print("编译开销分析")
    print(f"{'='*80}")

    # 测试编译时间
    @lc.jit()
    def test_compilation_func(x: int) -> int:
        return x * x + 2 * x + 1

    # 测试有缓存时的加载时间
    @lc.jit()
    def test_cached_func(x: int) -> int:
        return x * x + 2 * x + 1

    # 首次编译时间
    start = time.perf_counter()
    result1 = test_compilation_func(42)
    compilation_time = time.perf_counter() - start

    # 第二次调用时间（有缓存）
    start = time.perf_counter()
    result2 = test_compilation_func(42)
    cached_time = time.perf_counter() - start

    print(f"首次编译并执行时间: {compilation_time*1000:.4f} ms")
    print(f"缓存命中执行时间:   {cached_time*1000:.4f} ms")
    print(f"编译开销倍数:       {compilation_time/cached_time:.2f}x")
    print(f"函数结果: {result1}, {result2}")


# ==================== 主测试函数 ====================

def main():
    """主测试函数"""
    print("l0n0lc JIT 编译器性能分析测试")
    print("=" * 80)

    # 创建性能分析器 - 增加测试迭代次数以获得更准确的结果
    analyzer = PerformanceAnalyzer(warmup_iterations=5, test_iterations=20)

    # 准备测试数据 - 显著增加数据量
    small_array = list(range(1000))
    medium_array = list(range(10000))
    large_array = list(range(100000))
    huge_array = list(range(1000000))
    test_text = "The quick brown fox jumps over the lazy dog. " * 1000  # 更长的字符串

    # 测试用例列表 - 增加更具挑战性的数据量
    test_cases = [
        # 数学计算函数 - 增加计算复杂度
        (fibonacci_iterative_py, fibonacci_iterative_jit, (50,), {}, "迭代斐波那契数列 (n=50)"),
        (factorial_iterative_py, factorial_iterative_jit, (20,), {}, "迭代阶乘计算 (n=20)"),
        (simple_prime_count_py, simple_prime_count_jit, (500,), {}, "素数计数 (n=500)"),

        # 数组操作函数 - 使用更大的数组
        (array_sum_py, array_sum_jit, (small_array,), {}, "小数组求和 (1000个元素)"),
        (array_sum_py, array_sum_jit, (medium_array,), {}, "中数组求和 (10000个元素)"),
        (array_sum_py, array_sum_jit, (large_array,), {}, "大数组求和 (100000个元素)"),
        (array_sum_py, array_sum_jit, (huge_array,), {}, "巨大数组求和 (1000000个元素)"),
        (array_max_py, array_max_jit, (large_array,), {}, "数组最大值 (100000个元素)"),

        # 字符串操作
        (char_count_py, char_count_jit, (test_text,), {}, "长字符串字符计数"),

        # 循环密集型函数 - 显著增加计算量
        (nested_loops_py, nested_loops_jit, (100,), {}, "嵌套循环 (100x100)"),
        (nested_loops_py, nested_loops_jit, (200,), {}, "嵌套循环 (200x200)"),

        # 数学计算 - 增加迭代次数
        (mathematical_computation_py, mathematical_computation_jit, (5000,), {}, "数学计算 (1/求和, n=5000)"),
        (mathematical_computation_py, mathematical_computation_jit, (10000,), {}, "数学计算 (1/求和, n=10000)"),

        # 高强度计算密集型任务
        (matrix_multiply_py, matrix_multiply_jit, (20,), {}, "矩阵乘法模拟 (20x20x20)"),
        (matrix_multiply_py, matrix_multiply_jit, (50,), {}, "矩阵乘法模拟 (50x50x50)"),
        # 排序模拟暂时移除，因为JIT编译器对动态列表创建有兼容性问题
    ]

    # 执行性能测试
    for py_func, jit_func, args, kwargs, description in test_cases:
        try:
            print(f"\n正在测试: {description}")
            comparison = analyzer.compare_functions(py_func, jit_func, *args, **kwargs)
            analyzer.print_comparison(comparison)
        except Exception as e:
            print(f"测试失败: {description}")
            print(f"错误: {e}")

    # 分析编译开销
    analyze_compilation_overhead()

    # 打印总结
    analyzer.print_summary()

    # 输出生成的C++代码位置
    print(f"\n编译输出目录: l0n0lcoutput/")
    print("可以查看生成的C++代码以了解转换细节")


if __name__ == "__main__":
    main()