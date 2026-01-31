"""
日志工具模块 - 提供可配置的日志系统
替代调试代码，提供更专业的日志记录功能
"""

import logging
import sys
from typing import Optional
from enum import Enum


class 日志级别(Enum):
    """日志级别枚举"""
    调试 = logging.DEBUG
    信息 = logging.INFO
    警告 = logging.WARNING
    错误 = logging.ERROR
    严重 = logging.CRITICAL


class 日志工具:
    """统一的日志管理类"""
    
    _实例 = None
    _已初始化 = False
    
    def __new__(cls):
        """单例模式"""
        if cls._实例 is None:
            cls._实例 = super().__new__(cls)
        return cls._实例
    
    def __init__(self):
        if not self._已初始化:
            self.日志器 = logging.getLogger("l0n0lc")
            self.日志器.setLevel(logging.INFO)  # 默认级别
            self.处理器 = None
            self.调试模式 = False
            self.已初始化 = True
    
    def 设置级别(self, 级别: 日志级别):
        """设置日志级别"""
        self.日志器.setLevel(级别.value)
    
    def 启用调试模式(self):
        """启用调试模式"""
        self.调试模式 = True
        self.设置级别(日志级别.调试)
    
    def 禁用调试模式(self):
        """禁用调试模式"""
        self.调试模式 = False
        self.设置级别(日志级别.信息)
    
    def 设置输出格式(self, 格式字符串: Optional[str] = None):
        """设置日志输出格式"""
        if 格式字符串 is None:
            if self.调试模式:
                格式字符串 = '[%(asctime)s] %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s'
            else:
                格式字符串 = '[%(levelname)s] %(message)s'
        
        formatter = logging.Formatter(格式字符串)
        
        if self.处理器:
            self.处理器.setFormatter(formatter)
        else:
            self.处理器 = logging.StreamHandler(sys.stdout)
            self.处理器.setFormatter(formatter)
            self.日志器.addHandler(self.处理器)
    
    def 调试(self, 消息: str, **kwargs):
        """记录调试信息"""
        if self.调试模式:
            self.日志器.debug(消息, **kwargs)
    
    def 信息(self, 消息: str, **kwargs):
        """记录一般信息"""
        self.日志器.info(消息, **kwargs)
    
    def 警告(self, 消息: str, **kwargs):
        """记录警告信息"""
        self.日志器.warning(消息, **kwargs)
    
    def 错误(self, 消息: str, **kwargs):
        """记录错误信息"""
        self.日志器.error(消息, **kwargs)
    
    def 严重(self, 消息: str, **kwargs):
        """记录严重错误信息"""
        self.日志器.critical(消息, **kwargs)
    
    def 异常(self, 消息: str, 异常对象: Optional[Exception] = None, **kwargs):
        """记录异常信息"""
        if 异常对象:
            self.错误(f"{消息}: {str(异常对象)}", **kwargs)
            if self.调试模式:
                self.调试(f"异常详细信息: {type(异常对象).__name__}", **kwargs)
        else:
            self.错误(消息, **kwargs)
    
    def 编译信息(self, 文件名: str, 操作: str, **kwargs):
        """记录编译相关信息"""
        self.信息(f"编译操作 - {操作}: {文件名}", **kwargs)
    
    def 类型推断信息(self, 变量名: str, python类型: str, cpp类型: str, **kwargs):
        """记录类型推断信息"""
        if self.调试模式:
            self.调试(f"类型推断 - {变量名}: {python类型} -> {cpp类型}", **kwargs)
    
    def 依赖关系信息(self, 主函数: str, 依赖函数: str, **kwargs):
        """记录依赖关系信息"""
        if self.调试模式:
            self.调试(f"依赖关系 - {主函数} 依赖 {依赖函数}", **kwargs)
    
    def 性能信息(self, 操作: str, 耗时: float, **kwargs):
        """记录性能信息"""
        if self.调试模式:
            self.信息(f"性能 - {操作}: {耗时:.3f}秒", **kwargs)
    
    def 清理信息(self, 文件路径: str, 原因: str = "编译失败", **kwargs):
        """记录文件清理信息"""
        if self.调试模式:
            self.调试(f"文件清理 - {原因}: {文件路径}", **kwargs)
    
    def 缓存信息(self, 操作: str, 文件名: str, **kwargs):
        """记录缓存操作信息"""
        if self.调试模式:
            self.调试(f"缓存操作 - {操作}: {文件名}", **kwargs)


# 全局日志实例
日志 = 日志工具()

# 便捷函数
def 启用调试模式():
    """全局启用调试模式"""
    日志.启用调试模式()
    日志.设置输出格式()

def 禁用调试模式():
    """全局禁用调试模式"""
    日志.禁用调试模式()
    日志.设置输出格式()

def 设置日志级别(级别: 日志级别):
    """全局设置日志级别"""
    日志.设置级别(级别)
    日志.设置输出格式()

# 初始化默认配置
日志.设置输出格式()
