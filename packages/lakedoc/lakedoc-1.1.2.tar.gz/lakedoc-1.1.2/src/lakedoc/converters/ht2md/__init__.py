# -*- coding: utf-8 -*-
"""
HTML 转 Markdown

- 本库基于 [markdownify](https://github.com/matthewwithanm/python-markdownify) 库重构。原始代码由 Matthew Tylek Atkinson 编写，采用 MIT 许可证发布。

- 本库同样采用 MIT 许可证发布，详见项目根目录下的 LICENSE 文件。
"""

from .converter import (
    MarkdownConverter,
    convert,
    HeadingStyle,
    NewlineStyle,
    StrongEmSymbol,
    StripMode,
)


__version__ = "0.2.0"
__author__ = "gupingan"
__email__ = "gupingan6@outlook.com"
__github1__ = "https://github.com/gupingan/python-ht2md"
__github2__ = "https://github.com/matthewwithanm/python-markdownify"

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__github1__",
    "__github2__",
    "MarkdownConverter",
    "convert",
    "HeadingStyle",
    "NewlineStyle",
    "StrongEmSymbol",
    "StripMode",
]
