"""
编译管理器模块

统一管理编译过程、文件操作、缓存管理和编译上下文。
整合了原编译管理器、文件管理器和编译上下文的功能。
"""

import os
import glob
import time
from typing import List, Optional, Set, Dict, Any, Callable
from .cpp编译器 import Cpp编译器
from .日志工具 import 日志


class 编译管理器:
    """
    统一的编译管理器

    负责：
    - 编译过程管理
    - 文件路径构建和文件操作
    - 缓存验证和清理
    - 编译上下文（头文件、链接库、变量ID等）
    """

    def __init__(
        self,
        工作目录: str,
        编译器: Cpp编译器
    ):
        """
        初始化编译管理器

        Args:
            工作目录: 编译输出目录
            编译器: C++ 编译器实例
        """
        # 文件管理相关
        self.工作目录 = 工作目录

        # 编译器
        self.编译器 = 编译器

        # 编译上下文相关
        self.编译栈: Set[str] = set()  # 防止循环编译的栈
        self.最大变量ID = 0  # 变量ID生成器
        self.包含头文件: Set[str] = set()  # 需要包含的头文件
        self.链接库: Set[str] = set()  # 需要链接的库
        self.库搜索目录: Set[str] = set()  # 库搜索目录

    # ========== 文件操作相关 ==========

    def 获取完整路径(self, 文件名: str) -> str:
        """
        获取文件的完整路径

        Args:
            文件名: 文件名（不含路径）

        Returns:
            完整路径: 工作目录/文件名
        """
        return f"{self.工作目录}/{文件名}"

    def 确保目录存在(self):
        """确保工作目录存在，不存在则创建"""
        if not os.path.exists(self.工作目录):
            try:
                os.makedirs(self.工作目录, exist_ok=True)
            except OSError as e:
                raise RuntimeError(f"无法创建工作目录 {self.工作目录}: {e}")

    def 清理临时文件(self, 基础名称: str):
        """
        清理编译产生的临时文件

        Args:
            基础名称: 文件的基础名称（不含扩展名）
        """
        temp_patterns = [
            f"{self.工作目录}/{基础名称}*.o",
            f"{self.工作目录}/{基础名称}*.tmp",
            f"{self.工作目录}/{基础名称}*.bak"
        ]

        self._删除文件按模式(temp_patterns)

    def 清理编译文件(self, 文件名列表: List[str]):
        """
        清理指定的编译文件

        Args:
            文件名列表: 需要清理的文件名列表
        """
        for 文件名 in 文件名列表:
            file_path = self.获取完整路径(文件名)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass  # 忽略删除失败

    def 清理所有缓存(self, 过期时间: Optional[float] = None) -> int:
        """
        清理所有缓存文件

        Args:
            过期时间: 可选，只清理超过此时间（秒）的文件
                     如果为 None，则清理所有缓存

        Returns:
            清理的文件数量
        """
        patterns = [
            os.path.join(self.工作目录, "*.so"),
            os.path.join(self.工作目录, "*.o"),
            os.path.join(self.工作目录, "*.tmp"),
            os.path.join(self.工作目录, "*.bak"),
            os.path.join(self.工作目录, "*.cpp"),
            os.path.join(self.工作目录, "*.h"),
            os.path.join(self.工作目录, "*.hash"),
            os.path.join(self.工作目录, "*.dylib"),  # macOS
            os.path.join(self.工作目录, "*.dll")     # Windows
        ]

        cleaned_count = 0
        当前时间 = time.time()

        for pattern in patterns:
            for file_path in glob.glob(pattern):
                try:
                    # 检查文件是否过期
                    if 过期时间 is not None:
                        file_mtime = os.path.getmtime(file_path)
                        if 当前时间 - file_mtime <= 过期时间:
                            continue

                    os.remove(file_path)
                    cleaned_count += 1
                except OSError:
                    pass

        return cleaned_count

    def 清理旧文件(self, 文件前缀: str):
        """
        清理具有指定前缀的所有旧文件

        Args:
            文件前缀: 文件名前缀
        """
        if not os.path.exists(self.工作目录):
            return

        for fname in os.listdir(self.工作目录):
            if fname.startswith(文件前缀):
                file_path = os.path.join(self.工作目录, fname)
                try:
                    os.remove(file_path)
                except OSError:
                    pass

    def 文件是否存在(self, 文件名: str) -> bool:
        """
        检查文件是否存在

        Args:
            文件名: 文件名

        Returns:
            文件是否存在
        """
        return os.path.exists(self.获取完整路径(文件名))

    def 文件是否可读(self, 文件名: str) -> bool:
        """
        检查文件是否可读

        Args:
            文件名: 文件名

        Returns:
            文件是否可读
        """
        file_path = self.获取完整路径(文件名)
        return os.path.exists(file_path) and os.access(file_path, os.R_OK)

    def 获取文件大小(self, 文件名: str) -> int:
        """
        获取文件大小

        Args:
            文件名: 文件名

        Returns:
            文件大小（字节）
        """
        file_path = self.获取完整路径(文件名)
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
        return 0

    def 获取文件修改时间(self, 文件名: str) -> float:
        """
        获取文件修改时间

        Args:
            文件名: 文件名

        Returns:
            文件修改时间（时间戳）
        """
        file_path = self.获取完整路径(文件名)
        if os.path.exists(file_path):
            return os.path.getmtime(file_path)
        return 0

    def 写入文件(self, 文件名: str, 内容: str):
        """
        写入内容到文件

        Args:
            文件名: 文件名
            内容: 文件内容
        """
        self.确保目录存在()
        file_path = self.获取完整路径(文件名)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(内容)

    def 读取文件(self, 文件名: str) -> Optional[str]:
        """
        读取文件内容

        Args:
            文件名: 文件名

        Returns:
            文件内容，如果文件不存在返回 None
        """
        file_path = self.获取完整路径(文件名)
        if not os.path.exists(file_path):
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def 列出文件(self, 模式: str = "*") -> List[str]:
        """
        列出工作目录中匹配模式的文件

        Args:
            模式: 文件匹配模式（如 "*.cpp"）

        Returns:
            文件列表
        """
        if not os.path.exists(self.工作目录):
            return []

        pattern = os.path.join(self.工作目录, 模式)
        return glob.glob(pattern)

    def _删除文件按模式(self, 模式列表: List[str]):
        """
        根据模式列表删除文件

        Args:
            模式列表: 文件模式列表
        """
        for pattern in 模式列表:
            for file_path in glob.glob(pattern):
                try:
                    os.remove(file_path)
                except OSError:
                    pass  # 忽略删除失败

    # ========== 编译上下文相关 ==========

    def 生成变量ID(self) -> int:
        """
        生成唯一的变量ID

        Returns:
            新的变量ID
        """
        self.最大变量ID += 1
        return self.最大变量ID

    def 添加包含头文件(self, 头文件: str):
        """
        添加需要包含的头文件

        Args:
            头文件: 头文件路径，如 <stdint.h> 或 "myheader.h"
        """
        self.包含头文件.add(头文件)

    def 添加链接库(self, 库名: str):
        """
        添加需要链接的库

        Args:
            库名: 库名称，如 "m" (数学库)
        """
        self.链接库.add(库名)

    def 添加库搜索目录(self, 目录: str):
        """
        添加库搜索目录

        Args:
            目录: 库搜索目录路径
        """
        self.库搜索目录.add(目录)

    def 入栈编译(self, 标识: str):
        """
        将函数标识压入编译栈

        Args:
            标识: 函数的唯一标识

        Raises:
            RuntimeError: 如果检测到循环编译
        """
        if 标识 in self.编译栈:
            raise RuntimeError(f"检测到循环编译: {标识}")
        self.编译栈.add(标识)

    def 出栈编译(self, 标识: str):
        """
        将函数标识从编译栈弹出

        Args:
            标识: 函数的唯一标识
        """
        self.编译栈.discard(标识)

    def 是否正在编译(self, 标识: str) -> bool:
        """
        检查函数是否正在编译

        Args:
            标识: 函数的唯一标识

        Returns:
            是否正在编译
        """
        return 标识 in self.编译栈

    def 重置上下文(self):
        """重置编译上下文（用于重复使用）"""
        self.编译栈.clear()
        self.最大变量ID = 0
        self.包含头文件.clear()
        self.链接库.clear()
        self.库搜索目录.clear()

    # ========== 编译管理相关 ==========

    def 检查缓存完整性(self, 获取文件名列表) -> List[str]:
        """
        检查缓存文件的完整性

        Args:
            获取文件名列表: 返回 (cpp文件名, 头文件名, 库文件名) 的函数

        Returns:
            问题列表，如果为空表示缓存完整
        """
        try:
            cpp_file名, 头文件名, 库文件名 = 获取文件名列表()

            issues = []

            # 检查源文件是否存在且可读
            if self.文件是否存在(cpp_file名):
                if not self.文件是否可读(cpp_file名):
                    issues.append(f"源文件不可读: {cpp_file名}")
            else:
                issues.append(f"源文件不存在: {cpp_file名}")

            # 检查头文件
            if self.文件是否存在(头文件名):
                if not self.文件是否可读(头文件名):
                    issues.append(f"头文件不可读: {头文件名}")

            # 检查库文件
            if self.文件是否存在(库文件名):
                if not self.文件是否可读(库文件名):
                    issues.append(f"库文件不可读: {库文件名}")

            return issues

        except Exception as e:
            return [f"缓存完整性检查失败: {str(e)}"]

    def 配置编译器(
        self,
        库目录列表: Optional[List[str]] = None,
        链接库列表: Optional[List[str]] = None
    ):
        """
        配置编译器

        Args:
            库目录列表: 库搜索目录列表
            链接库列表: 需要链接的库列表
        """
        if 库目录列表:
            self.编译器.添加库目录(库目录列表)

        if 链接库列表:
            self.编译器.添加库(链接库列表)

    def 执行编译(
        self,
        源文件列表: List[str],
        输出路径: str,
        是否为可执行文件: bool = False,
        编译选项: Optional[List[str]] = None
    ):
        """
        执行编译

        Args:
            源文件列表: 源文件路径列表
            输出路径: 输出文件路径
            是否为可执行文件: 是否编译为可执行文件
            编译选项: 额外的编译选项
        """
        if 编译选项:
            for option in 编译选项:
                self.编译器.添加编译选项(option)

        if 是否为可执行文件:
            self.编译器.编译文件(源文件列表, 输出路径)
        else:
            self.编译器.编译共享库(源文件列表, 输出路径)

    # ========== 状态查询 ==========

    def 获取状态摘要(self) -> Dict[str, Any]:
        """
        获取编译管理器的状态摘要

        Returns:
            包含当前状态的字典
        """
        状态信息 = {
            "工作目录": self.工作目录,
            "目录是否存在": os.path.exists(self.工作目录)
        }

        if 状态信息["目录是否存在"]:
            # 统计各类文件数量
            文件统计 = {
                "cpp文件": len(glob.glob(os.path.join(self.工作目录, "*.cpp"))),
                "头文件": len(glob.glob(os.path.join(self.工作目录, "*.h"))),
                "共享库": len(glob.glob(os.path.join(self.工作目录, "*.so"))) +
                         len(glob.glob(os.path.join(self.工作目录, "*.dylib"))) +
                         len(glob.glob(os.path.join(self.工作目录, "*.dll"))),
                "对象文件": len(glob.glob(os.path.join(self.工作目录, "*.o"))),
                "临时文件": len(glob.glob(os.path.join(self.工作目录, "*.tmp"))) +
                          len(glob.glob(os.path.join(self.工作目录, "*.bak")))
            }
            状态信息["文件统计"] = 文件统计

        # 添加编译上下文信息
        状态信息["编译上下文"] = {
            "编译栈大小": len(self.编译栈),
            "最大变量ID": self.最大变量ID,
            "包含头文件数量": len(self.包含头文件),
            "链接库数量": len(self.链接库),
            "库搜索目录数量": len(self.库搜索目录),
        }

        return 状态信息