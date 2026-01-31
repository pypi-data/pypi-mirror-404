import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).parent.parent))
import l0n0lc as lc
import subprocess

@lc.映射类型('int')
class int32_t:
    def __init__(self, v) -> None:
        pass


@lc.映射类型('char**')
class charpp:
    def __getitem__(self, key):
        pass


编译为可执行文件文件名 = '测试可执行文件'


@lc.即时编译(总是重编=True, 可执行文件名=编译为可执行文件文件名)
def 可执行(argc: int32_t, argv: charpp) -> int32_t:
    for i in range(argc):  # type: ignore
        print(argv[i])
    print('Hello World')
    return int32_t(0)


subprocess.run([f'l0n0lcoutput/{编译为可执行文件文件名}', '参数1', '参数2'])
