"""
基础混入类模块 - 提供可重用的功能混入
用于统一错误处理、类型处理等通用功能
"""

import ast
import inspect
from typing import Union
from .工具 import _ArrayInstance, 全局上下文
from .类型转换 import 类型转换器
from .通用工具 import (
    统一异常处理,
    构建参数字符串, 处理函数参数, 生成函数调用,
    验证AST节点类型, 获取节点行号
)
from .异常 import 错误处理器


class 错误处理混入:
    """错误处理混入类 - 提供统一的错误处理功能"""

    def 抛出错误(self, message: str, node: Union[ast.stmt, ast.expr, ast.arg, ast.arguments]):
        """
        抛出带行号的编译错误

        Args:
            message: 错误消息
            node: AST节点，用于获取行号
        """
        # 获取源代码
        源代码 = getattr(self, '源代码', None)
        # 使用统一的错误处理器
        错误处理器.抛出错误(message, node, 源代码)
    
    def 处理异常(self, e: Exception, node: Union[ast.stmt, ast.expr, ast.arg, ast.arguments], context_msg: str = ""):
        """
        统一异常处理
        
        Args:
            e: 异常对象
            node: AST节点
            context_msg: 上下文消息
        """
        统一异常处理(e, self, node, context_msg)


class 类型处理混入:
    """类型处理混入类 - 提供统一的类型处理功能"""
    
    def 解析类型(self, py_type) -> str:
        """
        解析Python类型为C++类型
        
        Args:
            py_type: Python类型对象
            
        Returns:
            str: C++类型名称
        """
        # 特殊处理：Array 类型实例
        if isinstance(py_type, _ArrayInstance):
            return py_type.获取C类型名()

        if inspect.isclass(py_type):
            # 首先检查是否有类型映射
            mapped_type = 全局上下文.类型映射表.get(py_type)
            if mapped_type:
                # 添加需要包含的头文件
                if mapped_type.包含目录:
                    if hasattr(self, '包含头文件'):
                        self.包含头文件.update(mapped_type.包含目录) # type: ignore
                return mapped_type.目标类型
            else:
                # 用户自定义类
                return py_type.__name__

        return 类型转换器.Python类型转C类型(py_type)


class 参数处理混入:
    """参数处理混入类 - 提供统一的参数处理功能"""
    
    def 构建参数字符串(self, args: list) -> str:
        """
        构建参数字符串
        
        Args:
            args: 参数列表
            
        Returns:
            str: 逗号分隔的参数字符串
        """
        获取值函数 = getattr(self, '获取值', None)
        if 获取值函数 is None:
            获取值函数 = getattr(getattr(self, 'transpiler', None), '获取值', None)
        
        if 获取值函数 is None:
            raise AttributeError("无法找到'获取值'函数，请确保在类或transpiler中定义了此方法")
            
        return 构建参数字符串(args, 获取值函数)
    
    def 处理函数参数(self, node_args) -> list:
        """
        处理函数参数
        
        Args:
            node_args: AST参数节点
            
        Returns:
            list: 处理后的参数列表
        """
        获取值函数 = getattr(self, '获取值', None)
        if 获取值函数 is None:
            获取值函数 = getattr(getattr(self, 'transpiler', None), '获取值', None)
            
        if 获取值函数 is None:
            raise AttributeError("无法找到'获取值'函数，请确保在类或transpiler中定义了此方法")
            
        return 处理函数参数(node_args, 获取值函数)
    
    def 生成函数调用(self, func_name: str, args_str: str):
        """
        生成函数调用
        
        Args:
            func_name: 函数名
            args_str: 参数字符串
            
        Returns:
            C函数调用对象
        """
        return 生成函数调用(func_name, args_str)


class AST验证混入:
    """AST验证混入类 - 提供AST节点验证功能"""
    
    def 验证节点类型(self, node, expected_type, error_msg: str):
        """
        验证AST节点类型
        
        Args:
            node: AST节点
            expected_type: 期望的类型
            error_msg: 错误消息
        """
        验证AST节点类型(node, expected_type, self, error_msg)
    
    def 获取行号(self, node) -> str:
        """
        获取节点行号
        
        Args:
            node: AST节点
            
        Returns:
            str: 行号字符串
        """
        return 获取节点行号(node)


class 通用访问者混入(错误处理混入, 类型处理混入, 参数处理混入, AST验证混入):
    """
    通用访问者混入类 - 组合所有常用功能
    适用于大多数AST访问者类
    """
    pass