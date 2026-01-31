"""
容器构建器模块 - 统一处理容器初始化逻辑
消除从列表、字典、集合构建初始化列表的重复代码
"""

from typing import List, Dict, Set, Any, Union
from .类型转换 import 类型转换器
from .异常 import 类型不一致错误
from .cpp类型 import *

# 安全限制配置
MAX_CONTAINER_SIZE = 10**6  # 最大容器大小
MAX_STRING_LENGTH = 10**4   # 最大字符串长度
MAX_NESTING_DEPTH = 100     # 最大嵌套深度


class 容器构建器:
    """统一的容器构建器类"""
    
    @staticmethod
    def 构建初始化列表(container: Union[List[Any], Dict[Any, Any], Set[Any]], container_type: str):
        """
        统一的容器初始化列表构建逻辑
        
        Args:
            container: 容器对象（list、dict、set）
            container_type: 容器类型（"list"、"dict"、"set"）
            
        Returns:
            对应的初始化列表对象
        """
        # 验证输入参数
        if container is None:
            raise ValueError(f"{container_type} container cannot be None")
            
        # 检查容器大小限制
        container_size = len(container)
        if container_size > MAX_CONTAINER_SIZE:
            raise ValueError(
                f"{container_type} size {container_size} exceeds maximum limit {MAX_CONTAINER_SIZE}"
            )
        
        # 递归检查嵌套深度
        容器构建器._检查嵌套深度(container, current_depth=0)
        
        if container_type == "list":
            return 容器构建器._从列表构建初始化列表(list(container))
        elif container_type == "dict":
            return 容器构建器._从字典构建初始化列表(dict(container))
        elif container_type == "set":
            return 容器构建器._从集合构建初始化列表(set(container))
        else:
            raise ValueError(f"Unsupported container type: {container_type}")
    
    @staticmethod
    def _从列表构建初始化列表(value: List[Any]):
        """
        将 Python List 转换为 C++ 初始化列表字符串
        """
        if not value:
            return 列表初始化列表("{}", "auto", 0)

        # 检查是否是嵌套列表（元素是 列表初始化列表）
        # 用于支持多维数组，如 [[1, 2, 3], [4, 5, 6]]
        if all(isinstance(v, 列表初始化列表) for v in value):
            # 嵌套列表的情况
            init_items = [str(v) for v in value]
            type_names = [v.类型名 for v in value]

            # 检查类型一致性
            容器构建器._检查类型一致性(type_names, "Nested list elements")

            # 构建多维初始化列表: {{1,2,3}, {4,5,6}}
            init_list_str = "{" + ",".join(init_items) + "}"
            return 列表初始化列表(init_list_str, type_names[0], len(value))

        # 普通列表
        data_types = []
        init_items = []
        for v in value:
            dtype = type(v)
            data_types.append(dtype)
            init_items.append(str(v))

        # 构建初始化列表字符串
        init_list_str = "{" + ",".join(init_items) + "}"

        # 一致性检查
        容器构建器._检查类型一致性(data_types, "List elements")

        type_name = 容器构建器._推断元素类型(value, data_types[0])

        return 列表初始化列表(init_list_str, type_name, len(value))
    
    @staticmethod
    def _从字典构建初始化列表(value: Dict[Any, Any]):
        """
        将 Python Dict 转换为 C++ 初始化列表字符串
        """
        if not value:
            return 字典初始化列表("{}", "auto", "auto")

        code_items = []
        key_types = []
        value_types = []

        # 需要捕获第一个 key/value 实例来解析类型
        first_key = None
        first_value = None

        for i, (k, v) in enumerate(value.items()):
            if i == 0:
                first_key = k
                first_value = v
            key_type = type(k)
            value_type = type(v)
            key_types.append(key_type)
            value_types.append(value_type)
            code_items.append(f"{{ {k}, {v} }}")

        # 一致性检查
        容器构建器._检查类型一致性(key_types, "Dict keys")
        容器构建器._检查类型一致性(value_types, "Dict values")

        # 推断 key 和 value 的 C++ 类型
        key_type_name = 容器构建器._推断元素类型([first_key], type(first_key))
        value_type_name = 容器构建器._推断元素类型([first_value], type(first_value))

        init_list_str = "{" + ",".join(code_items) + "}"

        return 字典初始化列表(init_list_str, key_type_name, value_type_name)
    
    @staticmethod
    def _从集合构建初始化列表(value: Set[Any]):
        """
        将 Python Set 转换为 C++ 初始化列表字符串
        """
        if not value:
            return 集合初始化列表("{}", "auto")

        init_items = []
        data_types = []
        for v in value:
            data_types.append(type(v))
            init_items.append(str(v))

        # 一致性检查
        容器构建器._检查类型一致性(data_types, "Set elements")

        type_name = 容器构建器._推断元素类型(value, data_types[0])

        init_list_str = "{" + ",".join(init_items) + "}"

        return 集合初始化列表(init_list_str, type_name)
    
    @staticmethod
    def _检查类型一致性(data_types: List[type], error_context: str):
        """
        检查类型一致性
        
        Args:
            data_types: 类型列表
            error_context: 错误上下文信息
        """
        if not data_types:
            return
            
        first_type = data_types[0]
        if not all(t == first_type for t in data_types):
            raise 类型不一致错误(
                f"{error_context} must have same type, got {set(data_types)}"
            )
    
    @staticmethod
    def _检查嵌套深度(container: Any, current_depth: int = 0) -> None:
        """
        递归检查容器嵌套深度，防止过深嵌套导致栈溢出
        
        Args:
            container: 要检查的容器对象
            current_depth: 当前嵌套深度
            
        Raises:
            ValueError: 当嵌套深度超过限制时
        """
        if current_depth > MAX_NESTING_DEPTH:
            raise ValueError(f"容器嵌套深度 {current_depth} 超过限制 {MAX_NESTING_DEPTH}")
        
        # 如果是字符串，检查长度限制
        if isinstance(container, str):
            if len(container) > MAX_STRING_LENGTH:
                raise ValueError(f"字符串长度 {len(container)} 超过限制 {MAX_STRING_LENGTH}")
            return
        
        # 如果是容器类型，递归检查嵌套
        if isinstance(container, (list, tuple, set)):
            for item in container:
                容器构建器._检查嵌套深度(item, current_depth + 1)
        elif isinstance(container, dict):
            for key, value in container.items():
                容器构建器._检查嵌套深度(key, current_depth + 1)
                容器构建器._检查嵌套深度(value, current_depth + 1)
    
    @staticmethod
    def _推断元素类型(container: Union[List[Any], Set[Any]], first_type: type) -> str:
        """
        推断元素的C++类型
        
        Args:
            container: 容器对象
            first_type: 第一个元素的类型
            
        Returns:
            str: C++类型名称
        """
        if not container:
            return "auto"
            
        # 根据第一个元素值推断 C++ 类型
        first_val = next(iter(container)) if isinstance(container, set) else container[0]
        return 类型转换器.Python类型转C类型(first_type, first_val)
