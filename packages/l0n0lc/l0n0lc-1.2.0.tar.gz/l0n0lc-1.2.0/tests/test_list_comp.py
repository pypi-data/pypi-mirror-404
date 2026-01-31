import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).parent.parent))


from l0n0lc.即时编译 import jit

@jit(总是重编=True)
def test_list_comp() -> int:
    # Test simple list comp from vector
    data = [1, 2, 3, 4, 5]
    res = [x * 2 for x in data]
    
    print("Element 0:", res[0]) # Should be 2
    print("Element 4:", res[4]) # Should be 10

    # Test filter
    # [1, 2, 3, 4, 5]
    res2 = [x for x in data if x % 2 == 0]
    # Should be [2, 4]
    
    # We can't use len() in C++ easily unless we implemented len support for vector?
    # Py转Cpp转译器.py check len support?
    # If not supported, we can just check elements.
    # But std_vector.py doesn't implement len()?
    # Python built-in 'len' support in C++:
    # If len(x) is called.
    # We should support it if we want robustness.
    # But for now, assume we check via print or logic.
    
    if res2[0] == 2:
        print("Filter test part 1 passed")
    if res2[1] == 4:
        print("Filter test part 2 passed")

    return 0

if __name__ == "__main__":
    print("Testing List Comp...")
    test_list_comp()
