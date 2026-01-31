# l0n0lc

<div align="center">

**将 Python 函数翻译为 C++ 并运行的 JIT 编译器**

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.1.0-orange.svg)](pyproject.toml)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen.svg)](pyproject.toml)

</div>

## 简介

l0n0lc 是一个零外部依赖的 Python JIT 编译器，通过简单的装饰器将 Python 函数转换为原生 C++ 代码并编译执行。它专注于计算密集型任务的性能优化，同时保持 API 的简洁性和易用性。

### 核心特点

- **零依赖** - 仅依赖 Python 3.10+ 标准库
- **简单易用** - 一个 `@jit` 装饰器即可启用
- **智能缓存** - 基于源码哈希，自动避免重复编译
- **跨平台** - 支持 Linux、macOS、Windows
- **类型推断** - 自动推断变量类型，生成高效 C++ 代码

---

## 安装

```bash
pip install l0n0lc
```

### 系统要求

- Python 3.10 或更高版本
- C++ 编译器（g++、clang++ 或 c++）

```bash
# Ubuntu/Debian
sudo apt install g++

# macOS
xcode-select --install

# Windows (MSYS2)
pacman -S mingw-w64-x86_64-gcc
```

---

## 快速开始

### 基础用法

```python
from l0n0lc import jit

@jit()
def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

print(fibonacci(40))  # 输出: 102334155
```

### 容器类型支持

```python
from typing import List

@jit()
def sum_list(nums: List[int]) -> int:
    total = 0
    for num in nums:
        total += num
    return total

print(sum_list([1, 2, 3, 4, 5]))  # 输出: 15
```

### 类支持

```python
# 定义类（类本身不需要 jit 装饰器）
class Point:
    x: float
    y: float

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

@jit()
def compute_distance() -> float:
    # 在 JIT 函数内部创建和使用类实例
    p1 = Point(0.0, 0.0)
    p2 = Point(3.0, 4.0)
    dx = p1.x - p2.x
    dy = p1.y - p2.y
    return (dx * dx + dy * dy) ** 0.5

print(compute_distance())  # 输出: 25.0 (平方距离)
```

---

## API 参考

### @jit 装饰器

```python
@jit(
    总是重编=False,        # 强制重新编译
    可执行文件名=None,     # 编译为独立可执行文件
    优化级别='O2',         # C++ 优化级别
)
def function_name() -> ReturnType:
    ...
```

### 中文别名

```python
from l0n0lc import jit, 即时编译

# 两者等价
@jit()
def func1(): pass

@即时编译()
def func2(): pass
```

### 优化级别

- `O0` - 无优化，编译最快，运行最慢
- `O1` - 基础优化
- `O2` - 标准优化（默认）
- `O3` - 最大优化，编译较慢，运行最快
- `Os` - 优化代码大小
- `Ofast` - 激进优化（可能破坏标准合规）
- `Og` - 调试优化
- `Oz` - 最小代码大小

```python
@jit(优化级别='O3')
def performance_critical(x: int) -> int:
    return x ** 2
```

---

## 高级功能

### 自定义 C++ 映射

```python
import l0n0lc as lc
import math

# 映射到 C++ 标准库函数
@lc.映射函数(math.ceil, ['<cmath>'])
def cpp_ceil(v: float) -> float:
    return f'std::ceil({lc.转C字符串(v)});'

@lc.映射函数到('std::cout << u8"请输入>>>"; std::cin >> {v};', ['<iostream>'])
def cpp_cin(v):
    pass
```

### 可执行文件编译

```python
@jit(可执行文件名='my_program')
def main():
    # 编译为独立的可执行文件
    pass
```

### 类型映射

```python
@lc.映射类型('std::vector<int>', ['<vector>'])
class CppVectorInt:
    def push_back(self, v: int): pass
    def size(self) -> int: return 0
    def __getitem__(self, key: int) -> int: return 0

@lc.映射类型('short')
class ShortInt:
    def __init__(self, v: int) -> None: pass
```

---

## 工作原理

```
Python 函数
    ↓
AST 解析与类型推断
    ↓
C++ 代码生成
    ↓
系统 C++ 编译器
    ↓
动态库 (.so/.dll/.dylib)
    ↓
ctypes 加载执行
```

---

## 支持的语言特性

| 特性 | 支持情况 |
|------|----------|
| 基本类型 (int, float, bool, str) | ✅ |
| 容器类型 (List, Dict, Set) | ✅ |
| 类定义和实例方法 | ✅ |
| for/while 循环 | ✅ |
| if/else 条件 | ✅ |
| try/except 异常处理 | ✅ |
| 列表推导式 | ✅ |
| 固定大小数组 (Array) | ✅ |
| 可变参数 (*args, **kwargs) | ❌ |
| 生成器 | ❌ |
| 异步函数 | ❌ |

---

## 开发

### 从源码构建

```bash
git clone https://github.com/username/l0n0lc.git
cd l0n0lc
pip install -e .
```

### 运行测试

```bash
cd tests
for test in test_*.py; do
    echo "Running $test"
    python "$test"
done
```

### 构建发布包

```bash
# 使用 uv 构建
uv build

# 或使用构建脚本
./build.sh
```

---

## 缓存机制

编译产物存储在 `l0n0lcoutput/` 目录：

```
l0n0lcoutput/
├── {hash}_{filename}_{funcname}@_{hash}.cpp  # C++ 源码
├── {hash}_{filename}_{funcname}@_{hash}.h    # 头文件
└── {hash}_{filename}_{funcname}@_{hash}.so   # 动态库
```

缓存基于函数源码的 BLAKE2s 哈希，代码修改后自动重新编译。

### 清理缓存

```bash
# 清理所有缓存
rm -rf l0n0lcoutput/

# 清理构建产物
./build.sh  # 自动清理并重新构建
```

---

## 编译器选择

```bash
# 使用环境变量指定编译器
export CXX=clang++      # 使用 clang++
export CXX=g++          # 使用 g++

# 在运行时指定
CXX=clang++ python your_script.py

# 编译器优先级：
# 1. CXX 环境变量
# 2. 系统PATH中的 c++
# 3. 系统PATH中的 g++
# 4. 系统PATH中的 clang++
```

---

## 项目结构

```
l0n0lc/
├── 即时编译.py          # @jit 装饰器
├── Py转Cpp转译器.py     # AST 转 C++ 核心逻辑
├── cpp编译器.py         # C++ 编译器管理
├── 类型推断工具.py      # 类型推断
├── 类型转换.py          # Python ↔ C++ 类型转换
├── ast访问者.py         # AST 访问者基类
├── 表达式处理.py        # 表达式处理
├── 代码生成.py          # C++ 代码生成
├── 文件管理器.py        # 文件管理
├── 变量管理器.py        # 变量作用域管理
├── 编译上下文.py        # 编译上下文
├── 编译管理器.py        # 编译过程管理
├── std_vector.py        # std::vector 支持
├── std_map.py           # std::map 支持
├── std_set.py           # std::set 支持
├── std_array.py         # std::array 支持
├── 工具.py              # 核心工具函数
├── 日志工具.py          # 日志记录
├── 异常.py              # 自定义异常
└── 基础映射.py          # 预定义函数映射
```

---

## 许可证

[MIT License](LICENSE)

---

## 作者

倾城铸剑师
