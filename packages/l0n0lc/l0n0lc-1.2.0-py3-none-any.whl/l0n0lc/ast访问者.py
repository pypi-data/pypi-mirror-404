import ast
from typing import Any, Union, cast
from .cpp类型 import (
    列表初始化列表, 字典初始化列表, 集合初始化列表,
    SuperCallWrapper, C变量
)
from .容器构建器 import 容器构建器
from .std_map import 标准无序映射
from .std_set import 标准集合
from .std_array import 标准数组
from .std_vector import 标准列表
from .基础混入 import 错误处理混入, 参数处理混入, 类型处理混入
from .工具 import _ArrayCallResult, _ArrayInstance

class AST访问者基类(错误处理混入, 参数处理混入, 类型处理混入):
    """AST节点访问的基类，提供基础的访问方法"""

    def __init__(self, transpiler):
        from .Py转Cpp转译器 import Py转Cpp转译器
        self.transpiler:Py转Cpp转译器 = transpiler

    def 计算比较(self, node: ast.Compare) -> Any:
        """处理比较运算 (==, !=, <, >, <=, >=, in, not in)"""
        # 调用transpiler的获取值方法
        left = self.transpiler.获取值(node.left)
        comparisons = []

        curr_left = left

        for op, comp in zip(node.ops, node.comparators):
            curr_right = self.transpiler.获取值(comp)

            op_str = ""
            if isinstance(op, ast.Eq):
                op_str = "=="
            elif isinstance(op, ast.NotEq):
                op_str = "!="
            elif isinstance(op, ast.Lt):
                op_str = "<"
            elif isinstance(op, ast.LtE):
                op_str = "<="
            elif isinstance(op, ast.Gt):
                op_str = ">"
            elif isinstance(op, ast.GtE):
                op_str = ">="

            if op_str:
                comparisons.append(f"({curr_left} {op_str} {curr_right})")
            elif isinstance(op, (ast.In, ast.NotIn)):
                # Check optimized contains
                contains_expr = None
                # Try to use __contains__ if available on the wrapper object
                if hasattr(curr_right, "__contains__"):
                    try:
                        contains_expr = curr_right.__contains__(curr_left)
                    except (AttributeError, TypeError, ValueError):
                        pass
                    except KeyboardInterrupt:
                        raise

                if not contains_expr:
                    # Generic std::find fallback
                    self.transpiler.编译管理器.包含头文件.add("<algorithm>")
                    self.transpiler.编译管理器.包含头文件.add("<iterator>")
                    contains_expr = f"(std::find(std::begin({curr_right}), std::end({curr_right}), {curr_left}) != std::end({curr_right}))"

                if isinstance(op, ast.In):
                    comparisons.append(f"({contains_expr})")
                else:
                    comparisons.append(f"!({contains_expr})")
            else:
                self.抛出错误(
                    f"Unsupported comparison operator: {type(op).__name__}", node
                )

            curr_left = curr_right

        if len(comparisons) == 1:
            return comparisons[0]
        return f'({" && ".join(comparisons)})'

    def 计算二元运算(self, node: Union[ast.BinOp, ast.AugAssign]):
        """处理二元运算 (+, -, *, /, %, <<, >>, &, |, ^)"""
        if isinstance(node, ast.BinOp):
            left = self.transpiler.获取值(node.left)
            right = self.transpiler.获取值(node.right)
            op = node.op
        elif isinstance(node, ast.AugAssign):
            left = self.transpiler.获取值(node.target)
            right = self.transpiler.获取值(node.value)
            op = node.op
        else:
            return None

        op_str = ""
        if isinstance(op, ast.Add):
            op_str = "+"
        elif isinstance(op, ast.Sub):
            op_str = "-"
        elif isinstance(op, ast.Mult):
            op_str = "*"
        elif isinstance(op, (ast.Div, ast.FloorDiv)):
            op_str = "/"
        elif isinstance(op, ast.Mod):
            op_str = "%"
        elif isinstance(op, ast.BitAnd):
            op_str = "&"
        elif isinstance(op, ast.BitOr):
            op_str = "|"
        elif isinstance(op, ast.BitXor):
            op_str = "^"
        elif isinstance(op, ast.LShift):
            op_str = "<<"
        elif isinstance(op, ast.RShift):
            op_str = ">>"

        if op_str:
            return f"({left} {op_str} {right})"

        self.抛出错误(f"Unsupported operator: {type(op).__name__}", node)


    def 处理super调用(self, node: ast.Call):
        """处理super()调用"""
        if not self.transpiler.是类:
            self.抛出错误("super() can only be used inside a class", node)

        # 检查是否有基类
        if not self.transpiler.类基类列表:
            self.抛出错误("super() requires at least one base class", node)

        # 获取第一个基类（Python的super()通常指MRO中的下一个类）
        base_class = self.transpiler.类基类列表[0]
        base_name = base_class.__name__

        # 返回一个特殊的SuperCall对象，用于后续的属性访问处理
        return SuperCallWrapper(base_name, self.transpiler)


