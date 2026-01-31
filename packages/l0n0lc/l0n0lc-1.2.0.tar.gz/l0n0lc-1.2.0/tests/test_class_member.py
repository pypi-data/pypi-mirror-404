from enum import IntEnum
import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).parent.parent))
import l0n0lc as lc
import os

if not os.path.exists('./l0n0lcoutput'):
    os.mkdir('./l0n0lcoutput')


# 测试 1: enum class 成员访问
with open(f'./l0n0lcoutput/test_class2.h', 'w') as fp:
    fp.write('''
#pragma once
#include <cstdint>
enum class TPosition : uint8_t {
      GM,
      A1,
};
''')

@lc.映射类型('TPosition', ['"test_class2.h"'])
class TPosition(IntEnum):
    GM = 0               # Global Memory
    A1 = 1               # L1 Buffer

@lc.即时编译(总是重编=True)
def test_enum_class()->int:
    return int(TPosition.GM)

gm = test_enum_class()
print('Test 1 - TPosition::GM = ', gm)
assert gm == 0, f"Expected 0, got {gm}"


# 测试 2: 带静态成员和静态方法的类（内联定义以避免链接问题）
with open(f'./l0n0lcoutput/test_static_class2.h', 'w') as fp:
    fp.write('''
#pragma once
#include <cstdint>

struct TestStaticClass2 {
    static constexpr int64_t static_value = 42;

    static int64_t get_static_value() {
        return static_value;
    }

    static int64_t add(int64_t a, int64_t b) {
        return a + b;
    }
};
''')

@lc.映射类型('TestStaticClass2', ['"test_static_class2.h"'])
class TestStaticClass2:
    static_value = 0
    
    @staticmethod
    def get_static_value()->int:
        return int(0)
        
    @staticmethod
    def add(a, b)->int:
        return int(0)

@lc.即时编译(总是重编=True)
def test_static_member_access()->int:
    # 测试访问静态成员
    return TestStaticClass2.static_value

@lc.即时编译(总是重编=True)
def test_static_method_call()->int:
    # 测试调用静态方法
    return TestStaticClass2.get_static_value()

@lc.即时编译(总是重编=True)
def test_static_method_with_args()->int:
    # 测试调用带参数的静态方法
    return TestStaticClass2.add(10, 20)

result1 = test_static_member_access()
print('Test 2a - 静态成员访问:', result1)
assert result1 == 42, f"Expected 42, got {result1}"

result2 = test_static_method_call()
print('Test 2b - 静态方法调用:', result2)
assert result2 == 42, f"Expected 42, got {result2}"

result3 = test_static_method_with_args()
print('Test 2c - 静态方法带参数:', result3)
assert result3 == 30, f"Expected 30, got {result3}"

print('All tests passed!')

