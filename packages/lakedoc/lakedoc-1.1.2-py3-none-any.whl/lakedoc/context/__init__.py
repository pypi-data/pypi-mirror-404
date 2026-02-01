"""
Lakedoc 上下文模块

提供上下文管理和转换器注册功能。
"""

from .base import LakeBaseContext
from .lake import LakeContext
from .mod import convert, get_context, set_context
