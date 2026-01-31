from typing import Optional
from .工具 import 生成变量ID


class Cpp类型:
    """
    预定义的 C++ 类型字符串常量。
    """

    INT8_T = "int8_t"
    INT16_T = "int16_t"
    INT32_T = "int32_t"
    INT64_T = "int64_t"
    UINT8_T = "uint8_t"
    UINT16_T = "uint16_t"
    UINT32_T = "uint32_t"
    UINT64_T = "uint64_t"
    HALF = "half"
    FLOAT32 = "float"
    FLOAT64 = "double"
    字符串 = "char*"
    静态字符串 = "const char*"
    StdString = "std::string"
    布尔 = "bool"
    任意 = "std::any"
    自动 = "auto"
    空指针 = "void*"


class 代码块:
    """
    用于生成 C++ 代码块的上下文管理器（包含大括号）。
    """

    def __init__(self, 编译器) -> None:
        self.编译器 = 编译器

    def __enter__(self, *args, **kwargs):
        self.编译器.添加代码("{")
        self.编译器.进入作用域()

    def __exit__(self, *args, **kwargs):
        self.编译器.退出作用域()
        self.编译器.添加代码("}\n")


class C代码:
    """
    表示单行 C++ 代码，主要负责缩进处理。
    """

    def __init__(self, 代码: str, 层级: int, lineno: Optional[int] = None) -> None:
        self.代码 = 代码
        self.层级 = 层级
        self.lineno = lineno  # 对应的Python源码行号

    def __str__(self) -> str:
        return "  " * self.层级 + self.代码


class C获取下标:
    """
    表示 C++ 数组或 Vector 的下标访问表达式。
    """

    def __init__(self, 变量, 下标) -> None:
        self.变量 = 变量
        self.下标 = 下标

    def __str__(self) -> str:
        return f"{self.变量}[{self.下标}]"


class C获取属性:
    """
    表示 C++ 对象属性或成员函数访问表达式。
    自动处理指针 ->、引用 . 以及对象 . 的访问差异。
    """

    def __init__(self, 变量, 属性) -> None:
        self.变量 = 变量
        self.属性 = 属性

    def __str__(self) -> str:
        # 如果是C变量，根据类型决定访问方式
        if isinstance(self.变量, C变量):
            类型名 = self.变量.类型名

            # 指针类型使用 -> 访问
            if 类型名.endswith("*"):
                return f"{self.变量}->{self.属性}"
            # 引用类型使用 . 访问
            elif 类型名.endswith("&"):
                return f"{self.变量}.{self.属性}"
            # 对象类型使用 . 访问
            else:
                return f"{self.变量}.{self.属性}"

        # 如果是字符串表达式，需要解析类型
        elif isinstance(self.变量, str):
            # 简单的指针检测（以*结尾）
            if self.变量.endswith("*"):
                return f"{self.变量}->{self.属性}"
            # 简单的引用检测（以&结尾）
            elif self.变量.endswith("&"):
                return f"{self.变量}.{self.属性}"
            else:
                return f"{self.变量}.{self.属性}"

        # 如果是C函数调用（临时对象），需要用括号包围
        elif isinstance(self.变量, C函数调用):
            return f"({self.变量}).{self.属性}"

        # 默认使用 . 访问
        return f"{self.变量}.{self.属性}"


class C函数调用:
    """
    表示 C++ 函数调用表达式。
    """

    def __init__(self, 函数名, 参数字符串, 返回C类型=None) -> None:
        self.函数名 = 函数名
        self.参数字符串 = 参数字符串
        self.返回C类型 = 返回C类型

    def __str__(self) -> str:
        return f"{self.函数名}({self.参数字符串})"

    def __getattr__(self, name):
        """
        支持对函数调用返回对象的属性访问。
        当访问 C函数调用 对象的属性时，返回一个 C获取属性 表达式。
        """
        return C获取属性(self, name)


class C布尔:
    """
    表示 C++ 布尔值 (true/false)。
    """

    def __init__(self, v) -> None:
        self.v = v

    def __str__(self) -> str:
        return "true" if self.v else "false"


class C静态访问:
    """
    表示 C++ 静态方法调用表达式。
    """

    def __init__(self, class_name, method_name) -> None:
        self.class_name = class_name
        self.method_name = method_name

    def __str__(self) -> str:
        return f"{self.class_name}::{self.method_name}"


class CInt常量:
    def __init__(self, v: int) -> None:
        self.v = v

    def __str__(self) -> str:
        from .基础映射 import int映射目标
        return f'{int映射目标}({self.v})'


class CFloat常量:
    def __init__(self, v: float) -> None:
        self.v = v

    def __str__(self) -> str:
        from .基础映射 import float映射目标
        return f'{float映射目标}({self.v})'


