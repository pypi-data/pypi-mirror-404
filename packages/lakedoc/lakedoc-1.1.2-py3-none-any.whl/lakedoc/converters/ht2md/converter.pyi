# -*- coding: utf-8 -*-
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union
from bs4.element import Tag


class HeadingStyle(Enum):
    """标题样式"""
    ATX = "atx"
    ATX_CLOSED = "atx_closed"
    UNDERLINED = "underlined"
    SETEXT = UNDERLINED


class NewlineStyle(Enum):
    """换行样式"""
    SPACES = "spaces"
    BACKSLASH = "backslash"


class StrongEmSymbol(Enum):
    """粗体和斜体样式"""
    ASTERISK = "*"
    UNDERSCORE = "_"


class StripMode(Enum):
    """文档/pre 去除样式"""
    LSTRIP = "lstrip"
    RSTRIP = "rstrip"
    STRIP = "strip"
    STRIP_ONE = "strip_one"


@dataclass
class Options:
    """转换选项。"""
    #: 是否自动将 URL 转换为自动链接格式
    autolinks: bool = True
    #: 传递给 BeautifulSoup 的解析器选项
    bs4_options: Union[str, List[str], Dict[str, Any]] = "html.parser"
    #: 无序列表的标记字符序列
    bullets: str = "*+-"
    #: 代码块的语言标识符
    code_language: str = ""
    #: 代码块语言回调函数
    code_language_callback: Optional[Callable[[Tag], Optional[str]]] = None
    #: 要转换的标签列表（与 strip 互斥）
    convert: Optional[List[str]] = None
    #: 是否为没有标题的链接使用 URL 作为默认标题
    default_title: bool = False
    #: 是否转义星号
    escape_asterisks: bool = True
    #: 是否转义下划线
    escape_underscores: bool = True
    #: 是否转义其他特殊字符
    escape_misc: bool = False
    #: 标题样式：'atx'、'atx_closed' 或 'underlined'
    heading_style: HeadingStyle = HeadingStyle.UNDERLINED
    #: 保持内联图片的父标签列表
    keep_inline_images_in: List[str] = ...
    #: 换行样式：'spaces' 或 'backslash'
    newline_style: NewlineStyle = NewlineStyle.SPACES
    #: 要移除的标签列表（与 convert 互斥）
    strip: Optional[List[str]] = None
    #: 文档空白处理方式
    strip_document: Optional[StripMode] = StripMode.STRIP
    #: pre 标签空白处理方式
    strip_pre: Optional[StripMode] = StripMode.STRIP
    #: 粗体和斜体符号：'*' 或 '_'
    strong_em_symbol: StrongEmSymbol = StrongEmSymbol.ASTERISK
    #: 下标符号
    sub_symbol: str = "~"
    #: 上标符号
    sup_symbol: str = "^"
    #: 是否推断表格标题行
    table_infer_header: bool = False
    #: 是否自动换行
    wrap: bool = False
    #: 换行宽度
    wrap_width: int = 80


