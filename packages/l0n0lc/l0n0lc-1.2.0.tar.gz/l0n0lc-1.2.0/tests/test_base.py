import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).parent.parent))
import l0n0lc as lc
import math


@lc.映射函数(math.ceil, ['<cmath>'])
def cpp_ceil(v):
    return f'std::ceil({lc.转C字符串(v)});'

@lc.映射函数到('std::cout << u8"请输入>>>"; std::cin >> {v};', ['<iostream>'])
def cpp_cin(v):
    pass


    

@lc.可直接调用
def test_direct_call():
    return 123


def 测试自动编译(a: int, b: int) -> int:
    return a - b


@lc.即时编译(总是重编=True)
def test编译的函数(a: int, b: int) -> int:
    return a * b


@lc.映射类型('std::vector<int>', ['<vector>'])
class CppVectorInt:
    def push_back(self, v):
        pass

    def size(self):
        return 0

    def __getitem__(self, key):
        return 0


@lc.映射类型('short')
class ShortInt:
    def __init__(self, v) -> None:
        pass


@lc.即时编译(总是重编=True)
def jit_all_ops(a: int, b: int) -> int:
    # 常量与基础赋值
    x = 42
    y: int = a + b
    z = 3.14
    flag = True
    nums = [1, 2, 3]
    numsshorts = [ShortInt(1), ShortInt(2), ShortInt(3)]
    tup = (4, 5)
    mp = {1: 10, 2: 20}
    # 注释掉包含ShortInt的字典，避免NoneType问题
    # mp2 = {ShortInt(1): 10, ShortInt(2): 20}

    # 一元运算
    pos = +(a + 1)
    neg = -b
    inv = ~a
    not_flag = not flag

    # 二元运算
    add = a + b
    sub = a - b
    mul = a * b
    div = a / (b if b != 0 else 1)
    mod = a % (b if b != 0 else 1)
    band = a & b
    bor = a | b
    bxor = a ^ b
    lshift = a << 1
    rshift = a >> 1

    # 比较运算
    cmp1 = a == b
    cmp2 = a != b
    cmp3 = a < b
    cmp4 = a <= b
    cmp5 = a > b
    cmp6 = a >= b

    # 逻辑运算与三元表达式
    logic_and = cmp1 and cmp2
    logic_or = cmp3 or cmp4
    ternary = a if a > b else b

    # if / else
    if a > b:
        y += 1
    else:
        y -= 1

    # for 循环 range
    for i in range(3):
        y += i

    # for 循环 列表
    for v in nums:
        y += v
        if v == 2:
            continue
        if v == 3:
            break

    # while 循环
    count = 0
    while count < 2:
        y += count
        count += 1

    # 增强赋值
    y += 5
    y -= 1
    y *= 2
    y //= 2
    y %= 10
    y &= 7
    y |= 3
    y ^= 1
    y <<= 1
    y >>= 1

    # 下标访问
    first_num = nums[0]
    mp_val = mp[1]
    y += first_num + mp_val

    vector = CppVectorInt()
    vector.push_back(count)
    vector.push_back(y)
    for i in range(vector.size()):
        print('vector->', i, '=', vector[i])
    return y


@lc.即时编译(总是重编=True)
def test_add(a: int, b: int) -> int:
    if a > 1:
        return (a + b) * 123123
    for i in range(1, 10, 2):
        a += i
    for i in [1, 2, 3]:
        a += i
    a = math.ceil(12.5)
    cc = {'a': 1, 'b': 2}
    cc['c'] = 3
    print('输出map:')
    for k, v in cc:
        print(k, v)  # type: ignore
    aa = [1, 3, 2]
    aa[0] = 134
    print('输出list:')
    for i in range(3):
        print(i, aa[i])
    print('Hello World', a, b)
    print('test_other_fn', 测试自动编译(a, b))
    print('test编译的函数', test编译的函数(a, b))

    print('测试所有操作:')
    jit_all_ops(a, b)
    # vvv = 0
    # vv = True and (False or 1)
    # print('vv:', vv)
    # print('测试while:')
    # while vv:
    #     cpp_cin(vvv)
    #     if vvv > 100:
    #         break
    #     else:
    #         print('输入的', vvv, '小于等于100')
    return a + b + 1 + test_direct_call()


print('结果:', test_add(1, 3))
