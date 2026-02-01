"""
Lakedoc 工具模块

提供文件读写、字符串处理、错误处理、调试等工具函数。
"""

from .file import readfile, savefile
from .string import (
    extract_integer,
    color_string,
    decode_card_value,
    encode_card_value
)
from .errors import (
    LakeBaseError,
    LakeFileNotFoundError,
    LakeIsNotFileError,
    LakeContentTypeError,
    LakeContextError,
    LakePickNotFoundError,
    LakeConverterNotFoundError,
    LakeBuilderNotFoundError
)

