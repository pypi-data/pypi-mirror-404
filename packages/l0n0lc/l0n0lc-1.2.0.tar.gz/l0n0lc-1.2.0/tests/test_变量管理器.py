"""
变量管理器模块的单元测试
"""

import unittest
from l0n0lc.变量管理器 import 变量管理器
from l0n0lc.cpp类型 import C变量


class Test变量管理器初始化(unittest.TestCase):
    """测试变量管理器的初始化"""

    def test_初始化状态(self):
        """测试初始化后的状态"""
        manager = 变量管理器()
        self.assertEqual(manager.当前作用域层级, 0)
        self.assertEqual(len(manager.作用域变量), 1)
        self.assertEqual(manager.获取当前作用域变量数(), 0)
        self.assertEqual(manager.获取所有作用域变量数(), 0)


class Test变量管理器作用域操作(unittest.TestCase):
    """测试变量管理器的作用域操作"""

    def setUp(self):
        """每个测试前的设置"""
        self.manager = 变量管理器()

    def test_进入作用域(self):
        """测试进入新作用域"""
        self.manager.进入作用域()
        self.assertEqual(self.manager.当前作用域层级, 1)
        self.assertEqual(len(self.manager.作用域变量), 2)

        self.manager.进入作用域()
        self.assertEqual(self.manager.当前作用域层级, 2)
        self.assertEqual(len(self.manager.作用域变量), 3)

    def test_退出作用域(self):
        """测试退出作用域"""
        self.manager.进入作用域()
        self.manager.进入作用域()
        self.assertEqual(self.manager.当前作用域层级, 2)

        self.manager.退出作用域()
        self.assertEqual(self.manager.当前作用域层级, 1)

        self.manager.退出作用域()
        self.assertEqual(self.manager.当前作用域层级, 0)

    def test_退出根作用域(self):
        """测试从根作用域退出（不应该报错）"""
        # 根作用域层级为 0
        self.assertEqual(self.manager.当前作用域层级, 0)

        # 尝试退出根作用域不应该报错
        self.manager.退出作用域()
        self.assertEqual(self.manager.当前作用域层级, 0)


class Test变量管理器变量操作(unittest.TestCase):
    """测试变量管理器的变量操作"""

    def setUp(self):
        """每个测试前的设置"""
        self.manager = 变量管理器()
        # 创建一些测试变量 (类型名, 名称, 是否参数, 默认值)
        self.var1 = C变量("int", "x", False, "0")
        self.var2 = C变量("float", "y", False, "0.0")
        self.var3 = C变量("int", "z", False, "1")

    def test_添加变量(self):
        """测试添加变量"""
        self.manager.添加C变量(self.var1)
        self.assertEqual(self.manager.获取当前作用域变量数(), 1)

        self.manager.添加C变量(self.var2)
        self.assertEqual(self.manager.获取当前作用域变量数(), 2)

    def test_获取变量(self):
        """测试获取变量"""
        self.manager.添加C变量(self.var1)
        self.manager.添加C变量(self.var2)

        # 获取存在的变量
        result = self.manager.获取C变量("x")
        self.assertIs(result, self.var1)

        result = self.manager.获取C变量("y")
        self.assertIs(result, self.var2)

    def test_获取不存在的变量(self):
        """测试获取不存在的变量"""
        result = self.manager.获取C变量("nonexistent")
        self.assertIsNone(result)

    def test_变量是否存在(self):
        """测试变量是否存在"""
        self.manager.添加C变量(self.var1)

        self.assertTrue(self.manager.变量是否存在("x"))
        self.assertFalse(self.manager.变量是否存在("y"))

    def test_跨作用域变量查找(self):
        """测试跨作用域变量查找"""
        # 在根作用域添加变量
        self.manager.添加C变量(self.var1)

        # 进入新作用域
        self.manager.进入作用域()

        # 在新作用域应该能找到根作用域的变量
        result = self.manager.获取C变量("x")
        self.assertIs(result, self.var1)

        # 在新作用域添加同名变量会覆盖
        var1_new = C变量("int", "x", False, "2")
        self.manager.添加C变量(var1_new)

        # 应该获取到新作用域的变量
        result = self.manager.获取C变量("x")
        self.assertIs(result, var1_new)
        self.assertEqual(result.默认值, "2")

    def test_作用域隔离(self):
        """测试作用域隔离"""
        # 在根作用域添加变量
        self.manager.添加C变量(self.var1)
        self.manager.添加C变量(self.var2)

        # 进入新作用域
        self.manager.进入作用域()

        # 在新作用域添加变量
        self.manager.添加C变量(self.var3)

        # 新作用域应该只有1个变量
        self.assertEqual(self.manager.获取当前作用域变量数(), 1)

        # 总变量数应该是3个
        self.assertEqual(self.manager.获取所有作用域变量数(), 3)

        # 退出作用域后，新作用域的变量应该消失
        self.manager.退出作用域()
        self.assertEqual(self.manager.获取当前作用域变量数(), 2)
        self.assertEqual(self.manager.获取所有作用域变量数(), 2)


