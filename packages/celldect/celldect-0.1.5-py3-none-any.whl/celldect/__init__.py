import sys
import os
import importlib.util

# 1. 定义基础模块名
_MODULE_BASE_NAMES = ['celldect20', 'celldect30']

# 2. 建立平台到实际文件名的精确映射
if sys.platform.startswith('win32'):
    _FILE_MAP = {
        'celldect20': 'celldect20.cp310-win_amd64.pyd',
        'celldect30': 'celldect30.cp310-win_amd64.pyd'
    }
elif sys.platform.startswith('linux'):
    _FILE_MAP = {
        'celldect20': 'celldect20.cpython-310-x86_64-linux-gnu.so',
        'celldect30': 'celldect30.cpython-310-x86_64-linux-gnu.so'
    }
else:
    raise OSError(f"Unsupported platform: {sys.platform}")

# 3. 预先声明变量为None，解决静态检查报错
celldect20 = None
celldect30 = None

# 4. 动态加载每个模块
for _base_name in _MODULE_BASE_NAMES:
    _actual_filename = _FILE_MAP[_base_name]
    # 修正：使用 os.path 正确构建兄弟文件的路径
    _dir_of_this_file = os.path.dirname(os.path.abspath(__file__))
    _file_path = os.path.join(_dir_of_this_file, _actual_filename)

    # 检查文件是否存在（友好的错误提示）
    if not os.path.exists(_file_path):
        # 这通常意味着.pyd/.so文件没有被正确打包或安装
        raise FileNotFoundError(
            f"Compiled extension module '{_actual_filename}' not found at: {_file_path}\n"
            f"This usually means the package was not installed correctly. "
            f"Ensure the binary files are included in the wheel."
        )

    _spec = importlib.util.spec_from_file_location(_base_name, _file_path)
    _module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_module)

    # 将加载的模块赋值给预声明的变量
    globals()[_base_name] = _module

# 5. 清理内部变量（可选）
del sys, os, importlib, _MODULE_BASE_NAMES, _FILE_MAP
del _base_name, _actual_filename, _dir_of_this_file, _file_path, _spec, _module

# 6. 定义 __all__
__all__ = ['celldect20', 'celldect30']