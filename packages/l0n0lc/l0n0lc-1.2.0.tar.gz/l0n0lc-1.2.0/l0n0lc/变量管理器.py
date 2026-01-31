"""
变量管理器模块

负责管理变量作用域、变量查找和变量注册。
从 Py转Cpp转译器 中分离出来，实现单一职责原则。
"""

from typing import Optional, Any, Dict, List
from .cpp类型 import C变量


class 变量管理器:
    """
    变量管理器

    负责：
    - 管理变量作用域栈
    - 查找变量
    - 注册变量
    """

    def __init__(self):
        """初始化变量管理器"""
        # 变量作用域栈，每个元素是一个字典 {变量名: C变量}
        self.作用域变量: List[Dict[str, C变量]] = [{}]
        self.当前作用域层级 = 0
        self.最大变量ID = 0  # 变量ID生成器

    def 进入作用域(self):
        """
        进入新的作用域（如 if/for 块内部）

        创建一个新的空字典用于存储当前作用域的变量。
        """
        self.作用域变量.append({})
        self.当前作用域层级 += 1

    def 退出作用域(self):
        """
        退出当前作用域

        弹出当前作用域的变量字典，返回到上一层作用域。
        """
        if self.当前作用域层级 > 0:
            self.作用域变量.pop()
            self.当前作用域层级 -= 1

    def 获取C变量(self, name: str) -> Optional[C变量]:
        """
        从当前及上层作用域查找 C 变量

        Args:
            name: 变量名

        Returns:
            找到的 C 变量，如果未找到返回 None
        """
        # 从当前作用域向上查找
        for i in range(self.当前作用域层级, -1, -1):
            v = self.作用域变量[i].get(name)
            if v is not None:
                return v
        return None

    def 添加C变量(self, variable: C变量):
        """
        在当前作用域注册 C 变量

        Args:
            variable: 要注册的 C 变量
        """
        self.作用域变量[self.当前作用域层级][variable.名称] = variable

    def 变量是否存在(self, name: str) -> bool:
        """
        检查变量是否存在于任何作用域

        Args:
            name: 变量名

        Returns:
            变量是否存在
        """
        return self.获取C变量(name) is not None

    def 获取当前作用域变量数(self) -> int:
        """
        获取当前作用域的变量数量

        Returns:
            当前作用域的变量数量
        """
        return len(self.作用域变量[self.当前作用域层级])

    def 获取所有作用域变量数(self) -> int:
        """
        获取所有作用域的变量总数

        Returns:
            所有作用域的变量总数
        """
        total = 0
        for scope in self.作用域变量:
            total += len(scope)
        return total

    def 清空所有作用域(self):
        """清空所有作用域，重置为初始状态"""
        self.作用域变量 = [{}]
        self.当前作用域层级 = 0

    def 生成变量ID(self) -> int:
        """
        生成唯一的变量ID

        Returns:
            新的变量ID
        """
        self.最大变量ID += 1
        return self.最大变量ID

    def 获取状态摘要(self) -> Dict[str, Any]:
        """
        获取变量管理器的状态摘要

        Returns:
            包含当前状态的字典
        """
        return {
            "当前作用域层级": self.当前作用域层级,
            "作用域总数": len(self.作用域变量),
            "当前作用域变量数": self.获取当前作用域变量数(),
            "总变量数": self.获取所有作用域变量数(),
            "最大变量ID": self.最大变量ID,
        }
