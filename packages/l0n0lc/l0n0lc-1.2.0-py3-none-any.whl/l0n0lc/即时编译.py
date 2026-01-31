
import os
import inspect
from typing import Callable, Optional
from .Py转Cpp转译器 import Py转Cpp转译器
from .cpp编译器 import Cpp编译器
from .工具 import 全局上下文
from .日志工具 import 日志


def 即时编译(
    转译器类=None,
    编译器类=None,
    总是重编: bool = False,
    可执行文件名: Optional[str] = None,
    优化级别: str = 'O2'
):
    """
    JIT (即时编译) 装饰器。

    能够将受支持的 Python 函数转换为 C++ 代码，编译为动态库并加载执行。
    大大提高计算密集型任务的性能。

    注意：编译延迟到函数首次调用时才执行（可执行文件除外）。

    Args:
        转译器类: 自定义转译器类 (可选)
        编译器类: 自定义编译器类 (可选)
        总是重编: 是否每次运行都强制重新编译 (默认为 False，利用缓存)
        可执行文件名: 如果指定，将编译为独立的可执行文件而不是动态库
        优化级别: 编译优化级别，默认为 'O2'
            - O0: 无优化，编译最快，运行最慢
            - O1: 基础优化
            - O2: 标准优化（默认）
            - O3: 最大优化，编译较慢，运行最快
            - Os: 优化代码大小
            - Ofast: 激进优化（可能破坏标准合规）
            - Og: 调试优化
            - Oz: 最小代码大小
       

    Examples:
        >>> @jit()
        >>> def func(x: int) -> int:
        >>>     return x * 2

        >>> @jit(优化级别='O3')
        >>> def performance_critical(x: int) -> int:
        >>>     return x ** 2

        >>> @jit(优化级别='O0')
        >>> def fast_compile(x: int) -> int:
        >>>     return x + 1


    """
    def 装饰器(fn: Callable):
        # 输入验证
        if not callable(fn):
            raise TypeError(
                f"@jit 装饰器只能用于函数或类，得到: {type(fn).__name__}\n"
                f"请确保 @jit 装饰器应用在函数定义上，例如：\n"
                f"  @jit()\n"
                f"  def my_function():\n"
                f"      pass"
            )

        # 检查是否为异步函数
        if inspect.iscoroutinefunction(fn):
            raise NotImplementedError("暂不支持异步函数 (async/await)，请使用同步函数")

        _编译器类 = 编译器类 or Cpp编译器
        _转译器类 = 转译器类 or Py转Cpp转译器

        # 创建编译器实例
        编译器实例 = _编译器类(优化级别=优化级别)

        # 创建转译器实例，传递参数
        转译器实例 = _转译器类(fn, 编译器实例, 可执行文件名, 总是重编)

        # 可执行文件需要立即编译
        if 可执行文件名 is not None:
            库文件名 = 转译器实例.获取库文件名()
            库路径 = f'{全局上下文.工作目录}/{库文件名}'

            if 总是重编 or not os.path.exists(库路径):
                日志.缓存信息("编译", fn.__name__ if hasattr(fn, '__name__') else "unknown")
                转译器实例.编译()

        # 将转译器对象添加到目标函数的全局变量中，以便其他JIT函数可以调用它
        if hasattr(fn, '__name__'):
            转译器实例.全局变量[fn.__name__] = 转译器实例

        return 转译器实例
    return 装饰器


jit = 即时编译