class 语句访问者(AST访问者基类):
    """处理所有语句类型的访问者"""

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        # 这个方法会在TranspilerCore中重写
        pass

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        # 这个方法会在ClassSupport中处理
        pass

    def visit_Return(self, node: ast.Return) -> Any:
        ret_val = self.transpiler.获取值(node.value) if node.value is not None else ""
        self.transpiler.添加代码带行号(f"return {ret_val};", node)

    def visit_If(self, node: ast.If) -> Any:
        test = self.transpiler.获取值(node.test)
        self.transpiler.添加代码带行号(f"if ({test})", node)

        with self.transpiler.代码块上下文:
            for stmt in node.body:
                self.transpiler.visit(stmt)

        if node.orelse:
            self.transpiler.添加代码带行号("else", node)
            with self.transpiler.代码块上下文:
                for stmt in node.orelse:
                    self.transpiler.visit(stmt)

    def visit_For(self, node: ast.For) -> Any:
        """处理 for 循环，委托给专门的处理方法"""
        iter_node = node.iter
        
        # 1. 特殊处理：Dict 特殊遍历
        if self._是Dict特殊遍历(node):
            self._处理Dict特殊遍历(node, iter_node)
            return
        
        # 2. 处理元组解包
        target, is_tuple = self._处理循环目标(node.target)
        
        # 3. 生成循环代码
        code = self._生成循环代码(target, is_tuple, iter_node, node)
        
        # 4. 添加循环体
        self.transpiler.添加代码(code)
        with self.transpiler.代码块上下文:
            for stmt in node.body:
                self.transpiler.visit(stmt)

    def _是Dict特殊遍历(self, node: ast.For) -> bool:
        """检查是否是 Dict 的特殊遍历"""
        if not isinstance(node.iter, ast.Call):
            return False
        if not isinstance(node.iter.func, ast.Attribute):
            return False
        return node.iter.func.attr in ('items', 'keys', 'values')
    
    def _处理Dict特殊遍历(self, node: ast.For, iter_node):
        """处理 Dict 的 items/keys/values 遍历"""
        if not isinstance(iter_node, ast.Call):
            return
        attr_node = iter_node.func
        if not isinstance(attr_node, ast.Attribute):
            return
        
        if attr_node.attr == "items":
            self._处理DictItems遍历(node, attr_node)
        elif attr_node.attr == "keys":
            self._处理DictKeys遍历(node, attr_node)
        elif attr_node.attr == "values":
            self._处理DictValues遍历(node, attr_node)
    
    def _处理DictItems遍历(self, node: ast.For, attr_node: ast.Attribute):
        """处理 Dict.items() 遍历"""
        # 检查目标是否为元组解包 (key, value)
        if not isinstance(node.target, ast.Tuple):
            self.抛出错误("Dict.items() target must be tuple with two names", node)
        target_tuple = cast(ast.Tuple, node.target)
        if len(target_tuple.elts) != 2:
            self.抛出错误("Dict.items() target must have exactly two elements", node)
        
        # 获取字典对象
        dict_obj = self.transpiler.获取值(attr_node.value)
        
        # 获取键和值的变量名
        key_target = target_tuple.elts[0]
        value_target = target_tuple.elts[1]
        
        if not isinstance(key_target, ast.Name) or not isinstance(value_target, ast.Name):
            self.抛出错误("Dict.items() target must be two names", node)
        
        key_var = C变量("auto", key_target.id, False)  # type: ignore
        value_var = C变量("auto", value_target.id, False)  # type: ignore
        
        # 使用 C++17 结构化绑定
        code = f"for (auto& [{key_var.C名称}, {value_var.C名称}] : {dict_obj})"
        
        self.transpiler.添加代码(code)
        with self.transpiler.代码块上下文:
            # 注册键和值变量
            self.transpiler.添加C变量(key_var)
            self.transpiler.添加C变量(value_var)
            for stmt in node.body:
                self.transpiler.visit(stmt)
    
    def _处理DictKeys遍历(self, node: ast.For, attr_node: ast.Attribute):
        """处理 Dict.keys() 遍历"""
        dict_obj = self.transpiler.获取值(attr_node.value)
        
        # 对于循环目标，检查是否是已存在的变量
        if isinstance(node.target, ast.Name):
            target = self.transpiler.获取C变量(node.target.id)
            if target is None:
                # 创建新变量
                target = C变量("auto", node.target.id, False)
                self.transpiler.添加C变量(target)
        else:
            self.抛出错误("For loop target must be a name", node)
        
        # 遍历键：使用结构化绑定但只使用第一个元素
        code = f"for (auto& [{target.C名称}, _] : {dict_obj})"
        
        self.transpiler.添加代码(code)
        with self.transpiler.代码块上下文:
            for stmt in node.body:
                self.transpiler.visit(stmt)
    
    def _处理DictValues遍历(self, node: ast.For, attr_node: ast.Attribute):
        """处理 Dict.values() 遍历"""
        dict_obj = self.transpiler.获取值(attr_node.value)
        
        # 对于循环目标，检查是否是已存在的变量
        if isinstance(node.target, ast.Name):
            target = self.transpiler.获取C变量(node.target.id)
            if target is None:
                # 创建新变量
                target = C变量("auto", node.target.id, False)
                self.transpiler.添加C变量(target)
        else:
            self.抛出错误("For loop target must be a name", node)
        
        # 遍历值：使用结构化绑定但只使用第二个元素
        code = f"for (auto& [_, {target.C名称}] : {dict_obj})"
        
        self.transpiler.添加代码(code)
        with self.transpiler.代码块上下文:
            for stmt in node.body:
                self.transpiler.visit(stmt)
    
    def _处理循环目标(self, target_node):
        """处理循环目标，返回目标对象和是否为元组解包的标志"""
        # 特殊处理：元组解包目标 (如 for k, v in dict)
        if isinstance(target_node, ast.Tuple):
            targets = []
            for elt in target_node.elts:  # type: ignore
                if isinstance(elt, ast.Name):
                    var = C变量("auto", elt.id, False)
                    self.transpiler.添加C变量(var)
                    targets.append(var)
                else:
                    self.抛出错误(
                        "For loop target must be a name in tuple unpacking", target_node
                    )
            return targets, True
        else:
            # 对于for循环目标，先检查是否是已存在的变量
            if isinstance(target_node, ast.Name):
                target = self.transpiler.获取C变量(target_node.id)
                if target is None:
                    # 不存在，创建新变量
                    target = C变量("auto", target_node.id, False)
                    self.transpiler.添加C变量(target)
            else:
                # 非简单名称的情况，尝试获取值
                target = self.transpiler.获取值(target_node)
                if target is None:
                    self.抛出错误("For loop target must be a name", target_node)
            return target, False
    
    def _生成循环代码(self, target, is_tuple, iter_node, node: ast.For) -> str:
        """生成循环代码"""
        # 处理 range() 循环
        if isinstance(iter_node, ast.Call):
            return self._生成Range循环代码(target, iter_node, node)
        
        # 处理列表/元组字面量循环
        elif isinstance(iter_node, (ast.List, ast.Tuple)):
            return self._生成字面量循环代码(target, iter_node)
        
        # 处理可迭代对象循环
        else:
            return self._生成可迭代对象循环代码(target, is_tuple, iter_node)
    
    def _生成Range循环代码(self, target, iter_node: ast.Call, node: ast.For) -> str:
        """生成 range() 循环代码"""
        func = self.transpiler.获取值(iter_node.func)
        if func is range:
            args = [self.transpiler.获取值(arg) for arg in iter_node.args]
            if len(args) == 1:
                return f"for (int64_t {target} = 0; {target} < {args[0]}; ++{target})"
            elif len(args) == 2:
                return f"for (int64_t {target} = {args[0]}; {target} < {args[1]}; ++{target})"
            elif len(args) == 3:
                return f"for (int64_t {target} = {args[0]}; {target} < {args[1]}; {target} += {args[2]})"
            else:
                self.抛出错误("Invalid range arguments", node)
                return ""  # 不会执行，但满足类型检查
        else:
            call_code = self.transpiler.表达式访问者.处理调用(iter_node)
            return f"for (auto {target} : {call_code})"
    
    def _生成字面量循环代码(self, target, iter_node) -> str:
        """生成列表/元组字面量循环代码"""
        l = [self.transpiler.获取值(e) for e in iter_node.elts]
        init_list = 容器构建器._从列表构建初始化列表(l)
        return f"for (auto {target} : {init_list})"
    
    def _生成可迭代对象循环代码(self, target, is_tuple, iter_node) -> str:
        """生成可迭代对象循环代码"""
        iter_obj = self.transpiler.获取值(iter_node)
        
        # 检查是否为 Dict 类型的直接遍历
        if isinstance(iter_obj, 标准无序映射):
            if isinstance(target, list) and len(target) == 2:
                # 元组解包：k, v in dict
                return f"for (auto& [{target[0].C名称}, {target[1].C名称}] : {iter_obj})"
            else:
                # 单变量：k in dict
                target_name = target.C名称 if not isinstance(target, list) else str(target)
                return f"for (auto& [{target_name}, _] : {iter_obj})"
        else:
            if isinstance(target, list):
                # 列表遍历的元组解包
                target_names = ", ".join([t.C名称 for t in target])
                return f"for (auto& [{target_names}] : {iter_obj})"
            else:
                return f"for (auto {target} : {iter_obj})"

    def visit_Break(self, node: ast.Break):
        self.transpiler.添加代码("break;")

    def visit_Continue(self, node: ast.Continue):
        self.transpiler.添加代码("continue;")

    def visit_While(self, node: ast.While):
        test = self.transpiler.获取值(node.test)
        self.transpiler.添加代码(f"while ({test})")
        with self.transpiler.代码块上下文:
            for stmt in node.body:
                self.transpiler.visit(stmt)

    def visit_Try(self, node: ast.Try):
        """处理try-except-finally语句，委托给专门的处理方法"""
        # 1. 处理try块
        self._处理Try块(node)
        
        # 2. 处理except块
        for handler in node.handlers:
            self._处理ExceptHandler(handler)
        
        # 3. 处理finally块
        if node.finalbody:
            self._处理Finally块(node.finalbody)
    
    def _处理Try块(self, node: ast.Try):
        """处理try块"""
        self.transpiler.添加代码("try")
        with self.transpiler.代码块上下文:
            for stmt in node.body:
                self.transpiler.visit(stmt)
    
    def _处理ExceptHandler(self, handler):
        """处理except handler"""
        # 生成catch子句
        c_exc_type = self._生成异常类型(handler.type)
        catch_code = self._生成Catch子句(c_exc_type, handler.name)
        self.transpiler.添加代码(catch_code)
        
        # 处理except块体
        with self.transpiler.代码块上下文:
            if handler.name:
                # 注册异常变量到作用域
                self.transpiler.添加C变量(C变量(c_exc_type, handler.name, False))
            
            for stmt in handler.body:
                self.transpiler.visit(stmt)
    
    def _生成异常类型(self, exc_type_node):
        """生成C++异常类型"""
        if not exc_type_node:
            return "..."  # catch all
        
        exc_type = self.transpiler.获取值(exc_type_node)
        
        # 检查是否是Exception基类
        if exc_type == Exception or (
            isinstance(exc_type, str) and exc_type == "Exception"
        ):
            return "const std::exception&"
        
        # 尝试解析类型
        c_exc_type = (
            self.解析类型(exc_type)
            if not isinstance(exc_type, str)
            else exc_type
        )
        
        # 确保类型是引用
        if not c_exc_type.endswith("&") and not c_exc_type.endswith("*"):
            c_exc_type = f"const {c_exc_type}&"
        
        return c_exc_type
    
    def _生成Catch子句(self, c_exc_type: str, handler_name):
        """生成catch子句代码"""
        if handler_name:
            # e.g., except Exception as e:
            return f"catch ({c_exc_type} {handler_name})"
        else:
            # except Exception:
            return f"catch ({c_exc_type})"
    
    def _处理Finally块(self, finalbody):
        """处理finally块"""
        # C++没有finally，但可以在try-catch后执行代码模拟
        self.transpiler.添加代码(
            "// Note: finally block executed here. Warning: does not handle returns inside try/catch correcty without RAII."
        )
        for stmt in finalbody:
            self.transpiler.visit(stmt)

    def visit_Raise(self, node: ast.Raise):
        """处理raise语句，委托给专门的处理方法"""
        if node.exc:
            # 有异常表达式
            self._处理带异常的Raise(node)
        else:
            # re-raise: raise
            self._处理重新抛出()
    
    def _处理带异常的Raise(self, node: ast.Raise):
        """处理带异常表达式的raise语句"""
        exc_node = node.exc
        
        if isinstance(exc_node, ast.Call):
            # raise Exception("msg")
            self._处理Exception调用(exc_node)
        elif isinstance(exc_node, ast.Name):
            # raise e
            self._处理异常变量抛出(exc_node)
        else:
            # 其他情况，使用通用处理
            self._处理通用异常抛出(exc_node)
    
    def _处理Exception调用(self, exc_call_node: ast.Call):
        """处理 raise Exception("msg") 形式"""
        func_name = self.transpiler.获取值(exc_call_node.func)
        if self._是Exception类型(func_name):
            if exc_call_node.args:
                msg_val = self.transpiler.获取值(exc_call_node.args[0])
                self.transpiler.添加代码(
                    f"throw std::runtime_error({msg_val});"
                )
                self.transpiler.编译管理器.包含头文件.add("<stdexcept>")
            else:
                self.transpiler.添加代码("throw std::runtime_error(\"\");")
                self.transpiler.编译管理器.包含头文件.add("<stdexcept>")
        else:
            # 其他类型的异常调用
            call_code = self.transpiler.表达式访问者.处理调用(exc_call_node)
            if call_code is None:
                self.抛出错误(
                    f"Failed to generate exception call for {func_name}", 
                    exc_call_node
                )
            self.transpiler.添加代码(f"throw {call_code};")
    
    def _是Exception类型(self, func_name) -> bool:
        """检查是否是Exception类型"""
        return func_name == Exception or (
            isinstance(func_name, str) and func_name == "Exception"
        )
    
    def _处理异常变量抛出(self, exc_name_node: ast.Name):
        """处理 raise e 形式，重新抛出异常变量"""
        val = self.transpiler.获取值(exc_name_node)
        self.transpiler.添加代码(f"throw {val};")
    
    def _处理通用异常抛出(self, exc_node):
        """处理通用异常抛出"""
        val = self.transpiler.获取值(exc_node)
        self.transpiler.添加代码(f"throw {val};")
    
    def _处理重新抛出(self):
        """处理无参数的raise语句（重新抛出当前异常）"""
        self.transpiler.添加代码("throw;")

    def visit_Assign(self, node: ast.Assign):
        """处理赋值语句，委托给专门的处理方法"""
        value = self.transpiler.获取值(node.value)
        
        # 特殊处理：Array 调用结果 - a = Array(int, 3, [1, 2, 3])
        if isinstance(value, _ArrayCallResult):
            self._处理数组赋值(node, value)
        else:
            # 普通赋值
            for target in node.targets:
                self.transpiler.代码生成器._assign(target, value, node)
    
    def _处理数组赋值(self, node: ast.Assign, value: _ArrayCallResult):
        """处理 Array 调用结果的赋值"""
        # 验证目标
        if len(node.targets) != 1:
            self.抛出错误("Array assignment must have exactly one target", node)
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            self.抛出错误("Array assignment target must be a name", node)

        # 获取数组信息
        元素类型 = value.元素类型
        大小列表 = value.大小列表
        初始化列表 = value.初始化列表
        元素类型名 = str(self.解析类型(元素类型))

        # 处理初始化列表
        init_list = self._处理数组初始化列表(初始化列表, 大小列表, 元素类型名)

        # 创建并初始化数组变量
        self._创建数组变量(元素类型名, 大小列表, init_list, target.id)  # type: ignore
    
    def _处理数组初始化列表(self, 初始化列表, 大小列表, 元素类型名: str) -> 列表初始化列表:
        """处理数组的初始化列表"""
        if isinstance(初始化列表, 列表初始化列表):
            return 初始化列表
        elif isinstance(初始化列表, list):
            # 如果初始化列表是 Python list，需要先处理成 C++ 初始化列表
            return self._从Python列表构建初始化列表(初始化列表, 大小列表, 元素类型名)
        else:
            return 列表初始化列表(str(初始化列表), 元素类型名, 0)
    
    def _从Python列表构建初始化列表(self, python_list, 大小列表, 元素类型名: str) -> 列表初始化列表:
        """从 Python 列表构建 C++ 初始化列表"""
        init_code = "{"
        if len(大小列表) == 1:
            # 一维数组
            init_code += ", ".join(str(self.transpiler.获取值(v)) for v in python_list)
        else:
            # 多维数组
            inner_size = 大小列表[-1]
            for i in range(0, len(python_list), inner_size):
                inner_list = python_list[i:i+inner_size]
                init_code += "{" + ", ".join(str(self.transpiler.获取值(v)) for v in inner_list) + "}"
                if i + inner_size < len(python_list):
                    init_code += ", "
        init_code += "}"
        return 列表初始化列表(init_code, 元素类型名, len(python_list))
    
    def _创建数组变量(self, 元素类型名: str, 大小列表, init_list, target_name: str):
        """创建数组变量并生成初始化代码"""
        target_var = 标准数组(元素类型名, 大小列表, init_list, target_name, False)  # type: ignore
        
        # 生成初始化代码
        init_code = target_var.初始化代码(
            init_list.代码 if isinstance(init_list, 列表初始化列表) else str(init_list),
            None,
        )
        self.transpiler.添加代码(init_code)
        self.transpiler.添加C变量(target_var)

    def visit_AugAssign(self, node: ast.AugAssign):
        value = self.计算二元运算(node)
        self.transpiler.代码生成器._assign(node.target, value, node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        """处理类型注解赋值，委托给专门的类型处理器"""
        目标py类型 = self.transpiler.获取值(
            node.annotation, is_type_annotation=True
        )
        目标c类型 = self.解析类型(目标py类型)

        # 识别类型并委托给对应的处理器
        if 目标c类型.startswith("std::unordered_set"):
            self._处理集合类型赋值(node, 目标py类型, 目标c类型)
        elif 目标c类型.startswith("std::unordered_map"):
            self._处理映射类型赋值(node, 目标py类型, 目标c类型)
        elif isinstance(目标py类型, _ArrayInstance):
            self._处理数组类型赋值(node, 目标py类型)
        elif 目标c类型.startswith("std::vector"):
            self._处理列表类型赋值(node, 目标py类型, 目标c类型)
        else:
            # 其他类型正常处理
            value = self.transpiler.获取值(node.value)
            self.transpiler.代码生成器._assign(node.target, value, node, 目标c类型)
    
    def _处理集合类型赋值(self, node: ast.AnnAssign, 目标py类型, 目标c类型: str):
        """处理 Set[T] 类型赋值"""
        if not isinstance(node.target, ast.Name):
            self.抛出错误("Assignment target must be a name", node)

        # 获取元素类型
        origin = getattr(目标py类型, "__origin__", None)
        args = getattr(目标py类型, "__args__", [])
        if origin is set and args:
            elem_type_str = str(self.解析类型(args[0]))
        else:
            elem_type_str = "int64_t"  # fallback

        # 处理值
        value = self._处理集合值(node.value)

        # 创建集合初始化列表（如果值还不是）
        if isinstance(value, str):
            init_list = 集合初始化列表(value, elem_type_str)
        else:
            init_list = value

        target_var = 标准集合(init_list, node.target.id, False)  # type: ignore
        self.transpiler.编译管理器.包含头文件.add("<unordered_set>")
        self.transpiler.添加代码(target_var.初始化代码(value, None))
        self.transpiler.添加C变量(target_var)
    
    def _处理映射类型赋值(self, node: ast.AnnAssign, 目标py类型, 目标c类型: str):
        """处理 Dict[K, V] 类型赋值"""
        if not isinstance(node.target, ast.Name):
            self.抛出错误("Assignment target must be a name", node)

        # 获取键值类型
        origin = getattr(目标py类型, "__origin__", None)
        args = getattr(目标py类型, "__args__", [])
        if origin is dict and len(args) == 2:
            key_type_str = str(self.解析类型(args[0]))
            val_type_str = str(self.解析类型(args[1]))
        else:
            key_type_str = "int64_t"  # fallback
            val_type_str = "int64_t"

        value = self.transpiler.获取值(node.value)

        # 创建字典初始化列表（如果值还不是）
        if isinstance(value, str):
            init_list = 字典初始化列表(value, key_type_str, val_type_str)
        elif isinstance(value, 字典初始化列表):
            # 如果已经是字典初始化列表但类型是 auto，需要用正确的类型重新创建
            if value.键类型名 == "auto" or value.值类型名 == "auto":
                init_list = 字典初始化列表(value.代码, key_type_str, val_type_str)
            else:
                init_list = value
        else:
            init_list = value

        target_var = 标准无序映射(init_list, node.target.id, False)  # type: ignore
        self.transpiler.编译管理器.包含头文件.add("<unordered_map>")
        # 如果键或值类型包含string，添加string头文件
        if "std::string" in str(target_var.类型名):
            self.transpiler.编译管理器.包含头文件.add("<string>")
        self.transpiler.添加代码(
            target_var.初始化代码(
                (
                    init_list.代码
                    if isinstance(init_list, 字典初始化列表)
                    else init_list
                ),
                None,
            )
        )
        self.transpiler.添加C变量(target_var)
    
    def _处理数组类型赋值(self, node: ast.AnnAssign, 目标py类型: _ArrayInstance):
        """处理 Array[T, N] 类型赋值"""
        if not isinstance(node.target, ast.Name):
            self.抛出错误("Array assignment target must be a name", node)

        # 获取数组信息
        元素类型 = 目标py类型.元素类型
        大小列表 = 目标py类型.大小列表
        元素类型名 = str(self.解析类型(元素类型))

        # 处理值
        value = self.transpiler.获取值(node.value)

        # 如果是初始化列表，确保有正确的类型信息
        if isinstance(value, 列表初始化列表):
            if value.类型名 == "auto":
                value = 列表初始化列表(value.代码, 元素类型名, value.长度)

        # 创建数组变量
        init_list = value if isinstance(value, 列表初始化列表) else 列表初始化列表(str(value), 元素类型名, 0)
        target_var = 标准数组(元素类型名, 大小列表, init_list, node.target.id, False)  # type: ignore

        # 生成初始化代码
        init_code = target_var.初始化代码(
            init_list.代码 if isinstance(init_list, 列表初始化列表) else str(init_list),
            None,
        )
        self.transpiler.添加代码(init_code)
        self.transpiler.添加C变量(target_var)
    
    def _处理列表类型赋值(self, node: ast.AnnAssign, 目标py类型, 目标c类型: str):
        """处理 List[T] 类型赋值"""
        if not isinstance(node.target, ast.Name):
            self.抛出错误("Assignment target must be a name", node)

        # 获取元素类型
        origin = getattr(目标py类型, "__origin__", None)
        args = getattr(目标py类型, "__args__", [])
        if origin is list and args:
            elem_type_str = str(self.解析类型(args[0]))
        else:
            # 从 c_type_str 中提取类型，例如 "std::vector<int>" -> "int"
            if 目标c类型.startswith("std::vector<") and 目标c类型.endswith(">"):
                elem_type_str = 目标c类型[12:-1]  # 去掉 "std::vector<" 和 ">"
            else:
                elem_type_str = "int64_t"  # fallback

        # 处理值
        value = self.transpiler.获取值(node.value)

        # 如果是空列表或类型是 auto，需要使用正确的元素类型
        if isinstance(value, 列表初始化列表):
            if value.类型名 == "auto" or not value.代码.strip():
                # 创建带有正确类型的空列表初始化
                value = 列表初始化列表("{}", elem_type_str, 0)

        # 创建列表变量
        target_var = 标准列表(value, node.target.id, False)  # type: ignore
        self.transpiler.编译管理器.包含头文件.add("<vector>")
        self.transpiler.添加代码(
            target_var.初始化代码(
                value.代码 if isinstance(value, 列表初始化列表) else value,
                None,
            )
        )
        self.transpiler.添加C变量(target_var)
    
    def _处理集合值(self, value_node):
        """处理集合的值"""
        if isinstance(value_node, ast.Call):
            func = self.transpiler.获取值(value_node.func)
            if func is set:
                return "{}"
            else:
                return self.transpiler.获取值(value_node)
        else:
            return self.transpiler.获取值(value_node)

    def visit_Expr(self, node: ast.Expr):
        # 处理独立表达式，如函数调用语句
        if isinstance(node.value, ast.Call):
            code = self.transpiler.表达式访问者.处理调用(node.value)
            self.transpiler.添加代码(f"{code};")

    def visit_arguments(self, node: ast.arguments) -> Any:
        from .代码生成 import 参数处理器
        processor = 参数处理器(self.transpiler)
        processor.处理参数列表(node)
