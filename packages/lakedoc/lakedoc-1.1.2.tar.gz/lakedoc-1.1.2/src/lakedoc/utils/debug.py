"""
Lakedoc 全局调试模块

提供全局调试功能，支持启用/禁用调试模式和输出调试信息。
"""

from colorama import Fore, Style
from threading import Lock

# 全局调试状态
_debug_enabled = False
_debug_lock = Lock()


def enable_debug():
    """
    启用全局调试模式
    """
    global _debug_enabled
    with _debug_lock:
        _debug_enabled = True


def disable_debug():
    """
    禁用全局调试模式
    """
    global _debug_enabled
    with _debug_lock:
        _debug_enabled = False


def is_debug_enabled() -> bool:
    """
    检查调试模式是否启用

    :return: 调试模式是否启用
    """
    with _debug_lock:
        return _debug_enabled


def debug(message: str, level: int = 0, color: str = "cyan"):
    """
    输出调试信息

    :param message: 调试信息内容
    :param level: 缩进级别，用于显示层级关系
    :param color: 终端输出颜色，默认 cyan
    """
    if not is_debug_enabled():
        return

    indent = "  " * level
    prefix = f"{Fore.CYAN}[DEBUG]{Style.RESET_ALL}"
    color_code = getattr(Fore, color.upper(), Fore.CYAN)
    print(f"{prefix} {indent}{color_code}{message}{Style.RESET_ALL}")


def debug_section(title: str, level: int = 0):
    """
    打印调试章节标题

    :param title: 章节标题
    :param level: 缩进级别
    """
    if not is_debug_enabled():
        return

    indent = "  " * level
    separator = "=" * 50
    print(f"\n{Fore.YELLOW}{indent}{separator}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{indent}{title}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{indent}{separator}{Style.RESET_ALL}\n")


def debug_subsection(title: str, level: int = 0):
    """
    打印调试子章节标题

    :param title: 子章节标题
    :param level: 缩进级别
    """
    if not is_debug_enabled():
        return

    indent = "  " * level
    print(f"{Fore.GREEN}{indent}--- {title} ---{Style.RESET_ALL}")
