"""
文件管理器模块的单元测试（现已整合到编译管理器中）
"""

import unittest
import os
import tempfile
import shutil
from l0n0lc.编译管理器 import 编译管理器
from l0n0lc.cpp编译器 import Cpp编译器


class Test文件管理器初始化(unittest.TestCase):
    """测试文件管理器的初始化"""

    def test_初始化(self):
        """测试初始化"""
        编译器实例 = Cpp编译器(优化级别='O2')
        manager = 编译管理器("/tmp/test", 编译器实例)
        self.assertEqual(manager.工作目录, "/tmp/test")


class Test文件管理器路径操作(unittest.TestCase):
    """测试文件管理器的路径操作"""

    def setUp(self):
        """每个测试前的设置"""
        # 创建临时目录
        self.test_dir = tempfile.mkdtemp()
        编译器实例 = Cpp编译器(优化级别='O2')
        self.manager = 编译管理器(self.test_dir, 编译器实例)

    def tearDown(self):
        """每个测试后的清理"""
        # 删除临时目录
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_获取完整路径(self):
        """测试获取完整路径"""
        path = self.manager.获取完整路径("test.cpp")
        self.assertEqual(path, f"{self.test_dir}/test.cpp")

    def test_确保目录存在_创建目录(self):
        """测试确保目录存在 - 创建新目录"""
        new_dir = tempfile.mktemp()
        编译器实例 = Cpp编译器(优化级别='O2')
        manager = 编译管理器(new_dir, 编译器实例)
        self.assertFalse(os.path.exists(new_dir))

        manager.确保目录存在()
        self.assertTrue(os.path.exists(new_dir))

        # 清理
        if os.path.exists(new_dir):
            shutil.rmtree(new_dir)


class Test文件管理器文件操作(unittest.TestCase):
    """测试文件管理器的文件操作"""

    def setUp(self):
        """每个测试前的设置"""
        # 创建临时目录
        self.test_dir = tempfile.mkdtemp()
        编译器实例 = Cpp编译器(优化级别='O2')
        self.manager = 编译管理器(self.test_dir, 编译器实例)

    def tearDown(self):
        """每个测试后的清理"""
        # 删除临时目录
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_写入和读取文件(self):
        """测试写入和读取文件"""
        content = "Hello, World!"
        self.manager.写入文件("test.txt", content)

        result = self.manager.读取文件("test.txt")
        self.assertEqual(result, content)

    def test_读取不存在的文件(self):
        """测试读取不存在的文件"""
        result = self.manager.读取文件("nonexistent.txt")
        self.assertIsNone(result)

    def test_文件是否存在(self):
        """测试检查文件是否存在"""
        self.assertFalse(self.manager.文件是否存在("test.txt"))

        self.manager.写入文件("test.txt", "content")
        self.assertTrue(self.manager.文件是否存在("test.txt"))

    def test_文件是否可读(self):
        """测试检查文件是否可读"""
        self.assertFalse(self.manager.文件是否可读("test.txt"))

        self.manager.写入文件("test.txt", "content")
        self.assertTrue(self.manager.文件是否可读("test.txt"))

    def test_获取文件大小(self):
        """测试获取文件大小"""
        self.manager.写入文件("test.txt", "Hello")
        size = self.manager.获取文件大小("test.txt")
        self.assertEqual(size, 5)  # "Hello" 是 5 个字节

    def test_获取不存在文件的大小(self):
        """测试获取不存在文件的大小"""
        size = self.manager.获取文件大小("nonexistent.txt")
        self.assertEqual(size, 0)

    def test_获取文件修改时间(self):
        """测试获取文件修改时间"""
        self.manager.写入文件("test.txt", "content")
        mtime = self.manager.获取文件修改时间("test.txt")
        self.assertGreater(mtime, 0)

    def test_获取不存在文件的修改时间(self):
        """测试获取不存在文件的修改时间"""
        mtime = self.manager.获取文件修改时间("nonexistent.txt")
        self.assertEqual(mtime, 0)


