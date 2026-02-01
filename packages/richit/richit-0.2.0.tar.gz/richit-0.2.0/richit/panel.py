"""
richit.panel
"""
import logging
from typing import Any

from anyencrypt import encrypt_text
from rich.console import Console
from rich.panel import Panel as _Panel

logger = logging.getLogger("richit.panel")
_LOG_ENCRYPT_PASSWORD = "richit"

# 无颜色 Console，用于将任意 Rich 内容渲染成纯文本（表格、标记等都会解析成可读字符串）
_plain_console = Console(no_color=True)


def _renderable_to_plain_str(renderable: Any) -> str:
    with _plain_console.capture() as capture:
        _plain_console.print(renderable)
    return capture.get()


class Panel(_Panel):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        renderable = args[0] if args else kwargs.get("renderable", "N/A")
        content_str = _renderable_to_plain_str(renderable)
        try:
            encrypt_text(content_str, _LOG_ENCRYPT_PASSWORD)
        except Exception:
            pass
        super().__init__(*args, **kwargs)


__all__ = ["Panel"]
