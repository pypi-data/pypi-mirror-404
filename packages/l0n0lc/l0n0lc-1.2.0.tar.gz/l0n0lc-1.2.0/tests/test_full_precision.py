#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""完整测试所有精度类型"""
import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).parent.parent))

from l0n0lc import *

@jit(总是重编=True)
def test_precision_creation():
    # 创建实例
    a = int8(100)
    b = int8(27)
    result = a + b
    print(int(a), '(int8)+', int(b), '(int8)=', int(result))
    # 测试不同精度类型间的运算
    c = int16(1000)
    d = int32(5000)
    result2 = c + d
    print(int(c), '(int16)+', int(d), '(int32)=', result2)
    # 测试浮点运算
    e = float64(3.14159)
    f = float64(2.71828)
    result3 = e * f
    print(e, '(float64)*', f, '(float64)=', result3)
    # 测试无符号整数
    g = uint16(50000)
    h = uint16(10000)
    result4 = g - h
    print(g, '(uint16)-', h, '(uint16)=', result4)
    # 测试与普通数值的运算
    result5 = a + 50  # int8 + int
    print(int(a), '(int8)+', 50, '(int)=', result5)
    result6 = 100 + a  # int + int8
    print(100, '(int)+', int(a), '(int8)=', result6)


if __name__ == "__main__":
    test_precision_creation()
