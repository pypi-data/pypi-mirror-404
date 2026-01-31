"""标准数组模块 - 支持 C++ 原生数组类型"""

from .cpp类型 import C变量, 列表初始化列表
from .转译器工具 import 获取当前transpiler
from typing import List


class 标准数组(C变量):
    """
    表示 C++ 原生数组类型
    例如: int a[3] = {1, 2, 3};
    """

    def __init__(self, 元素类型: str, 大小列表: List[int], 初始化列表: 列表初始化列表, 名称: str, 是否参数: bool) -> None:
        """
        Args:
            元素类型: C++ 元素类型，如 "int64_t"
            大小列表: 数组维度列表，如 [3] 表示一维数组，[2][3] 表示二维数组
            初始化列表: 初始化列表对象
            名称: 变量名
            是否参数: 是否为函数参数
        """
        self.元素类型 = 元素类型
        self.大小列表 = 大小列表
        self.初始化列表 = 初始化列表

        # 类型名只存储元素类型，不包含数组大小
        # 例如 "int64_t"，数组大小在初始化代码中添加到变量名后
        super().__init__(元素类型, 名称, 是否参数)

    def __getitem__(self, key):
        """支持下标访问 a[i]"""
        return f"{self.C名称}[{key}]"

    def __setitem__(self, key, value):
        """支持下标赋值 a[i] = value"""
        return f"{self.C名称}[{key}] = {value};"

    def 初始化代码(self, initial_value, cast_type: str | None = None):
        """生成数组变量声明和初始化代码"""
        # 构建数组声明: int64_t a[3] = {1, 2, 3};
        # 或多维: int64_t a[2][3] = {{1, 2, 3}, {4, 5, 6}};
        数组声明 = f"{self.C名称}"
        for size in self.大小列表:
            数组声明 = f"{数组声明}[{size}]"

        return f"{self.类型名} {数组声明} {initial_value};"

    def size(self):
        """返回数组总大小"""
        total_size = 1
        for size in self.大小列表:
            total_size *= size
        return total_size

    def _获取transpiler(self):
        """获取当前transpiler实例来添加必要的头文件"""
        return 获取当前transpiler()