class Test变量管理器清空操作(unittest.TestCase):
    """测试变量管理器的清空操作"""

    def setUp(self):
        """每个测试前的设置"""
        self.manager = 变量管理器()
        self.var1 = C变量("int", "x", False, "0")
        self.var2 = C变量("float", "y", False, "0.0")

    def test_清空所有作用域(self):
        """测试清空所有作用域"""
        # 添加一些作用域和变量
        self.manager.添加C变量(self.var1)
        self.manager.进入作用域()
        self.manager.添加C变量(self.var2)
        self.manager.进入作用域()

        # 验证状态
        self.assertEqual(self.manager.当前作用域层级, 2)
        self.assertEqual(self.manager.获取所有作用域变量数(), 2)

        # 清空
        self.manager.清空所有作用域()

        # 验证清空后的状态
        self.assertEqual(self.manager.当前作用域层级, 0)
        self.assertEqual(len(self.manager.作用域变量), 1)
        self.assertEqual(self.manager.获取当前作用域变量数(), 0)
        self.assertEqual(self.manager.获取所有作用域变量数(), 0)


class Test变量管理器状态摘要(unittest.TestCase):
    """测试变量管理器的状态摘要"""

    def test_获取状态摘要(self):
        """测试获取状态摘要"""
        manager = 变量管理器()
        var1 = C变量("int", "x", False, "0")
        var2 = C变量("float", "y", False, "0.0")

        # 添加变量
        manager.添加C变量(var1)
        manager.添加C变量(var2)

        # 进入新作用域
        manager.进入作用域()
        var3 = C变量("int", "z", False, "1")
        manager.添加C变量(var3)

        # 获取状态摘要
        summary = manager.获取状态摘要()

        self.assertEqual(summary["当前作用域层级"], 1)
        self.assertEqual(summary["作用域总数"], 2)
        self.assertEqual(summary["当前作用域变量数"], 1)
        self.assertEqual(summary["总变量数"], 3)


class Test变量管理器边界情况(unittest.TestCase):
    """测试变量管理器的边界情况"""

    def test_同名变量在不同作用域(self):
        """测试同名变量在不同作用域"""
        manager = 变量管理器()
        var1 = C变量("int", "x", False, "0")
        var2 = C变量("int", "x", False, "1")

        # 在根作用域添加
        manager.添加C变量(var1)

        # 在新作用域添加同名变量
        manager.进入作用域()
        manager.添加C变量(var2)

        # 应该获取到内层的变量
        result = manager.获取C变量("x")
        self.assertIs(result, var2)

        # 退出内层作用域后，应该获取到外层的变量
        manager.退出作用域()
        result = manager.获取C变量("x")
        self.assertIs(result, var1)

    def test_深层嵌套作用域(self):
        """测试深层嵌套作用域"""
        manager = 变量管理器()

        # 创建多层嵌套
        for i in range(10):
            manager.进入作用域()
            var = C变量("int", f"x{i}", False, "0")
            manager.添加C变量(var)

        self.assertEqual(manager.当前作用域层级, 10)
        self.assertEqual(len(manager.作用域变量), 11)

        # 应该能找到最深层的变量
        result = manager.获取C变量("x9")
        self.assertIsNotNone(result)

        # 应该能找到根作用域的变量
        result = manager.获取C变量("x0")
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
