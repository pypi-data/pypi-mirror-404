
from typing import Union, List, Optional
import subprocess
import os
import shutil


class Cpp编译器:
    """
    C++ 编译器包装类，负责检测编译器、设置参数并执行编译命令。
    """
    # 支持的优化级别
    _支持的优化级别 = {
        'O0': '-O0',   # 无优化，编译最快
        'O1': '-O1',   # 基础优化
        'O2': '-O2',   # 标准优化（默认）
        'O3': '-O3',   # 最大优化
        'Os': '-Os',   # 优化代码大小
        'Ofast': '-Ofast',  # 激进优化（可能破坏标准合规）
        'Og': '-Og',   # 调试优化
        'Oz': '-Oz',   # 最小代码大小（类似于 Os 但更激进）
    }

    def __init__(
        self,
        优化级别: str = 'O2'
    ) -> None:
        """
        初始化 C++ 编译器

        Args:
            优化级别: 优化级别，默认为 'O2'
                - O0: 无优化，编译最快，运行最慢
                - O1: 基础优化
                - O2: 标准优化（默认）
                - O3: 最大优化，编译较慢，运行最快
                - Os: 优化代码大小
                - Ofast: 激进优化（可能破坏标准合规）
                - Og: 调试优化
                - Oz: 最小代码大小
        """
        self.编译器 = self._检测编译器()
        self.包含目录: List[str] = []
        self.库目录: List[str] = []
        self.库: List[str] = []
        self.编译选项: List[str] = []
        self.详细模式 = False

        # 设置优化级别
        self.设置优化级别(优化级别)

    def _检测编译器(self) -> str:
        """
        自动检测可用的 C++ 编译器。
        优先检查 'CXX' 环境变量，然后检查常见的编译器命令。
        """
        # 1. 检查环境变量
        cxx = os.environ.get('CXX')
        if cxx:
            return cxx

        # 2. 检查系统路径中的标准编译器
        for compiler in ['c++', 'g++', 'clang++']:
            if shutil.which(compiler):
                return compiler

        # 3. 没有找到编译器，抛出明确错误
        raise RuntimeError(
            "未找到可用的C++编译器。请安装以下编译器之一：\n"
            "- Ubuntu/Debian: sudo apt install g++ clang++\n"
            "- CentOS/RHEL: sudo yum install gcc-c++ clang\n"
            "- macOS: xcode-select --install\n"
            "- Windows: 安装 Visual Studio 或 MinGW\n"
            "或者设置 CXX 环境变量指定编译器路径。"
        )

    def 设置编译器(self, compiler_path: str):
        """手动设置编译器路径"""
        self.编译器 = compiler_path

    def 设置优化级别(self, 优化级别: str):
        """
        设置编译优化级别

        Args:
            优化级别: 优化级别字符串（如 'O0', 'O1', 'O2', 'O3', 'Os', 'Ofast'）
                      不区分大小写，'os' 和 'Os' 等效

        Raises:
            ValueError: 如果优化级别不支持
        """
        # 不区分大小写，但保持原始形式
        优化级别_lower = 优化级别.lower()

        # 查找匹配的键（不区分大小写）
        匹配键 = None
        for key in self._支持的优化级别:
            if key.lower() == 优化级别_lower:
                匹配键 = key
                break

        if 匹配键 is None:
            支持的级别 = ', '.join(self._支持的优化级别.keys())
            raise ValueError(
                f"不支持的优化级别: {优化级别}\n"
                f"支持的优化级别: {支持的级别}"
            )

        self._当前优化级别 = 匹配键
        # 添加到编译选项（如果还没有）
        优化选项 = self._支持的优化级别[匹配键]
        if not any(opt.startswith('-O') or opt.startswith('--optimize') for opt in self.编译选项):
            self.编译选项.append(优化选项)

    def 获取优化级别(self) -> str:
        """获取当前优化级别"""
        return getattr(self, '_当前优化级别', 'O2')

    def 添加头文件目录(self, directory: Union[str, List[str]]):
        """添加头文件搜索目录 (-I)"""
        if isinstance(directory, str):
            self.包含目录.append(directory)
            return
        self.包含目录.extend(directory)

    def 添加库目录(self, directory: Union[str, List[str]]):
        """添加库文件搜索目录 (-L)"""
        if isinstance(directory, str):
            self.库目录.append(directory)
            return
        self.库目录.extend(directory)

    def 添加库(self, library_name: Union[str, List[str]]):
        """添加需要链接的库 (-l)"""
        if isinstance(library_name, str):
            self.库.append(library_name)
            return
        self.库.extend(library_name)

    def 添加编译选项(self, option: Union[str, List[str]]):
        """添加其他编译选项"""
        if isinstance(option, str):
            self.编译选项.append(option)
            return
        self.编译选项.extend(option)

    def 编译文件(self, file_path: Union[str, List[str]], output_path: str):
        """
        编译源文件到指定输出路径。
        构建并执行完整的编译器命令。
        """
        cmd = [self.编译器]

        # 添加头文件目录
        cmd.extend([f'-I{d}' for d in self.包含目录])

        # 添加库目录
        cmd.extend([f'-L{d}' for d in self.库目录])

        # 添加链接库
        cmd.extend([f'-l{lib}' for lib in self.库])

        # 添加编译选项
        cmd.extend(self.编译选项)

        # 添加源文件
        if isinstance(file_path, list):
            cmd.extend(file_path)
        else:
            cmd.append(file_path)

        # 添加输出路径
        cmd.extend(['-o', output_path])

        if self.详细模式:
            print(f"Compiling with command: {' '.join(cmd)}")

        try:
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Compilation failed with exit code {e.returncode}") from e
        except FileNotFoundError:
             raise RuntimeError(f"Compiler '{self.编译器}' not found. Please install a C++ compiler.")

    def 编译共享库(self, file_path: Union[str, List[str]], output_path: str):
        """
        编译为共享/动态库 (.so)。
        自动添加 -fPIC、--shared 和 RPATH 选项。
        使用初始化时设置的优化级别。
        """
        # 临时保存当前选项，避免重复添加
        原始选项 = self.编译选项.copy()

        # 确保必要选项存在（避免重复）
        if '-fPIC' not in self.编译选项:
            self.添加编译选项('-fPIC')
        if '--shared' not in self.编译选项:
            self.添加编译选项('--shared')

        # 注意：优化级别已在 __init__ 中通过 设置优化级别() 添加

        try:
            self.编译文件(file_path, output_path)
        finally:
            # 恢复原始选项
            self.编译选项 = 原始选项
