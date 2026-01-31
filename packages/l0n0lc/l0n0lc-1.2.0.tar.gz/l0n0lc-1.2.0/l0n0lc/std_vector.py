from .cpp类型 import C变量, Cpp类型, 列表初始化列表
from .转译器工具 import 获取当前transpiler


class 标准列表(C变量):
    def __init__(self, 初始化列表: 列表初始化列表, 名称: str, 是否参数: bool) -> None:
        self.初始化列表 = 初始化列表
        if 初始化列表.类型名 == Cpp类型.任意:
            super().__init__(f"std::vector<{初始化列表.类型名}>", 名称, 是否参数)
        else:
            super().__init__(f"std::vector<{初始化列表.类型名}>", 名称, 是否参数)

    def __getitem__(self, key):
        return f"{self}[{key}]"

    def __setitem__(self, key, value):
        return f"{self}[{key}] = {value};"

    def 初始化代码(self, initial_value, cast_type: str | None = None):
        """生成列表变量声明和初始化代码"""
        # 对于列表，直接使用初始化列表语法，不需要类型转换
        return f"{self.类型名} {self.C名称} {initial_value};"

    def _获取transpiler(self):
        """获取当前transpiler实例来添加必要的头文件"""
        return 获取当前transpiler()

    # Python list 方法映射到 C++ std::vector
    def append(self, value):
        """在列表末尾添加元素"""
        return f"{self}.push_back({value});"

    def extend(self, other_list):
        """扩展列表，添加另一个列表的所有元素"""
        return f"""
        [&]{{
            for(const auto& elem : {other_list}) {{
                {self}.push_back(elem);
            }}
            return {self}.size();
        }}()
        """.strip()

    def insert(self, index, value):
        """在指定位置插入元素"""
        return f"{self}.insert({self}.begin() + {index}, {value});"

    def pop(self, index=-1):
        """移除并返回指定位置的元素"""
        if index == -1:
            # 默认移除最后一个元素
            return f"[&]{{ auto last_elem = {self}.back(); {self}.pop_back(); return last_elem; }}()"
        else:
            # 移除指定位置的元素
            return f"[&]{{ auto elem = {self}[{index}]; {self}.erase({self}.begin() + {index}); return elem; }}()"

    def remove(self, value):
        """移除第一个匹配的元素"""
        # 添加algorithm头文件以支持std::find
        transpiler = self._获取transpiler()
        if transpiler:
            transpiler.编译管理器.包含头文件.add("<algorithm>")

        return f"[&]{{ auto it = std::find({self}.begin(), {self}.end(), {value}); if (it != {self}.end()) {{ {self}.erase(it); }} }}()"

    def clear(self):
        """清空列表"""
        return f"{self}.clear();"

    def size(self):
        """返回列表大小（len() 函数会使用这个）"""
        return f"{self}.size()"

    def empty(self):
        """检查列表是否为空"""
        return f"{self}.empty()"

    def front(self):
        """返回第一个元素"""
        return f"{self}.front()"

    def back(self):
        """返回最后一个元素"""
        return f"{self}.back()"

    def begin(self):
        """返回指向开始位置的迭代器（用于内部操作）"""
        return f"{self}.begin()"

    def end(self):
        """返回指向结束位置的迭代器（用于内部操作）"""
        return f"{self}.end()"

    def erase(self, iterator):
        """删除指定位置的元素（内部使用）"""
        return f"{self}.erase({iterator})"