class Test文件管理器清理操作(unittest.TestCase):
    """测试文件管理器的清理操作"""

    def setUp(self):
        """每个测试前的设置"""
        # 创建临时目录
        self.test_dir = tempfile.mkdtemp()
        编译器实例 = Cpp编译器(优化级别='O2')
        self.manager = 编译管理器(self.test_dir, 编译器实例)

    def tearDown(self):
        """每个测试后的清理"""
        # 删除临时目录
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_清理临时文件(self):
        """测试清理临时文件"""
        base_name = "test_func"
        # 创建临时文件
        open(f"{self.test_dir}/{base_name}.o", 'w').close()
        open(f"{self.test_dir}/{base_name}.tmp", 'w').close()
        open(f"{self.test_dir}/{base_name}.bak", 'w').close()
        # 创建不应该被删除的文件
        self.manager.写入文件("test.cpp", "content")

        self.manager.清理临时文件(base_name)

        # 验证临时文件被删除
        self.assertFalse(os.path.exists(f"{self.test_dir}/{base_name}.o"))
        self.assertFalse(os.path.exists(f"{self.test_dir}/{base_name}.tmp"))
        self.assertFalse(os.path.exists(f"{self.test_dir}/{base_name}.bak"))
        # 验证其他文件仍然存在
        self.assertTrue(self.manager.文件是否存在("test.cpp"))

    def test_清理编译文件(self):
        """测试清理编译文件"""
        # 创建一些文件
        self.manager.写入文件("test1.so", "content1")
        self.manager.写入文件("test2.h", "content2")
        self.manager.写入文件("test3.cpp", "content3")

        # 清理指定文件
        self.manager.清理编译文件(["test1.so", "test2.h"])

        # 验证文件被删除
        self.assertFalse(self.manager.文件是否存在("test1.so"))
        self.assertFalse(self.manager.文件是否存在("test2.h"))
        # 验证未指定的文件仍然存在
        self.assertTrue(self.manager.文件是否存在("test3.cpp"))

    def test_清理旧文件(self):
        """测试清理旧文件"""
        # 创建一些文件
        self.manager.写入文件("prefix_file1.txt", "content1")
        self.manager.写入文件("prefix_file2.txt", "content2")
        self.manager.写入文件("other_file.txt", "content3")

        self.manager.清理旧文件("prefix_")

        # 验证前缀匹配的文件被删除
        self.assertFalse(self.manager.文件是否存在("prefix_file1.txt"))
        self.assertFalse(self.manager.文件是否存在("prefix_file2.txt"))
        # 验证其他文件仍然存在
        self.assertTrue(self.manager.文件是否存在("other_file.txt"))

    def test_清理所有缓存(self):
        """测试清理所有缓存"""
        # 创建各种类型的缓存文件
        self.manager.写入文件("test.so", "")
        self.manager.写入文件("test.o", "")
        self.manager.写入文件("test.tmp", "")
        self.manager.写入文件("test.cpp", "")

        # 清理所有缓存（包括 .cpp）
        count = self.manager.清理所有缓存()

        # 所有文件都应该被删除
        self.assertFalse(self.manager.文件是否存在("test.so"))
        self.assertFalse(self.manager.文件是否存在("test.o"))
        self.assertFalse(self.manager.文件是否存在("test.tmp"))
        self.assertFalse(self.manager.文件是否存在("test.cpp"))

        # count 应该等于 4（删除了4个文件）
        self.assertEqual(count, 4)


class Test文件管理器列出文件(unittest.TestCase):
    """测试文件管理器列出文件"""

    def setUp(self):
        """每个测试前的设置"""
        # 创建临时目录
        self.test_dir = tempfile.mkdtemp()
        编译器实例 = Cpp编译器(优化级别='O2')
        self.manager = 编译管理器(self.test_dir, 编译器实例)

    def tearDown(self):
        """每个测试后的清理"""
        # 删除临时目录
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_列出所有文件(self):
        """测试列出所有文件"""
        self.manager.写入文件("test1.cpp", "content1")
        self.manager.写入文件("test2.cpp", "content2")
        self.manager.写入文件("test.h", "content3")

        files = self.manager.列出文件()
        self.assertEqual(len(files), 3)

    def test_列出指定模式的文件(self):
        """测试列出指定模式的文件"""
        self.manager.写入文件("test1.cpp", "content1")
        self.manager.写入文件("test2.cpp", "content2")
        self.manager.写入文件("test.h", "content3")

        cpp_files = self.manager.列出文件("*.cpp")
        self.assertEqual(len(cpp_files), 2)

        h_files = self.manager.列出文件("*.h")
        self.assertEqual(len(h_files), 1)

    def test_列出不存在目录的文件(self):
        """测试列出不存在目录的文件"""
        编译器实例 = Cpp编译器(优化级别='O2')
        manager = 编译管理器("/nonexistent/directory", 编译器实例)
        files = manager.列出文件()
        self.assertEqual(len(files), 0)


class Test文件管理器状态摘要(unittest.TestCase):
    """测试文件管理器的状态摘要"""

    def setUp(self):
        """每个测试前的设置"""
        # 创建临时目录
        self.test_dir = tempfile.mkdtemp()
        编译器实例 = Cpp编译器(优化级别='O2')
        self.manager = 编译管理器(self.test_dir, 编译器实例)

    def tearDown(self):
        """每个测试后的清理"""
        # 删除临时目录
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_获取状态摘要_空目录(self):
        """测试获取空目录的状态摘要"""
        summary = self.manager.获取状态摘要()

        self.assertEqual(summary["工作目录"], self.test_dir)
        self.assertTrue(summary["目录是否存在"])
        self.assertIn("文件统计", summary)
        self.assertEqual(summary["文件统计"]["cpp文件"], 0)
        self.assertEqual(summary["文件统计"]["头文件"], 0)

    def test_获取状态摘要_有文件(self):
        """测试获取有文件目录的状态摘要"""
        self.manager.写入文件("test.cpp", "content")
        self.manager.写入文件("test.h", "content")
        self.manager.写入文件("test.o", "content")

        summary = self.manager.获取状态摘要()

        self.assertEqual(summary["文件统计"]["cpp文件"], 1)
        self.assertEqual(summary["文件统计"]["头文件"], 1)
        self.assertEqual(summary["文件统计"]["对象文件"], 1)


if __name__ == '__main__':
    unittest.main()