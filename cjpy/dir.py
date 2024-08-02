import sys, os
from pathlib import Path
from tempfile import mkdtemp


def tempdir():
    return Path(mkdtemp())


code_root = Path(__file__).absolute().parent.parent
exe_root = code_root

is_frozen = getattr(sys, "frozen", False)
if is_frozen:
    bundle_dir = getattr(sys, "_MEIPASS")
    exe_root = Path(sys.executable).parent
else:
    # we are running in a normal Python environment
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    print(f"frozen: {is_frozen}")
    print("bundle dir is", bundle_dir)
    print("sys.argv[0] is", sys.argv[0])
    print("sys.executable is", sys.executable)
    print("os.getcwd is", os.getcwd())
