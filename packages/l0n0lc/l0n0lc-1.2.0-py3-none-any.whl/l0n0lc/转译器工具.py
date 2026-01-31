"""
转译器工具模块

提供转译器相关的通用工具函数。
消除各模块中的重复代码。
"""

import inspect
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .Py转Cpp转译器 import Py转Cpp转译器


def 获取当前transpiler() -> Optional["Py转Cpp转译器"]:
    """
    从调用栈中获取当前转译器实例

    通过检查调用栈中的局部变量来获取 transpiler 实例。
    用于在标准库容器类（如 std_vector、std_map）中访问转译器。

    Returns:
        找到的转译器实例，如果未找到返回 None
    """
    for frame_info in inspect.stack():
        frame = frame_info.frame
        if 'transpiler' in frame.f_locals:
            return frame.f_locals['transpiler']
        if 'self' in frame.f_locals and hasattr(frame.f_locals['self'], 'transpiler'):
            return frame.f_locals['self'].transpiler
    return None


def 获取当前转译器或抛出() -> "Py转Cpp转译器":
    """
    从调用栈中获取当前转译器实例

    类似于 `获取当前transpiler`，但如果未找到会抛出异常。

    Returns:
        找到的转译器实例

    Raises:
        RuntimeError: 如果未找到转译器实例
    """
    transpiler = 获取当前transpiler()
    if transpiler is None:
        raise RuntimeError("无法获取转译器实例：不在有效的转译上下文中")
    return transpiler
