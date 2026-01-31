import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).parent.parent))

from l0n0lc.即时编译 import 即时编译
import unittest

class TestStringOps(unittest.TestCase):
    def test_length(self):
        @即时编译(总是重编=True)
        def get_len(s:bytes) -> int:
            a = str(s) + '123'
            print("a =", a)
            return len(a)
        self.assertEqual(get_len(b'123'), 6)

if __name__ == '__main__':
    unittest.main()
