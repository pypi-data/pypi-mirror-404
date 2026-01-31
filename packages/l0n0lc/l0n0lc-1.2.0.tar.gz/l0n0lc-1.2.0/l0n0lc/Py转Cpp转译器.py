import os
import ast
import hashlib
import inspect
import ctypes
import io
from typing import Callable, Any, List, Dict, Set, Optional, Tuple, Union
from .cpp类型 import C变量, 代码块
from .异常 import Jit错误, 编译错误
from .工具 import 全局上下文, 含非ASCII字符
from .cpp编译器 import Cpp编译器
from .ast访问者 import 语句访问者
from .表达式处理 import 表达式访问者
from .类型转换 import 类型转换器
from .代码生成 import 代码生成器
from .类支持 import 类支持处理器
from .基础混入 import 通用访问者混入
from .变量管理器 import 变量管理器
from .编译管理器 import 编译管理器
from .类方法信息 import 类方法信息


class Py转Cpp转译器(通用访问者混入, ast.NodeVisitor):
    """
    AST 访问者类，负责将 Python 函数 AST 转换为 C++ 代码并进行编译。
    核心功能包括类型推断、代码生成、依赖管理和 C++ 编译器调用。
    """

    def __init__(
        self, 目标函数: Callable, 编译器: Cpp编译器, 可执行文件名: Optional[str] = None,
        总是重编: bool = False
    ) -> None:
        """
        初始化转译器。

        :param 目标函数: 需要编译的 Python 函数对象
        :param 编译器: CppCompiler 实例，用于处理后续的 C++ 编译工作
        :param 可执行文件名: 如果提供，将编译为可执行文件而非动态库
        :param 总是重编: 是否每次运行都强制重新编译
        :param 最大进程数: 并行编译的最大进程数（None 表示使用 CPU 核心数）
        """
        self.目标函数 = 目标函数
        # 使用传入的编译器实例（已配置优化级别）
        self.编译器 = 编译器
        self.可执行文件名 = 可执行文件名
        self.总是重编 = 总是重编
        self.已编译 = False  # 延迟编译标记
        self.源代码 = inspect.getsource(目标函数)
        # 计算源码哈希值，用于缓存文件名生成
        self.代码哈希 = hashlib.blake2s(
            self.源代码.encode(), digest_size=8).hexdigest()

        if inspect.isclass(目标函数):
            import sys

            module = sys.modules.get(目标函数.__module__)
            self.全局变量 = module.__dict__ if module else {}
            self.是类 = True
            self.类成员变量: Dict[str, str] = {}  # Python Name -> C Type
            self.类成员默认值: Dict[str, Any] = {}  # 成员变量默认值
            self.类静态成员: Dict[str, Tuple[str, Any]] = (
                {}
            )  # 静态成员: name -> (type, value)
            self.类基类列表: List[Any] = []  # 基类列表
            self.构造函数 = None
        else:
            self.全局变量 = 目标函数.__globals__
            self.是类 = False

        self.本地变量 = {}
        self.参数变量 = {}
        self.参数名称 = []  # 保存参数名称列表，用于类型推断
        self.当前方法参数: Dict[str, C变量] = {}  # 当前方法的参数（用于类方法）
        self.ctypes参数类型 = []  # 保存参数的 ctypes 类型，用于 ctypes 调用
        self.ctypes返回类型 = ctypes.c_voidp  # 保存返回值的 ctypes 类型
        self.类方法列表: List[类方法信息] = []  # 存储类方法信息
        self.依赖函数: Set["Py转Cpp转译器"] = set()  # 递归依赖的其他 JIT 函数
        self.代码缓冲区 = io.StringIO()  # 使用 StringIO 代替列表，提升字符串拼接性能
        self.代码块上下文 = 代码块(self)  # 代码块上下文管理器
        self.正在直接调用 = False  # 标记是否正在进行直接 Python 调用
        self.正在构建参数 = False  # 标记是否正在处理函数参数

        # 库缓存（每个转译器实例自己持有）
        self.目标库 = None  # ctypes.CDLL 对象
        self.cpp函数 = None  # 编译后的 C++ 函数

        # 初始化变量管理器
        self.变量管理器 = 变量管理器()

        # 初始化统一的编译管理器（整合了文件管理器和编译上下文）
        self.编译管理器 = 编译管理器(全局上下文.工作目录, 编译器)
        # 添加默认头文件
        self.编译管理器.添加包含头文件("<stdint.h>")

        self.函数名 = 目标函数.__name__

        if 可执行文件名:
            self.C函数名 = "main"  # 如果是可执行文件，入口函数为 main
        else:
            if 含非ASCII字符(self.函数名):
                # 防止中文函数名导致的编码问题，使用 hex 编码
                self.C函数名 = f"function_{self.函数名.encode().hex()}"
            else:
                self.C函数名 = self.函数名

        file_path = inspect.getfile(目标函数)
        file_name = os.path.split(file_path)[1]
        file_name_hash = hashlib.blake2s(
            file_path.encode(), digest_size=8).hexdigest()
        # 文件前缀，包含原文件名哈希、文件名、函数名，用于区分
        self.文件前缀 = f"{file_name_hash}_{file_name}_{self.函数名}_@"

        self.返回类型 = "void"  # 默认 C++ 返回类型
        self.目标库 = None  # ctypes 加载的动态库对象
        self.cpp函数 = None  # 加载后的 C++ 函数对象, 如果是类，这里可能不需要或者指向构造函数包装器

        # 初始化各个处理器
        self.表达式访问者 = 表达式访问者(self)
        self.语句访问者 = 语句访问者(self)
        # 类型转换器的所有方法都是静态方法，不需要实例化
        self.代码生成器 = 代码生成器(self)
        self.类支持处理器 = 类支持处理器(self) if self.是类 else None

        self.分析完成 = False
        self.仅分析函数声明 = False

    def __str__(self):
        return self.C函数名

    def 添加依赖(self, target):
        if target is self or target is self.目标函数 or target.目标函数 is self.目标函数:
            return
        self.依赖函数.add(target)

    def 分析(self, 仅分析函数声明: bool = False):
        """
        解析 Python 源码，遍历 AST 以分析类型和依赖，但不进行编译。
        此步骤对于推断返回类型和参数类型至关重要。
        """
        # 避免重复分析
        if self.分析完成 and self.仅分析函数声明 == 仅分析函数声明:
            return
        self.仅分析函数声明 = 仅分析函数声明
        # 清理源码缩进，防止因函数嵌套在类或其他块中导致的缩进错误
        lines = self.源代码.split("\n")
        cleaned_lines = []
        first_non_whitespace = None

        for line in lines:
            stripped = line.lstrip()
            if stripped:
                first_non_whitespace = len(line) - len(stripped)
                break

        if first_non_whitespace is not None:
            for line in lines:
                stripped = line.lstrip()
                if not stripped:
                    continue
                cleaned_lines.append(line[first_non_whitespace:])

        cleaned_source = "\n".join(cleaned_lines)
        if not cleaned_source:  # 处理空函数的情况
            cleaned_source = "def dummy(): pass"

        tree = ast.parse(cleaned_source, mode="exec")

        self.visit(tree)
        self.分析完成 = True

    def 尝试编译(self):
        """调用编译后的函数（延迟编译：首次调用时才编译）"""
        if self.已编译 or self.可执行文件名 is not None:
            return
        # 检查是否需要编译
        if self.总是重编 or not self.编译管理器.文件是否存在(self.获取库文件名()):
            self.编译()
        else:
            self.分析(True)

    def 编译(self):
        """
        执行完整的编译流程：分析 -> 生成 C++ 代码 -> 编译为动态库/可执行文件。
        """
        try:
            # 清除旧的库缓存，确保使用新编译的库
            self.目标库 = None
            self.cpp函数 = None
            self.分析()
            # 使用并行编译管理器编译依赖函数
            all_lib_files = set()
            all_source_files = set([self.编译管理器.获取完整路径(self.获取cpp文件名())])
            for dep in self.依赖函数:
                dep.尝试编译()
                self.编译管理器.包含头文件.add(f'"{dep.获取头文件名()}"')
                all_lib_files.add(dep.编译管理器.获取完整路径(dep.获取库文件名()))
            # 在添加依赖头文件之后生成代码，确保生成的C++代码包含依赖函数的声明
            self.代码生成器.保存代码到文件()
            # 添加工作目录到库搜索路径，以便找到编译好的类库
            self.编译器.添加库目录(全局上下文.工作目录)
            self.编译器.添加库目录(list(self.编译管理器.库搜索目录))
            self.编译器.添加库(list(self.编译管理器.链接库))
            output_path = self.编译管理器.获取完整路径(self.获取库文件名())
            # 使用编译管理器执行编译
            all_files = list(all_source_files) + list(all_lib_files)
            self.编译管理器.执行编译(
                all_files,
                output_path,
                是否为可执行文件=bool(self.可执行文件名)
            )
        except Exception as e:
            # 编译失败时清理临时文件
            self.清理编译文件()
            # 如果是编译错误，包装并重新抛出
            if isinstance(e, (RuntimeError, OSError)):
                raise 编译错误(
                    f"编译失败: {str(e)}",
                    compiler_output=str(e),
                    source_file=self.编译管理器.获取完整路径(self.获取cpp文件名()),
                    python_source=self.源代码
                ) from e
            else:
                raise
        # 编译成功后标记为已编译（用于类和非延迟编译的场景）
        self.已编译 = True

    def 清理编译文件(self):
        """清理编译失败时产生的临时文件"""
        files_to_clean = [
            self.获取cpp文件名(),
            self.获取头文件名(),
            self.获取库文件名()
        ]
        self.编译管理器.清理编译文件(files_to_clean)

    def 清理所有缓存(self):
        """清理所有缓存文件（手动清理接口）"""
        return self.编译管理器.清理所有缓存()

    def 检查缓存完整性(self):
        """检查缓存文件的完整性"""
        return self.编译管理器.检查缓存完整性(
            lambda: (self.获取cpp文件名(), self.获取头文件名(), self.获取库文件名())
        )

    def 添加代码(self, code: str, lineno: Optional[int] = None):
        """添加一行 C++ 代码"""
        # 使用 StringIO 而不是列表，提升性能
        self.代码缓冲区.write(code)
        self.代码缓冲区.write("\n")

    def 添加代码带行号(self, code: str, node: Union[ast.stmt, ast.expr, ast.arg, ast.arguments]):
        """添加一行C++代码并自动获取行号"""
        lineno = getattr(node, "lineno", None)
        self.添加代码(code, lineno)

    # 变量作用域管理方法（委托给变量管理器）
    def 进入作用域(self):
        """进入新的作用域（如 if/for 块内部）"""
        self.变量管理器.进入作用域()

    def 退出作用域(self):
        """退出当前作用域"""
        self.变量管理器.退出作用域()

    def 获取C变量(self, name: str) -> Optional[Any]:
        """从当前及上层作用域查找 C 变量"""
        return self.变量管理器.获取C变量(name)

    def 添加C变量(self, variable: C变量):
        """在当前作用域注册 C 变量"""
        self.变量管理器.添加C变量(variable)

    def 获取值(self, value, is_type_annotation=False):
        """
        将 AST 节点转换为对应的值或 C++ 表达式字符串。
        处理常量、变量名、属性访问、函数调用、运算表达式等。
        """
        return self.表达式访问者.获取值(value, is_type_annotation)

    # 文件操作相关方法
    def 获取文件前缀(self):
        return self.文件前缀

    def 获取无扩展名文件名(self):
        return f"{self.文件前缀}{self.代码哈希}"

    def 获取头文件名(self):
        return f"{self.获取无扩展名文件名()}.h"

    def 获取cpp文件名(self):
        return f"{self.获取无扩展名文件名()}.cpp"

    def 获取库文件名(self):
        if self.可执行文件名:
            return self.可执行文件名
        return f"{self.获取无扩展名文件名()}.so"

    def 获取链接库名(self):
        """获取用于链接的库名（不带.so扩展名）"""
        if self.可执行文件名:
            return self.可执行文件名
        return self.获取无扩展名文件名()

    def 生成定义(self):
        """生成 C 函数定义/声明，或 C++ 类定义"""
        return self.代码生成器.生成函数定义()

    def 获取包含代码(self):
        """生成包含头文件的代码"""
        return self.代码生成器.生成包含代码()

    def 获取头文件代码(self):
        """生成头文件完整代码"""
        return self.代码生成器.生成头文件代码()

    def 获取cpp代码(self):
        """生成cpp文件完整代码"""
        return self.代码生成器.生成cpp代码()

    def 保存代码到文件(self):
        """保存代码到文件"""
        self.代码生成器.保存代码到文件()

    def 加载库(self):
        """加载编译好的动态库（仅首次调用时加载）"""
        if self.目标库 is not None:
            return
        for dep in self.依赖函数:
            dep.加载库()
        # 首次加载
        lib_path = self.编译管理器.获取完整路径(self.获取库文件名())
        # 如果是类，只加载库到全局命名空间，不获取函数符号
        self.目标库 = ctypes.CDLL(lib_path, mode=ctypes.RTLD_GLOBAL)
        if self.是类:
            self.cpp函数 = None
        else:
            self.cpp函数 = self.目标库[self.C函数名]
            self.cpp函数.argtypes = self.ctypes参数类型
            self.cpp函数.restype = self.ctypes返回类型

    def __call__(self, *args, **kwargs):
        self.尝试编译()
        self.加载库()
        if self.cpp函数 is None:
            return
        return self.cpp函数(*args, **kwargs)

    # AST访问方法重写
    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        if self.是类:
            # 委托给类支持处理器
            if self.类支持处理器 is None:
                self.抛出错误("类支持处理器未初始化，但当前正在处理类", node)
            else:
                self.类支持处理器.访问方法节点(node)
        else:
            # 处理普通函数
            with self.代码块上下文:
                # 处理函数参数
                self.语句访问者.visit_arguments(node.args)
                if not self.仅分析函数声明:
                    for stmt in node.body:
                        self.visit(stmt)

        # 分析返回类型（仅对非类方法）
        if not self.是类:
            self.推断函数返回类型(node)

    def 推断函数返回类型(self, node: ast.FunctionDef):
        """推断普通函数的返回类型"""
        if isinstance(node.returns, ast.Name):
            py类型 = self.获取值(node.returns)
            self.返回类型 = self.解析类型(py类型)
            if not self.可执行文件名:
                self.ctypes返回类型 = 类型转换器.Python类型转ctypes(py类型)
        else:
            self.返回类型 = "auto"
            self.ctypes返回类型 = None

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        # 委托给类支持处理器
        if self.类支持处理器:
            self.类支持处理器.处理类定义(node)
        else:
            if hasattr(self, "抛出错误"):
                self.抛出错误(
                    "Class definition not supported in function context", node
                )
            else:
                raise Jit错误(
                    "Class definition not supported in function context")

    def generic_visit(self, node):
        """
        通用的访问方法，将未处理的节点委托给相应的访问者
        """
        # 优先委托给语句访问者
        if hasattr(self.语句访问者, f'visit_{node.__class__.__name__}'):
            return getattr(self.语句访问者, f'visit_{node.__class__.__name__}')(node)
        # 其次委托给表达式访问者
        elif hasattr(self.表达式访问者, f'visit_{node.__class__.__name__}'):
            return getattr(self.表达式访问者, f'visit_{node.__class__.__name__}')(node)
        # 最后调用父类的默认处理
        else:
            return super().generic_visit(node)
