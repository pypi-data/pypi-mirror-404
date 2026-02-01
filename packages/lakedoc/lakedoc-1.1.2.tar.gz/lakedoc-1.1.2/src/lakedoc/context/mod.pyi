from os import PathLike
from typing import Any, Callable, List, Optional, Set, Union
from pathlib import Path

from bs4 import Tag

from lakedoc.converters.ht2md.converter import (
    HeadingStyle,
    NewlineStyle,
    StripMode,
    StrongEmSymbol,
)
from .lake import LakeContext

# 全局上下文实例
_context: Optional[LakeContext] = None

def get_context() -> LakeContext:
    """获取当前上下文，如果不存在则创建默认上下文"""

def set_context(context_: Optional[LakeContext]):
    """设置当前的上下文内容"""

def register(converter: str, converter_class, is_cover: bool = True):
    """
    注册转换器到当前上下文

    :param converter: 转换器名称
    :param converter_class: 转换器类
    :param is_cover: 是否覆盖已存在的转换器
    """

def convert(
    source: str,
    *,
    saveto: Optional[Union[str, Path, PathLike]] = ...,
    converter: str = ...,
    encoding: str = ...,
    title: Optional[str] = ...,
    bs4_builder: str = "...",
    remove_tags: Set[str] = ...,
    diagram_as_code: bool = ...,
    diagram_as_code_cond: Optional[Callable[[str, str, str],bool]] = ...,
    autolinks: bool = ...,
    bullets: str = ...,
    code_language: str = ...,
    code_language_callback: Optional[Callable[[Tag], Optional[str]]] = ...,
    convert: Optional[List[str]] = ...,
    default_title: bool = ...,
    escape_asterisks: bool = ...,
    escape_underscores: bool = ...,
    escape_misc: bool = ...,
    heading_style: HeadingStyle = ...,
    keep_inline_images_in: Optional[List[str]] = ...,
    newline_style: NewlineStyle = ...,
    strip: Optional[List[str]] = ...,
    strip_document: Optional[StripMode] = ...,
    strip_pre: Optional[StripMode] = ...,
    strong_em_symbol: StrongEmSymbol = ...,
    sub_symbol: str = ...,
    sup_symbol: str = ...,
    table_infer_header: bool = ...,
    wrap: bool = ...,
    wrap_width: int = ...,
) -> Any:
    """
    将 Lake 文档转换为指定格式，返回转换后的字符串内容

    :param source: 输入源，可以是 HTML 内容字符串或文件路径，如果包含 `<!doctype lake>`，则视为 HTML 内容，否则视为文件路径
    :param saveto: 保存路径（可选，不提供则返回转换结果）
    :param converter: 转换器类型，默认 'markdown'
    :param encoding: 文件编码，默认 'utf-8'
    :param title: 转换后文档首行的标题（可选）
    :param bs4_builder: BeautifulSoup HTML 解析器，默认 'html.parser'
    :param remove_tags: 需要从源文件中删除的标签集合，默认 {'meta', 'link', 'script', 'style'}
    :param diagram_as_code: 是否将 diagram 转换为代码块格式，默认 False
    :param diagram_as_code_cond: 指定需要转换为代码块的回调条件函数，参数是 (src, lang, code)
    :param autolinks: 是否自动将 URL 转换为自动链接格式
    :param bullets: 无序列表的标记字符序列
    :param code_language: 代码块的语言标识符
    :param code_language_callback: 代码块语言回调函数
    :param convert: 要转换的标签列表（与 strip 互斥）
    :param default_title: 是否为没有标题的链接使用 URL 作为默认标题
    :param escape_asterisks: 是否转义星号
    :param escape_underscores: 是否转义下划线
    :param escape_misc: 是否转义其他特殊字符
    :param heading_style: 标题样式（HeadingStyle枚举）：ATX / ATX_CLOSED / UNDERLINED / SETEXT
    :param keep_inline_images_in: 保持内联图片的父标签列表
    :param newline_style: 换行样式（NewLineStyle枚举）：SPACES / BACKSLASH
    :param strip: 要移除的标签列表（与 convert 互斥）
    :param strip_document: 文档空白处理方式（StripMode枚举）：LSTRIP / RSTRIP / STRIP / STRIP_ONE
    :param strip_pre: pre 标签空白处理方式（StripMode枚举）：LSTRIP / RSTRIP / STRIP / STRIP_ONE
    :param strong_em_symbol: 粗体和斜体符号（StrongEmSymbol枚举）：ASTERISK / UNDERSCORE
    :param sub_symbol: 下标符号，默认为 '~'
    :param sup_symbol: 上标符号，默认为 '^'
    :param table_infer_header: 是否推断表格标题行
    :param wrap: 是否自动换行
    :param wrap_width: 换行宽度
    """
