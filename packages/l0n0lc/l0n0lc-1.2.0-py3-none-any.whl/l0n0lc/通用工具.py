"""
通用工具模块 - 提供统一的错误处理、类型解析和异常处理功能
用于消除代码中的重复逻辑
"""

import ast
import inspect
import traceback
from typing import Union
from .异常 import Jit错误
from .工具 import 全局上下文, _ArrayInstance
from .类型转换 import 类型转换器
from .cpp类型 import C函数调用


def 统一抛出错误(transpiler, message: str, node: Union[ast.stmt, ast.expr, ast.arg, ast.arguments]):
    """
    统一的错误处理函数，消除22处重复的hasattr检查模式
    
    Args:
        transpiler: 转译器实例
        message: 错误消息
        node: AST节点，用于获取行号
    """
    if hasattr(transpiler, '抛出错误'):
        transpiler.抛出错误(message, node)
    else:
        line_no = getattr(node, "lineno", "?")
        raise Jit错误(f"Line {line_no}: {message}")



def 统一异常处理(e: Exception, transpiler, node: Union[ast.stmt, ast.expr, ast.arg, ast.arguments], context_msg: str = ""):
    """
    统一的异常处理逻辑，消除3处重复的异常+回溯处理模式
    
    Args:
        e: 异常对象
        transpiler: 转译器实例
        node: AST节点
        context_msg: 上下文消息
    """
    error_msg = f"{context_msg}: {str(e)}" if context_msg else str(e)
    
    # 添加原始回溯信息
    if traceback.format_exc():
        error_msg += f"\nOriginal traceback:\n{traceback.format_exc()}"
    
    统一抛出错误(transpiler, error_msg, node)


def 构建参数字符串(args: list, 获取值函数) -> str:
    """
    统一的参数字符串构建逻辑
    
    Args:
        args: 参数列表
        获取值函数: 用于获取参数值的函数
        
    Returns:
        str: 逗号分隔的参数字符串
    """
    arg_list = [str(获取值函数(arg)) for arg in args]
    return ",".join(arg_list)


def 处理函数参数(node_args, 获取值函数) -> list:
    """
    统一的函数参数处理逻辑
    
    Args:
        node_args: AST参数节点
        获取值函数: 用于获取参数值的函数
        
    Returns:
        list: 处理后的参数列表
    """
    return [获取值函数(arg) for arg in node_args]


def 生成函数调用(func_name: str, args_str: str):
    """
    统一的函数调用生成逻辑
    
    Args:
        func_name: 函数名
        args_str: 参数字符串
        
    Returns:
        C函数调用对象
    """    
    return C函数调用(func_name, args_str)


def 验证AST节点类型(node, expected_type, transpiler, error_msg: str):
    """
    统一的AST节点类型验证
    
    Args:
        node: AST节点
        expected_type: 期望的类型
        transpiler: 转译器实例
        error_msg: 错误消息
    """
    if not isinstance(node, expected_type):
        统一抛出错误(transpiler, error_msg, node)


def 获取节点行号(node) -> str:
    """
    统一的行号获取逻辑
    
    Args:
        node: AST节点
        
    Returns:
        str: 行号字符串
    """
    return str(getattr(node, "lineno", "?"))