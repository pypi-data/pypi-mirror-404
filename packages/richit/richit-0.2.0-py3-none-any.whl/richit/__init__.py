"""
Richit - 终端富文本与美化的 Python 库，提供与常用终端库一致的接口。
"""

import importlib.abc
import importlib.machinery
import sys
from typing import TYPE_CHECKING, Any

# 顶层 API 委托给后端库
from rich import (
    get_console,
    reconfigure,
    print,
    inspect,
    print_json,
)

__version__ = "0.1.0"
__all__ = ["get_console", "reconfigure", "print", "inspect", "print_json"]

if TYPE_CHECKING:
    from rich.console import Console

# 子模块缓存：richit.console 等指向后端同名子模块
_submodule_cache: dict[str, Any] = {}


def __getattr__(name: str) -> Any:
    """将 richit.xxx 子模块访问委托给后端同名子模块。"""
    if name in _submodule_cache:
        return _submodule_cache[name]
    try:
        import importlib
        mod = importlib.import_module(f"rich.{name}")
        _submodule_cache[name] = mod
        this_module = sys.modules[__name__]
        setattr(this_module, name, mod)
        return mod
    except ModuleNotFoundError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None


class _RichitFinder(importlib.abc.MetaPathFinder):
    """将 richit.xxx 的导入委托给后端同名子模块，使 from richit.console import Console 等可用。"""

    def find_spec(self, fullname: str, path: object, target: object = None):
        if fullname == "richit" or not fullname.startswith("richit."):
            return None
        subname = fullname.split(".", 1)[1]
        # 只处理第一级子模块；不重定向 __main__，保留本包自己的入口
        # panel 使用本包重写的 richit/panel.py，不委托给 rich.panel
        if "." in subname or subname == "__main__" or subname == "panel":
            return None
        try:
            backend = __import__(f"rich.{subname}", fromlist=["__name__"])
        except ModuleNotFoundError:
            return None
        loader = _RichitLoader(backend)
        return importlib.machinery.ModuleSpec(fullname, loader, origin=backend.__spec__.origin)


class _RichitLoader(importlib.abc.Loader):
    """加载器：richit.xxx 在 sys.modules 中复用后端同名子模块。"""

    def __init__(self, backend: Any) -> None:
        self._backend = backend

    def create_module(self, spec: object) -> Any:
        return self._backend

    def exec_module(self, module: object) -> None:
        pass


# 注册导入钩子，使 from richit.console import Console 等能正确解析
if _RichitFinder not in sys.meta_path:
    sys.meta_path.insert(0, _RichitFinder())
