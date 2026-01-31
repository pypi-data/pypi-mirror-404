import ast
from typing import Union
from .cpp类型 import C变量, Cpp类型, 字典初始化列表, 列表初始化列表, 集合初始化列表
from .std_vector import 标准列表
from .std_map import 标准无序映射
from .std_set import 标准集合
from .类型转换 import 类型转换器
from .基础混入 import 错误处理混入, 类型处理混入
from .表达式处理 import 表达式访问者


class 代码生成器(错误处理混入, 类型处理混入):
    """负责生成C++代码的类"""

    def __init__(self, transpiler):
        from .Py转Cpp转译器 import Py转Cpp转译器
        self.transpiler:Py转Cpp转译器 = transpiler

    def _assign(
        self, target_node, value, context_node, cast_type: Union[str, None] = None
    ):
        """处理赋值操作"""
        try:
            target_var = self.transpiler.获取值(target_node)
        except Exception:
            # 如果获取值失败，说明这是一个复杂的表达式赋值目标
            # 这种情况下我们让代码继续，target_var为None会在后续处理中被捕获
            target_var = None
        except KeyboardInterrupt:
            raise

        # 处理 Python 变量的直接赋值 (仅在 正在直接调用 模式下)
        if self.transpiler.正在直接调用:
            if isinstance(target_node, ast.Name):
                self.transpiler.本地变量[target_node.id] = value
            else:
                self.抛出错误("Direct assignment only supports simple names", context_node)
            self.transpiler.正在直接调用 = False
            return

        if target_var is None:
            # 新变量声明
            if isinstance(target_node, ast.Name):
                if isinstance(value, 字典初始化列表):
                    target_var = 标准无序映射(value, target_node.id, False)
                    self.transpiler.编译管理器.包含头文件.add("<unordered_map>")
                    # 如果键或值类型包含string，添加string头文件
                    if "std::string" in str(target_var.类型名):
                        self.transpiler.编译管理器.包含头文件.add("<string>")
                elif isinstance(value, 列表初始化列表):
                    target_var = 标准列表(value, target_node.id, False)
                    self.transpiler.编译管理器.包含头文件.add("<vector>")
                    if value.类型名 == Cpp类型.任意:
                        self.transpiler.编译管理器.包含头文件.add("<any>")
                elif isinstance(value, 集合初始化列表):
                    target_var = 标准集合(value, target_node.id, False)
                    self.transpiler.编译管理器.包含头文件.add("<unordered_set>")
                else:
                    target_var = C变量("auto", target_node.id, False)

                self.transpiler.添加代码(target_var.初始化代码(value, cast_type),
                                  getattr(context_node, 'lineno', None))
                self.transpiler.变量管理器.添加C变量(target_var)
            else:
                self.抛出错误("Assignment target must be a name", context_node)
        else:
            # 现有变量赋值
            target_name = (
                target_var.C名称 if hasattr(target_var, "C名称") else str(target_var)
            )
            if cast_type:
                self.transpiler.添加代码(f"{target_name} = ({cast_type})({value});",
                                         getattr(context_node, 'lineno', None))
            else:
                self.transpiler.添加代码(f"{target_name} = {value};",
                                         getattr(context_node, 'lineno', None))

    def 生成函数定义(self):
        """生成 C 函数定义/声明，或 C++ 类定义"""
        if self.transpiler.是类:
            return self.生成类定义()
        else:
            return self.生成函数声明()

    def 生成函数声明(self):
        """生成函数声明"""
        params = []
        for name, var in self.transpiler.参数变量.items():
            if isinstance(var, C变量):
                params.append(f"{var.类型名} {var.C名称}")

        param_str = ", ".join(params)
        return f'extern "C" {self.transpiler.返回类型} {self.transpiler.C函数名} ({param_str})'

    def 生成类定义(self):
        """生成类定义 struct Name { ... };"""
        # 处理继承
        继承代码 = ""
        if self.transpiler.类基类列表:
            基类名列表 = []
            for 基类 in self.transpiler.类基类列表:
                基类名列表.append(f"public {基类.__name__}")
            继承代码 = " : " + ", ".join(基类名列表)

        # 静态成员声明
        static_fields = []
        for 变量名, (变量类型, 默认值) in self.transpiler.类静态成员.items():
            static_fields.append(f"    static {变量类型} {变量名};")

        # 实例成员变量
        成员变量列表 = []
        for 变量名, 变量类型 in self.transpiler.类成员变量.items():
            成员变量列表.append(f"    {变量类型} {变量名};")

        # 方法声明
        函数声明列表 = []

        # 如果有默认值但没有显式构造函数，声明默认构造函数
        有显示的构造函数 = any(类方法.是构造函数 for 类方法 in self.transpiler.类方法列表)
        if self.transpiler.类成员默认值 and not 有显示的构造函数:
            函数声明列表.append(f"    {self.transpiler.C函数名}();")

        for m in self.transpiler.类方法列表:
            # 构建方法修饰符
            modifiers = []
            if m.是静态方法:
                modifiers.append("static")

            modifier_str = " ".join(modifiers) + " " if modifiers else ""

            if m.是构造函数:
                # 构造函数
                函数声明列表.append(f"    {modifier_str}{m.名称}({m.参数列表});")
            else:
                # 普通方法或运算符
                函数声明列表.append(
                    f"    {modifier_str}{m.返回类型} {m.名称}({m.参数列表});"
                )

        # 组合所有部分
        all_members = static_fields + 成员变量列表
        if all_members and 函数声明列表:
            all_members.append("")  # 空行分隔成员和方法
        all_members.extend(函数声明列表)

        struct_body = "\n".join(all_members)
        return f"struct {self.transpiler.C函数名}{继承代码} {{\n{struct_body}\n}};"

    def 生成包含代码(self):
        """生成包含头文件的代码"""
        return "\n".join([f"#include {d}" for d in sorted(self.transpiler.编译管理器.包含头文件)])

    def 生成头文件代码(self):
        """生成头文件完整代码"""
        return f"#pragma once\n{self.生成包含代码()}\n{self.生成函数定义()};"

    def 生成cpp代码(self):
        """生成cpp文件完整代码"""
        if self.transpiler.是类:
            return self.生成类实现代码()
        else:
            return self.生成函数实现代码()

    def 生成类实现代码(self):
        """生成类的实现代码"""
        parts = []

        # 1. 包含头文件
        parts.append(f'#include "{self.transpiler.获取头文件名()}"')

        # 2. 静态成员定义
        if self.transpiler.类静态成员:
            parts.append("")  # 空行
            for name, (type_, value) in self.transpiler.类静态成员.items():
                # 生成静态成员定义
                if isinstance(value, str):
                    parts.append(
                        f'{type_} {self.transpiler.C函数名}::{name} = "{value}";'
                    )
                elif isinstance(value, bool):
                    parts.append(
                        f'{type_} {self.transpiler.C函数名}::{name} = {"true" if value else "false"};'
                    )
                else:
                    parts.append(
                        f"{type_} {self.transpiler.C函数名}::{name} = {value};"
                    )

        # 3. 默认构造函数（如果有默认值且没有显式定义构造函数）
        has_explicit_init = any(m.是构造函数 for m in self.transpiler.类方法列表)
        if self.transpiler.类成员默认值 and not has_explicit_init:
            # 生成默认构造函数
            parts.append("")
            initializers = []
            for name, default_val in self.transpiler.类成员默认值.items():
                if isinstance(default_val, str):
                    initializers.append(f'{name}("{default_val}")')
                else:
                    initializers.append(f"{name}({default_val})")

            if initializers:
                init_list = ", ".join(initializers)
                parts.append(
                    f"{self.transpiler.C函数名}::{self.transpiler.C函数名}() : {init_list} {{}}"
                )
            else:
                parts.append(
                    f"{self.transpiler.C函数名}::{self.transpiler.C函数名}() {{}}"
                )

        # 4. 方法实现
        impls = []
        for m in self.transpiler.类方法列表:
            # 静态方法需要 static 修饰符
            modifier = "static " if m.是静态方法 else ""

            full_name = f"{self.transpiler.C函数名}::{m.名称}"
            if m.是构造函数:
                # 构造函数实现
                head = f"{full_name}({m.参数列表})"

                # 构建初始化列表
                initializers = []

                # 如果有基类，首先添加基类构造函数调用
                if self.transpiler.类基类列表:
                    base_class = self.transpiler.类基类列表[0]
                    base_name = base_class.__name__
                    # 对于构造函数参数，我们需要传递第一个参数给基类构造函数
                    # 这里假设第一个参数是name，与基类构造函数匹配
                    if m.参数列表:
                        # 提取第一个参数名（去掉类型声明，只保留参数名）
                        first_param_full = m.参数列表.split(",")[0].strip()
                        # 参数格式可能是 "std::string name" 或 "int x" 等，我们只需要参数名部分
                        if " " in first_param_full:
                            first_param = first_param_full.split()[-1]
                        else:
                            first_param = first_param_full
                        initializers.append(f"{base_name}({first_param})")
                    else:
                        # 如果没有参数，调用基类默认构造函数
                        initializers.append(f"{base_name}()")

                # 如果有默认值，添加成员变量初始化
                if self.transpiler.类成员默认值:
                    for name, default_val in self.transpiler.类成员默认值.items():
                        if isinstance(default_val, str):
                            initializers.append(f'{name}("{default_val}")')
                        else:
                            initializers.append(f"{name}({default_val})")

                if initializers:
                    init_list = ", ".join(initializers)
                    head = f"{full_name}({m.参数列表}) : {init_list}"
            else:
                # 普通方法或运算符
                head = f"{m.返回类型} {full_name}({m.参数列表})"

            body_lines = [str(line) for line in m.方法体]
            body_str = "\n".join(body_lines)
            impls.append(f"{head}\n{body_str}")

        if impls:
            parts.append("")
            parts.extend(impls)

        return "\n".join(parts)

    def 生成函数实现代码(self):
        """生成函数的实现代码"""
        # 获取Python源码行，用于生成注释
        source_lines = self.transpiler.源代码.split('\n')

        # 直接从 StringIO 获取生成的代码
        body_code = self.transpiler.代码缓冲区.getvalue()

        # 生成完整的C++代码
        parts = []
        parts.append(f'#include "{self.transpiler.获取头文件名()}"')
        parts.append("")  # 空行
        parts.append("// === Python 源码 ===")
        for i, line in enumerate(source_lines, 1):
            parts.append(f"// 第{i:2d}行: {line}")
        parts.append("")
        parts.append("// === C++ 实现 ===")
        parts.append(self.生成函数声明())
        parts.append("{")
        if body_code.strip():
            # 将 body_code 按行分割并添加到 parts
            for line in body_code.strip().split('\n'):
                parts.append(line)
        parts.append("}")

        return "\n".join(parts)

    def 保存代码到文件(self):
        """保存代码到文件"""
        # 清理旧文件
        self.transpiler.编译管理器.清理旧文件(self.transpiler.文件前缀)

        # 保存头文件
        self.transpiler.编译管理器.写入文件(
            self.transpiler.获取头文件名(),
            self.生成头文件代码()
        )

        # 保存 cpp 文件
        self.transpiler.编译管理器.写入文件(
            self.transpiler.获取cpp文件名(),
            self.生成cpp代码()
        )

    def 构建当前参数列表字符串(self):
        """构建当前方法的参数列表字符串（用于类方法）"""
        params = []
        # 使用 当前方法参数 而非 参数变量，确保参数隔离
        param_dict = (
            self.transpiler.当前方法参数
            if self.transpiler.当前方法参数
            else self.transpiler.参数变量
        )

        for name, var in param_dict.items():
            if name in ["self", "cls"]:
                continue  # Skip self/cls if present

            if isinstance(var, C变量):
                params.append(f"{var.类型名} {var.C名称}")
        return ", ".join(params)


