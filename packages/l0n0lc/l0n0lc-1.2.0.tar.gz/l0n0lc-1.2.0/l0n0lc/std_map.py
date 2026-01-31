
from .cpp类型 import 字典初始化列表, C变量
from .工具 import 转C字符串
from .转译器工具 import 获取当前transpiler


class 标准无序映射(C变量):
    def __init__(
            self,
            初始化列表: 字典初始化列表,
            名称: str,
            是否参数: bool) -> None:
        self.初始化列表 = 初始化列表
        super().__init__(
            f'std::unordered_map<{初始化列表.键类型名}, {初始化列表.值类型名}>', 名称, 是否参数)

    def __getitem__(self, key):
        return f'{self}[{转C字符串(key)}]'

    def __setitem__(self, key, value):
        left = f'{self}[{转C字符串(key)}]'
        right = 转C字符串(value)
        return f'{left} = {right};'

    def _获取transpiler(self):
        """获取当前transpiler实例来添加必要的头文件"""
        return 获取当前transpiler()

    # Python dict 方法映射到 C++ std::unordered_map
    def get(self, key, default=None):
        """安全获取值，如果键不存在则返回默认值"""
        if default is None:
            return f"({self}.find({转C字符串(key)}) != {self}.end() ? {self}.at({转C字符串(key)}) : decltype({self}.at({转C字符串(key)})){{}})"
        else:
            return f"({self}.find({转C字符串(key)}) != {self}.end() ? {self}.at({转C字符串(key)}) : {转C字符串(default)})"

    def pop(self, key, default=None):
        """移除并返回指定键的值"""
        transpiler = self._获取transpiler()
        if transpiler:
            transpiler.编译管理器.包含头文件.add("<utility>")  # for std::move
            transpiler.编译管理器.包含头文件.add("<stdexcept>")  # for std::out_of_range

        if default is None:
            return f"""
            [&]{{
                auto it = {self}.find({转C字符串(key)});
                if (it != {self}.end()) {{
                    auto value = std::move(it->second);
                    {self}.erase(it);
                    return value;
                }}
                throw std::out_of_range("Key not found");
            }}()
            """.strip()
        else:
            return f"""
            [&]{{
                auto it = {self}.find({转C字符串(key)});
                if (it != {self}.end()) {{
                    auto value = std::move(it->second);
                    {self}.erase(it);
                    return value;
                }}
                return {转C字符串(default)};
            }}()
            """.strip()

    def popitem(self):
        """移除并返回一个键值对（C++中返回第一个元素）"""
        transpiler = self._获取transpiler()
        if transpiler:
            transpiler.编译管理器.包含头文件.add("<utility>")  # for std::pair
            transpiler.编译管理器.包含头文件.add("<stdexcept>")  # for std::out_of_range

        return f"""
        [&]{{
            if (!{self}.empty()) {{
                auto it = {self}.begin();
                auto item = std::make_pair(it->first, std::move(it->second));
                {self}.erase(it);
                return item;
            }}
            throw std::out_of_range("Dictionary is empty");
        }}()
        """.strip()

    def setdefault(self, key, default):
        """设置默认值，如果键不存在则设置并返回默认值"""
        return f"""
        [&]{{
            auto result = {self}.emplace({转C字符串(key)}, {转C字符串(default)});
            if (result.second) {{
                return result.first->second;
            }}
            return {self}.at({转C字符串(key)});
        }}()
        """.strip()

    def update(self, other_dict):
        """用另一个字典更新当前字典"""
        return f"""
        [&]{{
            for(const auto& pair : {other_dict}) {{
                {self}[pair.first] = pair.second;
            }}
            return {self}.size();
        }}()
        """.strip()

    def clear(self):
        """清空字典"""
        return f"{self}.clear();"

    def size(self):
        """返回字典大小（len() 函数会使用这个）"""
        return f"{self}.size()"

    def empty(self):
        """检查字典是否为空"""
        return f"{self}.empty()"

    def contains(self, key):
        """检查键是否存在（用于 'in' 操作符）"""
        return f"{self}.find({转C字符串(key)}) != {self}.end()"

    def keys(self):
        """返回所有键的视图（用于遍历）"""
        return self

    def values(self):
        """返回所有值的视图（用于遍历）"""
        return self

    def items(self):
        """返回所有键值对的视图（用于遍历）"""
        return self

    def begin(self):
        """返回指向开始位置的迭代器（用于内部操作）"""
        return f"{self}.begin()"

    def end(self):
        """返回指向结束位置的迭代器（用于内部操作）"""
        return f"{self}.end()"

    def find(self, key):
        """查找指定键的迭代器"""
        return f"{self}.find({转C字符串(key)})"

    def erase(self, iterator_or_key):
        """删除指定位置的元素（内部使用）"""
        return f"{self}.erase({iterator_or_key})"
