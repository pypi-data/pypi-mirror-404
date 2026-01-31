import ctypes
from typing import Any, Dict, Set, Tuple, Union, List, get_origin, get_args
from .工具 import 全局上下文
from .基础映射 import *

class 类型转换器:
    """处理Python类型到C++类型和ctypes类型的转换"""

    @staticmethod
    def Python类型转C类型(py_type: Any, 类型实例=None) -> Any:
        """
        将Python类型转换为C++类型字符串

        Args:
            py_type: Python类型对象或类型字符串
            类型实例: 类型实例（可选），用于推断返回类型明确的函数调用等

        Returns:
            C++类型字符串
        """
        # 2. 检查全局类型映射表
        ret = 全局上下文.类型映射表.get(py_type)
        if ret is not None:
            return ret.目标类型

        # 4. 处理泛型类型
        origin = get_origin(py_type)
        args = get_args(py_type)

        # 4.1 Union types
        if origin is Union:
            from .cpp类型 import Cpp类型
            return Cpp类型.任意

        # 4.2 List[...] -> std::vector<...>
        if origin is list:
            if args:
                elem_type = 类型转换器.Python类型转C类型(args[0])
                return f"std::vector<{elem_type}>"

        # 4.3 Dict[K, V] -> std::unordered_map<K, V>
        if origin is dict:
            if len(args) == 2:
                key_type = 类型转换器.Python类型转C类型(args[0])
                val_type = 类型转换器.Python类型转C类型(args[1])
                return f"std::unordered_map<{key_type}, {val_type}>"

        # 4.4 Set[T] -> std::unordered_set<T>
        if origin is set:
            if args:
                elem_type = 类型转换器.Python类型转C类型(args[0])
                return f"std::unordered_set<{elem_type}>"

        # 4.5 Tuple[T1, T2...] -> std::tuple<T1, T2...> or std::pair<T1, T2>
        if origin is tuple:
            if args:
                # Check for Tuple[int, ...] (variable length, homogenous)
                if len(args) == 2 and args[1] is Ellipsis:
                    elem_type = 类型转换器.Python类型转C类型(args[0])
                    # Map to vector for variable length tuple
                    return f"std::vector<{elem_type}>"

                arg_types = [类型转换器.Python类型转C类型(arg) for arg in args]
                if len(arg_types) == 2:
                    return f"std::pair<{arg_types[0]}, {arg_types[1]}>"
                return f'std::tuple<{", ".join(arg_types)}>'

        # 5. None类型处理 - 映射到void或特殊标记
        if py_type is type(None):
            return "void"  # 或者使用特殊标记如 "NoneType"

        # 6. 直接传入的字符串类型名称 (例如 'int')
        if isinstance(py_type, str):
            return py_type

        # 7. 特殊处理：如果类型实例是函数调用且已知返回类型
        if (
            类型实例
            and hasattr(类型实例, "返回C类型")
            and 类型实例.返回C类型 is not None
        ):
            return 类型实例.返回C类型

        raise TypeError(f"Unsupported type: {py_type}")

    @staticmethod
    def Python类型转ctypes(py_type: Any) -> Any:
        """
        将Python类型转换为ctypes类型

        Args:
            py_type: Python类型对象

        Returns:
            ctypes类型对象
        """
        # 2. 检查全局类型映射表
        ret = 全局上下文.类型映射表.get(py_type)
        if ret is not None and ret.ctypes类型 is not None:
            return ret.ctypes类型

        # 4. 处理特殊类型
        if py_type in (None, "None", type(None)):
            return None

        # 5. 处理泛型类型
        origin = get_origin(py_type)
        args = get_args(py_type)

        # 5.1 处理类型字符串
        if isinstance(py_type, str):
            if py_type == "void":
                return None
            # 其他字符串类型可能是自定义类名，无法确定具体的ctypes类型
            return ctypes.c_void_p
        # 5.3 默认返回void指针
        return ctypes.c_void_p

    @staticmethod
    def C类型转Python(c_type: str) -> Any:
        """
        将C++类型字符串转换为Python类型对象

        Args:
            c_type: C++类型字符串

        Returns:
            Python类型对象
        """
        # 直接匹配
        ret = 全局上下文.反向类型映射表.get(c_type)
        if ret is not None:
            return ret

        # 处理容器类型
        if c_type.startswith("std::vector<"):
            # 提取元素类型
            elem_type_str = c_type[11:-1]  # 去掉 "std::vector<" 和 ">"
            elem_type = 类型转换器.C类型转Python(elem_type_str)
            if elem_type:
                return List[elem_type]
            else:
                return List[int]  # 默认元素类型
        elif c_type.startswith("std::unordered_map<"):
            # 提取键值类型
            content = c_type[18:-1]  # 去掉 "std::unordered_map<" 和 ">"
            if ", " in content:
                key_type_str, val_type_str = content.split(", ", 1)
                key_type = 类型转换器.C类型转Python(key_type_str)
                val_type = 类型转换器.C类型转Python(val_type_str)
                if key_type and val_type:
                    return Dict[key_type, val_type]
            return Dict[int, int]

        elif c_type.startswith("std::unordered_set<"):
            # 提取元素类型
            elem_type_str = c_type[18:-1]  # 去掉 "std::unordered_set<" 和 ">"
            elem_type = 类型转换器.C类型转Python(elem_type_str)
            if elem_type:
                return Set[elem_type]
            else:
                return Set[int]  # 默认元素类型

        elif c_type.startswith("std::pair<"):
            # 提取两个元素类型
            content = c_type[10:-1]  # 去掉 "std::pair<" 和 ">"
            if ", " in content:
                first_type_str, second_type_str = content.split(", ", 1)
                first_type = 类型转换器.C类型转Python(first_type_str)
                second_type = 类型转换器.C类型转Python(second_type_str)
                if first_type and second_type:
                    return Tuple[first_type, second_type]
            # 默认类型
            return Tuple[int, int]

        elif c_type.startswith("std::tuple<"):
            # 提取所有元素类型
            content = c_type[10:-1]  # 去掉 "std::tuple<" 和 ">"
            if content:
                elem_type_strs = [s.strip() for s in content.split(",")]
                elem_types = []
                for elem_type_str in elem_type_strs:
                    elem_type = 类型转换器.C类型转Python(elem_type_str)
                    elem_types.append(elem_type if elem_type else int)
                return Tuple[tuple(elem_types)]
            else:
                return Tuple[()]  # 空元组

        # 处理指针类型
        if c_type.endswith("*"):
            base_type = 类型转换器.C类型转Python(c_type[:-1].strip())
            # 指针类型在Python中通常用原类型表示
            return base_type

        # 处理引用类型
        if c_type.endswith("&"):
            base_type = 类型转换器.C类型转Python(c_type[:-1].strip())
            # 引用类型在Python中用原类型表示
            return base_type

        # 处理const修饰符
        if c_type.startswith("const "):
            base_type = 类型转换器.C类型转Python(c_type[6:].strip())
            return base_type
        return None