class 参数处理器(错误处理混入, 类型处理混入):
    """处理函数参数的类"""

    def __init__(self, transpiler):
        from .Py转Cpp转译器 import Py转Cpp转译器
        self.transpiler: Py转Cpp转译器 = transpiler

    def 处理参数列表(self, node: ast.arguments):
        """处理参数列表"""
        self.transpiler.正在构建参数 = True

        args = list(node.args)
        if node.vararg:
            # C++ 变长参数处理复杂，暂不支持
            self.抛出错误("*args not supported", node)

        for idx, arg in enumerate(args):
            default_val = None
            if idx >= len(args) - len(node.defaults):
                default_val = node.defaults[idx - (len(args) - len(node.defaults))]
            self.处理参数(arg, default_val)

        self.transpiler.正在构建参数 = False

    def 处理参数(self, node: ast.arg, default_val=None):
        """处理单个参数"""
        name = node.arg
        # 记录参数名称
        self.transpiler.参数名称.append(name)
        # 处理self/cls参数
        if node.annotation is None:
            # 对于类方法的self/cls参数，不需要类型注解
            if self.transpiler.是类 and name in ["self", "cls"]:
                # self/cls参数不会被添加到参数列表中（已在visit_FunctionDef中处理）
                return
            else:
                self.抛出错误(f"Argument '{name}' must have type annotation", node)
        
        # 获取参数类型
        py类型 = self.transpiler.表达式访问者.获取值(node.annotation, is_type_annotation=True)
        # 处理字符串类型注解（如 'Vector2D'）
        if isinstance(py类型, str):
            py类型 = self.transpiler.全局变量[py类型]
        c类型 = self.解析类型(py类型)
        if c类型 is None:
            self.抛出错误(f"Unsupported type {py类型}", node)

        # 检查并添加容器类型的头文件
        c类型_str = str(c类型)
        if c类型_str.startswith("std::unordered_set"):
            self.transpiler.编译管理器.包含头文件.add("<unordered_set>")
        elif c类型_str.startswith("std::unordered_map"):
            self.transpiler.编译管理器.包含头文件.add("<unordered_map>")
            # 如果键或值类型包含string，添加string头文件
            if "std::string" in c类型_str:
                self.transpiler.编译管理器.包含头文件.add("<string>")
        elif c类型_str.startswith("std::vector"):
            self.transpiler.编译管理器.包含头文件.add("<vector>")
        elif c类型_str.startswith("std::string"):
            self.transpiler.编译管理器.包含头文件.add("<string>")

        # 创建普通C变量
        self.transpiler.参数变量[name] = C变量(str(c类型), name, True)
        if not self.transpiler.可执行文件名:
            self.transpiler.ctypes参数类型.append(
                类型转换器.Python类型转ctypes(py类型)
            )
