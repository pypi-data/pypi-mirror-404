from .cpp类型 import 集合初始化列表, C变量
from .转译器工具 import 获取当前transpiler


class 标准集合(C变量):
    def __init__(self, 初始化列表: 集合初始化列表, 名称: str, 是否参数: bool) -> None:
        self.初始化列表 = 初始化列表
        super().__init__(f"std::unordered_set<{初始化列表.类型名}>", 名称, 是否参数)

    def add(self, value):
        return f"{self}.insert({str(value)});"

    def remove(self, value):
        return f"{self}.erase({str(value)});"

    def update(self, other_set):
        """将另一个集合的所有元素添加到当前集合（就地修改）"""
        return f"""
        [&]{{
            for(const auto& elem : {other_set}) {{
                {self}.insert(elem);
            }}
            return {self};
        }}()
        """.strip()

    def __contains__(self, item):
        # This will be used in 'item in set'
        # But transpiler handles 'in' via Compare?
        # If transpiler calls this, fine.
        return f"{self}.find({str(item)}) != {self}.end()"

    def _获取transpiler(self):
        """获取当前transpiler实例来添加必要的头文件"""
        return 获取当前transpiler()

    # Python set 方法映射到 C++ std::unordered_set
    def clear(self):
        """清空集合"""
        return f"{self}.clear();"

    def size(self):
        """返回集合大小（len() 函数会使用这个）"""
        return f"{self}.size()"

    def empty(self):
        """检查集合是否为空"""
        return f"{self}.empty()"

    def begin(self):
        """返回指向开始位置的迭代器（用于内部操作）"""
        return f"{self}.begin()"

    def end(self):
        """返回指向结束位置的迭代器（用于内部操作）"""
        return f"{self}.end()"

    def find(self, value):
        """查找指定值的迭代器"""
        return f"{self}.find({str(value)})"

    def erase(self, value_or_iterator):
        """删除指定值或迭代器位置的元素"""
        return f"{self}.erase({value_or_iterator})"

    def union(self, other_set):
        """返回两个集合的并集"""
        transpiler = self._获取transpiler()
        if transpiler:
            transpiler.编译管理器.包含头文件.add("<unordered_set>")

        return f"""
        [&]{{
            auto result = {self};
            for(const auto& elem : {other_set}) {{
                result.insert(elem);
            }}
            return result;
        }}()
        """.strip()

    def intersection(self, other_set):
        """返回两个集合的交集"""
        transpiler = self._获取transpiler()
        if transpiler:
            transpiler.编译管理器.包含头文件.add("<unordered_set>")

        return f"""
        [&]{{
            decltype({self}) result;
            for(const auto& elem : {self}) {{
                if ({other_set}.find(elem) != {other_set}.end()) {{
                    result.insert(elem);
                }}
            }}
            return result;
        }}()
        """.strip()

    def difference(self, other_set):
        """返回两个集合的差集"""
        transpiler = self._获取transpiler()
        if transpiler:
            transpiler.编译管理器.包含头文件.add("<unordered_set>")

        return f"""
        [&]{{
            decltype({self}) result;
            for(const auto& elem : {self}) {{
                if ({other_set}.find(elem) == {other_set}.end()) {{
                    result.insert(elem);
                }}
            }}
            return result;
        }}()
        """.strip()

    def issubset(self, other_set):
        """检查当前集合是否为另一个集合的子集"""
        return f"""
        [&]{{
            for(const auto& elem : {self}) {{
                if ({other_set}.find(elem) == {other_set}.end()) {{
                    return false;
                }}
            }}
            return true;
        }}()
        """.strip()

    def issuperset(self, other_set):
        """检查当前集合是否为另一个集合的超集"""
        return f"""
        [&]{{
            for(const auto& elem : {other_set}) {{
                if ({self}.find(elem) == {self}.end()) {{
                    return false;
                }}
            }}
            return true;
        }}()
        """.strip()

    def isdisjoint(self, other_set):
        """检查两个集合是否不相交"""
        return f"""
        [&]{{
            for(const auto& elem : {self}) {{
                if ({other_set}.find(elem) != {other_set}.end()) {{
                    return false;
                }}
            }}
            return true;
        }}()
        """.strip()

    def discard(self, value):
        """移除元素，如果元素不存在也不报错"""
        return f"{self}.erase({str(value)});"

    def pop(self):
        """移除并返回一个任意元素"""
        transpiler = self._获取transpiler()
        if transpiler:
            transpiler.编译管理器.包含头文件.add("<stdexcept>")  # for std::out_of_range

        return f"""
        [&]{{
            if (!{self}.empty()) {{
                auto it = {self}.begin();
                auto value = *it;
                {self}.erase(it);
                return value;
            }}
            throw std::out_of_range("Set is empty");
        }}()
        """.strip()

    def copy(self):
        """返回集合的浅拷贝"""
        return f"{self}"

    def __bool__(self):
        """支持布尔上下文（用于 if not s 等）"""
        return f"!{self}.empty()"
