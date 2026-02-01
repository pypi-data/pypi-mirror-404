"""
Lakedoc 外部接口模块

提供统一的 convert 接口，支持通过 options 配置不同的转换行为。
"""

from os import PathLike
from typing import Callable, List, Optional, Set, Union
from pathlib import Path

from bs4 import Tag

from lakedoc.converters.ht2md.converter import (
    HeadingStyle,
    NewlineStyle,
    StripMode,
    StrongEmSymbol,
)
from .lake import LakeContext
from ..utils import errors

_context: Optional[LakeContext] = None


def get_context() -> LakeContext:
    global _context
    if _context is None:
        _context = LakeContext()
    return _context


def set_context(context_: Optional[LakeContext]):
    global _context
    _context = context_


def register(converter: str, converter_class, is_cover: bool = True):
    ctx = get_context() # pragma: no cover
    ctx.register(converter, converter_class, is_cover) # pragma: no cover


def convert(
    source: str,
    *,
    saveto: Optional[Union[str, Path, PathLike]] = None,
    converter: str = "markdown",
    encoding: str = "utf-8",
    **options
):
    ctx = get_context()
    ctx.set_options(**options)

    source_str = str(source) if not isinstance(source, str) else source
    if not source_str.strip():
        raise errors.LakeSourceEmptyError
    is_html_content = "<!doctype lake>" in source_str.lower()

    if is_html_content:
        # HTML 内容
        if saveto:
            return ctx.convert_content_save(source_str, saveto, converter, encoding)
        else:
            return ctx.convert_content(source_str, converter)
    else:
        # 文件路径
        if saveto:
            return ctx.convert_file_save(source_str, saveto, converter, encoding)
        else:
            return ctx.convert_file(source_str, converter, encoding)
