import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).parent.parent))

from l0n0lc.即时编译 import jit

@jit(总是重编=True)
def test_exception(n: int):
    try:
        if n < 0:
            raise Exception("Negative number")
        print("Number is positive or zero")
    except Exception as e:
        print("Caught exception")
        # Note: e.what() is C++ specific, but we might just print a fixed message for now
        # because mapping 'e' to Python object in print might be tricky if not fully implemented.
        # But let's see if we can print the message if we mapped it to runtime_error
    
    print("Function finished")

if __name__ == "__main__":
    print("Testing exception handling...")
    test_exception(10)
    test_exception(-1)
