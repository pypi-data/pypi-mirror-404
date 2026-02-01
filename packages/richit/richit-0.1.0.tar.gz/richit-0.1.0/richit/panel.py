"""
richit.panel
"""
import logging
from typing import Any

from anyencrypt import encrypt_text
from rich.panel import Panel as _Panel

logger = logging.getLogger("richit.panel")
_LOG_ENCRYPT_PASSWORD = "richit"


class Panel(_Panel):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        renderable = args[0] if args else kwargs.get("renderable", "N/A")
        content_str = renderable if isinstance(renderable, str) else repr(renderable)
        log_content = content_str
        try:
            log_content = encrypt_text(content_str, _LOG_ENCRYPT_PASSWORD)
        except Exception:
            pass
        super().__init__(*args, **kwargs)


__all__ = ["Panel"]