class CString常量:
    def __init__(self, v: str) -> None:
        self.v = v

    def __str__(self) -> str:
        return f'u8"{self.v}"'


class CBytes常量:
    def __init__(self, v: bytes) -> None:
        self.v = v

    def __str__(self) -> str:
        return f'"{self.v}"'


class SuperCallWrapper:
    """包装super()调用，用于处理基类方法访问"""

    def __init__(self, base_class_name: str, transpiler):
        self.base_class_name = base_class_name
        self.transpiler = transpiler

    def __getattribute__(self, name):
        """拦截所有属性访问，包括特殊方法"""
        # Call object's __getattribute__ first to avoid infinite recursion
        obj = super().__getattribute__(name)

        # For special method names like __init__, return SuperMethodCall
        if name.startswith("__") and name.endswith("__") and name != "__getattribute__":
            transpiler = super().__getattribute__("transpiler")
            return SuperMethodCall(self.base_class_name, name, transpiler)

        # For other attributes, return normally
        return obj

    def __getattr__(self, method_name: str):
        """当访问super().method时返回基类方法调用"""
        transpiler = super().__getattribute__("transpiler")
        return SuperMethodCall(self.base_class_name, method_name, transpiler)

    def __call__(self, *args, **kwargs):
        """当直接调用super()时（构造函数）"""
        args_str = ", ".join(str(arg) for arg in args)
        return f"{self.base_class_name}({args_str})"


class SuperMethodCall:
    """表示super().method()调用"""

    def __init__(self, base_class_name: str, method_name: str, transpiler=None):
        self.base_class_name = base_class_name
        self.method_name = method_name
        self.transpiler = transpiler

    def __call__(self, *args):
        """生成基类方法调用的C++代码"""
        # Special handling: if this is super().__init__() in a constructor,
        # don't generate any code since the parent constructor is already called
        # in the initialization list
        if (
            self.method_name == "__init__"
            and self.transpiler
            and hasattr(self.transpiler, "当前方法名")
            and self.transpiler.当前方法名 == "__init__"
        ):
            return ""  # No code needed for super().__init__() in constructors

        args_str = ", ".join(str(arg) for arg in args)
        # C++中调用基类方法：BaseClass::method(args...)
        return f"{self.base_class_name}::{self.method_name}({args_str})"

    def __str__(self):
        """用于表达式上下文"""
        return f"{self.base_class_name}::{self.method_name}"




class 列表初始化列表:
    """
    表示 C++ 的初始化列表 {e1, e2, ...}，用于 std::vector 初始化。
    """

    def __init__(self, 代码: str, 类型名: str, 长度: int) -> None:
        self.代码 = 代码
        self.类型名 = 类型名
        self.长度 = 长度

    def __str__(self) -> str:
        return self.代码


class 字典初始化列表:
    """
    表示 C++ 的字典初始化列表 {{k1, v1}, {k2, v2}, ...}，用于 std::unordered_map。
    """

    def __init__(self, 代码: str, 键类型名: str, 值类型名: str) -> None:
        self.代码 = 代码
        self.键类型名 = 键类型名
        self.值类型名 = 值类型名

    def __str__(self) -> str:
        return self.代码


class 集合初始化列表:
    """
    表示 C++ 的集合初始化列表 {e1, e2, ...}，用于 std::unordered_set。
    """

    def __init__(self, 代码: str, 类型名: str) -> None:
        self.代码 = 代码
        self.类型名 = 类型名

    def __str__(self) -> str:
        return self.代码


class C变量:
    """
    表示一个 C++ 变量。
    包含变量类型、名称、生成的 C 变量名以及初始化代码生成逻辑。
    """

    def __init__(self, 类型名: str, 名称: str, 是否参数: bool, 默认值=None) -> None:
        self.类型名 = 类型名
        self.名称 = 名称
        self.C名称 = 生成变量ID(名称)
        self.是否参数 = 是否参数
        self.默认值 = 默认值

    def __str__(self):
        return self.C名称

    @property
    def decltype(self):
        return f"decltype({self})"

    def 初始化代码(self, initial_value, cast_type: str | None = None):
        """生成变量声明和初始化代码"""
        if cast_type:
            return f"{self.类型名} {self.C名称} = (({cast_type})({initial_value}));"
        else:
            return f"{self.类型名} {self.C名称} = {initial_value};"


class C模板变量(C变量):
    def __init__(self, 类型名: str, 名称: str,  默认值=None) -> None:
        super().__init__(类型名, 名称, True, 默认值)

    def 初始化代码(self):
        if self.默认值:
            return f"{self.类型名} {self.C名称} = {self.默认值}"
        return f"{self.类型名} {self.C名称}"
