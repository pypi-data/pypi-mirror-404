from .工具 import 映射函数, 映射类型
import ctypes
from typing import SupportsIndex
from .cpp类型 import *

class _数值类型基类(SupportsIndex):
    """数值类型基类，提供通用的运算符支持"""

    def __init__(self, value):
        pass
        
    def __index__(self) -> int:
        return 0

    # 基本运算
    def __add__(self, other): return self
    def __sub__(self, other): return self
    def __mul__(self, other): return self
    def __truediv__(self, other): return self
    def __floordiv__(self, other): return self
    def __mod__(self, other): return self
    def __pow__(self, other): return self
    def __neg__(self): return self
    def __abs__(self): return self
    
    # 比较运算
    def __eq__(self, other): return self
    def __ne__(self, other): return self
    def __lt__(self, other): return self
    def __le__(self, other): return self
    def __gt__(self, other): return self
    def __ge__(self, other): return self

    # 反向运算符（支持左操作数为普通数值的情况）
    def __radd__(self, other): return self
    def __rsub__(self, other): return self
    def __rmul__(self, other): return self
    def __rtruediv__(self, other): return self
    def __rfloordiv__(self, other): return self
    def __rmod__(self, other): return self
    def __rpow__(self, other): return self

    # 类型转换
    def __int__(self): return int(0)
    def __float__(self): return float(0)


# 设置全局变量
int映射目标 = Cpp类型.INT64_T
float映射目标 = Cpp类型.FLOAT64

# 基础类型映射
# str 类型映射为 const char* (C 接口)，但在 C++ 内部使用 std::string
映射类型(Cpp类型.静态字符串, ['<string>'], ctypes类型=ctypes.c_char_p)(str)
映射类型(Cpp类型.StdString, ['<string>'], ctypes类型=None)(CString常量)
映射类型(Cpp类型.字符串, ctypes类型=ctypes.c_char_p)(bytes)
映射类型(Cpp类型.字符串, ctypes类型=ctypes.c_char_p)(CBytes常量)
映射类型(Cpp类型.INT64_T, ctypes类型=ctypes.c_int64)(int)
映射类型(Cpp类型.INT64_T, ctypes类型=ctypes.c_int64)(CInt常量)
映射类型(Cpp类型.FLOAT64, ctypes类型=ctypes.c_double)(float)
映射类型(Cpp类型.FLOAT64, ctypes类型=ctypes.c_double)(CFloat常量)
映射类型(Cpp类型.布尔, ctypes类型=ctypes.c_bool)(bool)
映射类型(Cpp类型.布尔, ctypes类型=ctypes.c_bool)(C布尔)

# 数值类型映射
@映射类型(Cpp类型.INT8_T, ctypes类型=ctypes.c_int8)
class int8(_数值类型基类):
    pass

@映射类型(Cpp类型.INT16_T, ctypes类型=ctypes.c_int16)
class int16(_数值类型基类):
    pass

@映射类型(Cpp类型.INT32_T, ctypes类型=ctypes.c_int32)
class int32(_数值类型基类):
    pass

@映射类型(Cpp类型.INT64_T, ctypes类型=ctypes.c_int64)
class int64(_数值类型基类):
    pass

@映射类型(Cpp类型.UINT8_T, ctypes类型=ctypes.c_uint8)
class uint8(_数值类型基类):
    pass

@映射类型(Cpp类型.UINT16_T, ctypes类型=ctypes.c_uint16)
class uint16(_数值类型基类):
    pass

@映射类型(Cpp类型.UINT32_T, ctypes类型=ctypes.c_uint32)
class uint32(_数值类型基类):
    pass

@映射类型(Cpp类型.UINT64_T, ctypes类型=ctypes.c_uint64)
class uint64(_数值类型基类):
    pass

@映射类型(Cpp类型.FLOAT32, ctypes类型=ctypes.c_float)
class float32(_数值类型基类):
    pass

@映射类型(Cpp类型.FLOAT64, ctypes类型=ctypes.c_double)
class float64(_数值类型基类):
    pass

# 指针类型基类
class _指针类型基类:
    """指针类型基类，提供通用的指针操作"""
    _值类型 = None  # 子类需要覆盖此属性
    
    def __getitem__(self, index):
        """解引用指针，返回对应的值类型"""
        return type(self)._值类型() # type: ignore
    
    def __setitem__(self, index, value):
        """设置指针指向的值"""
        pass

# 指针类型映射
@映射类型("int8_t*", ctypes类型=ctypes.c_void_p)
class int8_ptr(_指针类型基类):
    _值类型 = int8

@映射类型("int16_t*", ctypes类型=ctypes.c_void_p)
class int16_ptr(_指针类型基类):
    _值类型 = int16

@映射类型("int32_t*", ctypes类型=ctypes.c_void_p)
class int32_ptr(_指针类型基类):
    _值类型 = int32

@映射类型("int64_t*", ctypes类型=ctypes.c_void_p)
class int64_ptr(_指针类型基类):
    _值类型 = int64

@映射类型("uint8_t*", ctypes类型=ctypes.c_void_p)
class uint8_ptr(_指针类型基类):
    _值类型 = uint8

@映射类型("uint16_t*", ctypes类型=ctypes.c_void_p)
class uint16_ptr(_指针类型基类):
    _值类型 = uint16

@映射类型("uint32_t*", ctypes类型=ctypes.c_void_p)
class uint32_ptr(_指针类型基类):
    _值类型 = uint32

@映射类型("uint64_t*", ctypes类型=ctypes.c_void_p)
class uint64_ptr(_指针类型基类):
    _值类型 = uint64

@映射类型("float*", ctypes类型=ctypes.c_void_p)
class float32_ptr(_指针类型基类):
    _值类型 = float32

@映射类型("double*", ctypes类型=ctypes.c_void_p)
class float64_ptr(_指针类型基类):
    _值类型 = float64

@映射类型("bool*", ctypes类型=ctypes.c_void_p)
class bool_ptr(_指针类型基类):
    _值类型 = bool

@映射类型("char*", ctypes类型=ctypes.c_char_p)
class char_ptr(_指针类型基类):
    _值类型 = str

@映射类型("const char*", ctypes类型=ctypes.c_char_p)
class const_char_ptr(_指针类型基类):
    _值类型 = str

@映射类型("void*", ctypes类型=ctypes.c_void_p)
class void_ptr(_指针类型基类):
    _值类型 = None

@映射类型("typename")(type)

@映射函数(print, ['<iostream>'])
def cpp_cout(*args):
    if len(args) == 0:
        return ''
    code = ['std::cout']
    for arg in args:
        code.append(f'<< {arg} << " "')
    code.append('<<std::endl;')
    return ''.join(code)

@映射函数(len)
def cpp_len(arg):
    return f'{arg}.size()'