class MarkdownConverter:
    """HTML 转 Markdown 转换器"""

    def __init__(
        self,
        autolinks: bool = True,
        bs4_options: Union[str, List[str], Dict[str, Any]] = "html.parser",
        bullets: str = "*+-",
        code_language: str = "",
        code_language_callback: Optional[Callable[[Tag], Optional[str]]] = None,
        convert: Optional[List[str]] = None,
        default_title: bool = False,
        escape_asterisks: bool = True,
        escape_underscores: bool = True,
        escape_misc: bool = False,
        heading_style: HeadingStyle = HeadingStyle.UNDERLINED,
        keep_inline_images_in: List[str] = ...,
        newline_style: NewlineStyle = NewlineStyle.SPACES,
        strip: Optional[List[str]] = None,
        strip_document: Optional[StripMode] = StripMode.STRIP,
        strip_pre: Optional[StripMode] = StripMode.STRIP,
        strong_em_symbol: StrongEmSymbol = StrongEmSymbol.ASTERISK,
        sub_symbol: str = "~",
        sup_symbol: str = "^",
        table_infer_header: bool = False,
        wrap: bool = False,
        wrap_width: int = 80,
    ) -> None:
        """
        初始化转换器。

        Args:
            autolinks: 是否自动将 URL 转换为自动链接格式
            bs4_options: 传递给 BeautifulSoup 的解析器选项
            bullets: 无序列表的标记字符序列
            code_language: 代码块的语言标识符
            code_language_callback: 代码块语言回调函数
            convert: 要转换的标签列表（与 strip 互斥）
            default_title: 是否为没有标题的链接使用 URL 作为默认标题
            escape_asterisks: 是否转义星号
            escape_underscores: 是否转义下划线
            escape_misc: 是否转义其他特殊字符
            heading_style: 标题样式：'atx'、'atx_closed' 或 'underlined'
            keep_inline_images_in: 保持内联图片的父标签列表
            newline_style: 换行样式：'spaces' 或 'backslash'
            strip: 要移除的标签列表（与 convert 互斥）
            strip_document: 文档空白处理方式
            strip_pre: pre 标签空白处理方式
            strong_em_symbol: 粗体和斜体符号：'*' 或 '_'
            sub_symbol: 下标符号，默认为 '~'
            sup_symbol: 上标符号，默认为 '^'
            table_infer_header: 是否推断表格标题行
            wrap: 是否自动换行
            wrap_width: 换行宽度
        """

    def convert(self, html: str) -> str:
        """
        将 HTML 字符串转换为 Markdown。

        Args:
            html: HTML 字符串

        Returns:
            Markdown 字符串
        """

    def convert_soup(self, soup: Any) -> str:
        """
        将 BeautifulSoup 对象转换为 Markdown。

        Args:
            soup: BeautifulSoup 对象

        Returns:
            Markdown 字符串
        """

    def process_element(self, node: Any, parent_tags: Optional[Set[str]] = None) -> str:
        """
        处理元素节点。

        Args:
            node: 要处理的节点
            parent_tags: 父标签集合

        Returns:
            处理后的字符串
        """

    def process_tag(self, node: Any, parent_tags: Optional[Set[str]] = None) -> str:
        """
        处理标签节点。

        Args:
            node: 要处理的标签节点
            parent_tags: 父标签集合

        Returns:
            处理后的字符串
        """

    def convert__document_(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """
        BeautifulSoup 对象的最终文档级格式化。

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            格式化后的字符串
        """

    def process_text(self, el: Any, parent_tags: Optional[Set[str]] = None) -> str:
        """
        处理文本节点。

        Args:
            el: 文本节点
            parent_tags: 父标签集合

        Returns:
            处理后的字符串
        """

    def get_conv_fn_cached(self, tag_name: str) -> Optional[Callable]:
        """
        给定标签名称，使用缓存返回转换函数。

        Args:
            tag_name: 标签名称

        Returns:
            转换函数
        """

    def get_conv_fn(self, tag_name: str) -> Optional[Callable]:
        """
        给定标签名称，查找并返回转换函数。

        Args:
            tag_name: 标签名称

        Returns:
            转换函数
        """

    def should_convert_tag(self, tag: str) -> bool:
        """
        给定标签名称，根据 strip/convert 选项返回是否转换。

        Args:
            tag: 标签名称

        Returns:
            是否转换该标签
        """

    def escape(self, text: str, parent_tags: Set[str]) -> str:
        """
        转义 Markdown 特殊字符。

        Args:
            text: 要转义的文本
            parent_tags: 父标签集合

        Returns:
            转义后的文本
        """

    def underline(self, text: str, pad_char: str) -> str:
        """
        使用下划线格式化文本。

        Args:
            text: 文本
            pad_char: 填充字符

        Returns:
            格式化后的字符串
        """

    def convert_a(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <a> 标签。"""

    def convert_blockquote(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <blockquote> 标签。"""

    def convert_br(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <br> 标签。"""

    def convert_code(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <code> 标签。"""

    def convert_del(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <del> 标签。"""

    def convert_div(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <div> 标签。"""

    def convert_article(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <article> 标签。"""

    def convert_section(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <section> 标签。"""

    def convert_header(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <header> 标签。"""

    def convert_footer(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <footer> 标签。"""

    def convert_nav(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <nav> 标签。"""

    def convert_main(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <main> 标签。"""

    def convert_aside(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <aside> 标签。"""

    def convert_em(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <em> 标签。"""

    def convert_kbd(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <kbd> 标签。"""

    def convert_dd(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <dd> 标签（定义列表描述）。"""

    def convert_dl(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <dl> 标签（定义列表）。"""

    def convert_dt(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <dt> 标签（定义列表术语）。"""

    def convert_hN(self, n: int, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <hN> 标签。"""

    def convert_hr(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <hr> 标签。"""

    def convert_i(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <i> 标签。"""

    def convert_img(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <img> 标签。"""

    def convert_video(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <video> 标签。"""

    def convert_audio(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <audio> 标签。"""

    def convert_list(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换列表标签。"""

    def convert_ul(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <ul> 标签。"""

    def convert_ol(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <ol> 标签。"""

    def convert_li(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <li> 标签。"""

    def convert_p(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <p> 标签。"""

    def convert_pre(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <pre> 标签。"""

    def convert_q(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <q> 标签（行内引用）。"""

    def convert_script(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <script> 标签（忽略脚本内容）。"""

    def convert_style(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <style> 标签（忽略样式内容）。"""

    def convert_s(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <s> 标签。"""

    def convert_strong(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <strong> 标签。"""

    def convert_samp(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <samp> 标签。"""

    def convert_sub(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <sub> 标签。"""

    def convert_sup(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <sup> 标签。"""

    def convert_table(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <table> 标签。"""

    def convert_caption(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <caption> 标签。"""

    def convert_figcaption(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <figcaption> 标签。"""

    def convert_figure(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <figure> 标签。"""

    def convert_td(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <td> 标签。"""

    def convert_th(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <th> 标签。"""

    def convert_tr(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <tr> 标签。"""

    def convert_mark(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <mark> 标签（高亮文本）。"""

    def convert_abbr(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <abbr> 标签（缩写）。"""

    def convert_time(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <time> 标签。"""

    def convert_address(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <address> 标签。"""

    def convert_details(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <details> 标签（可折叠详情）。"""

    def convert_summary(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <summary> 标签（详情摘要）。"""

    def convert_progress(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <progress> 标签（进度条）。"""

    def convert_meter(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <meter> 标签（度量衡）。"""

    def convert_data(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <data> 标签（机器可读数据）。"""

    def convert_output(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <output> 标签（输出结果）。"""

    def convert_noscript(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <noscript> 标签。"""

    def convert_template(self, el: Any, text: str, parent_tags: Set[str]) -> str:
        """转换 <template> 标签（忽略模板内容）。"""


def convert(
    html: str,
    autolinks: bool = True,
    bs4_options: Union[str, List[str], Dict[str, Any]] = "html.parser",
    bullets: str = "*+-",
    code_language: str = "",
    code_language_callback: Optional[Callable[[Tag], Optional[str]]] = None,
    convert: Optional[List[str]] = None,
    default_title: bool = False,
    escape_asterisks: bool = True,
    escape_underscores: bool = True,
    escape_misc: bool = False,
    heading_style: HeadingStyle = HeadingStyle.UNDERLINED,
    keep_inline_images_in: List[str] = ...,
    newline_style: NewlineStyle = NewlineStyle.SPACES,
    strip: Optional[List[str]] = None,
    strip_document: Optional[StripMode] = StripMode.STRIP,
    strip_pre: Optional[StripMode] = StripMode.STRIP,
    strong_em_symbol: StrongEmSymbol = StrongEmSymbol.ASTERISK,
    sub_symbol: str = "~",
    sup_symbol: str = "^",
    table_infer_header: bool = False,
    wrap: bool = False,
    wrap_width: int = 80,
) -> str:
    """
    将 HTML 转换为 Markdown

    Args:
        html: HTML 字符串
        autolinks: 是否自动将 URL 转换为自动链接格式
        bs4_options: 传递给 BeautifulSoup 的解析器选项
        bullets: 无序列表的标记字符序列
        code_language: 代码块的语言标识符
        code_language_callback: 代码块语言回调函数
        convert: 要转换的标签列表（与 strip 互斥）
        default_title: 是否为没有标题的链接使用 URL 作为默认标题
        escape_asterisks: 是否转义星号
        escape_underscores: 是否转义下划线
        escape_misc: 是否转义其他特殊字符
        heading_style: 标题样式：'atx'、'atx_closed' 或 'underlined'
        keep_inline_images_in: 保持内联图片的父标签列表
        newline_style: 换行样式：'spaces' 或 'backslash'
        strip: 要移除的标签列表（与 convert 互斥）
        strip_document: 文档空白处理方式
        strip_pre: pre 标签空白处理方式
        strong_em_symbol: 粗体和斜体符号：'*' 或 '_'
        sub_symbol: 下标符号，默认为 '~'
        sup_symbol: 上标符号，默认为 '^'
        table_infer_header: 是否推断表格标题行
        wrap: 是否自动换行
        wrap_width: 换行宽度

    Returns:
        Markdown 字符串
    """
