# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from bs4 import BeautifulSoup
from bs4.element import Comment, Doctype, Tag
from bs4.element import NavigableString
from textwrap import fill
import re


# 通用正则表达式模式
re_convert_heading = re.compile(r"convert_h(\d+)")
re_line_with_content = re.compile(r"^(.*)", flags=re.MULTILINE)
re_whitespace = re.compile(r"[\t ]+")
re_all_whitespace = re.compile(r"[\t \r\n]+")
re_newline_whitespace = re.compile(r"[\t \r\n]*[\r\n][\t \r\n]*")
re_html_heading = re.compile(r"h(\d+)")
re_pre_lstrip1 = re.compile(r"^ *\n")
re_pre_rstrip1 = re.compile(r"\n *$")
re_pre_lstrip = re.compile(r"^[ \n]*\n")
re_pre_rstrip = re.compile(r"[ \n]*$")

# 从标签名称创建 convert_<tag> 函数名称的模式
re_make_convert_fn_name = re.compile(r"[\[\]:-]")

# 从字符串中提取（前导换行符、内容、尾随换行符）
# （功能上等同于 r'^(\n*)(.*?)(\n*)$'，但贪婪匹配比非贪婪匹配更快）
re_extract_newlines = re.compile(r"^(\n*)((?:.*[^\n])?)(\n*)$", flags=re.DOTALL)

# 转义通用的特殊 Markdown 字符
re_escape_misc_chars = re.compile(r"([]\\&<`[>~=+|])")

# 转义一个或多个连续的 '-' 序列，前后有空白或片段的开始/结束，
# 因为它可能与标题下划线或列表标记混淆
re_escape_misc_dash_sequences = re.compile(r"(\s|^)(-+(?:\s|$))")

# 转义最多六个连续的 '#'，前后有空白或片段的开始/结束，
# 因为它可能与 ATX 标题混淆
re_escape_misc_hashes = re.compile(r"(\s|^)(#{1,6}(?:\s|$))")

# 转义前面最多有九位数字的 '.' 或 ')'，因为它可能与列表项混淆
re_escape_misc_list_items = re.compile(r"((?:\s|^)[0-9]{1,9})([.)](?:\s|$))")

# 在字符串中查找连续的反引号序列
re_backtick_runs = re.compile(r"`+")


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


def strip1_pre(text):
    """从 <pre> 字符串中去除一个前导和尾随换行符"""
    text = re_pre_lstrip1.sub("", text)
    text = re_pre_rstrip1.sub("", text)
    return text


def strip_pre(text):
    """从 <pre> 字符串中去除所有前导和尾随换行符"""
    text = re_pre_lstrip.sub("", text)
    text = re_pre_rstrip.sub("", text)
    return text


def chomp(text):
    """
    如果 b、a 或 em 等内联标签中的文本包含前导或尾随空格，
    则去除字符串并返回空格作为前缀或后缀（如果需要）
    此函数用于防止如下转换：
        <b> foo</b> => ** foo**
    """
    prefix = " " if text and text[0] == " " else ""
    suffix = " " if text and text[-1] == " " else ""
    text = text.strip()
    return (prefix, suffix, text)


def abstract_inline_conversion(markup_fn):
    """
    抽象所有简单的内联标签，如 b、em、del 等
    返回一个函数，将去除的文本包裹在 markup_fn 返回的字符串对中，
    如果它看起来像 HTML 标签，则在文本后使用的字符串中插入 '/'
    markup_fn 是必要的，以允许引用 self.strong_em_symbol 等
    """

    def implementation(self, el, text, parent_tags):
        markup_prefix = markup_fn(self)
        if markup_prefix.startswith("<") and markup_prefix.endswith(">"):
            markup_suffix = "</" + markup_prefix[1:]
        else:
            markup_suffix = markup_prefix
        if "_noformat" in parent_tags:
            return text
        prefix, suffix, text = chomp(text)
        if not text:
            return ""
        return "%s%s%s%s%s" % (prefix, markup_prefix, text, markup_suffix, suffix)

    return implementation


def _todict(obj):
    """将对象的属性转换为字典"""
    return dict((k, getattr(obj, k)) for k in dir(obj) if not k.startswith("_"))


def should_remove_whitespace_inside(el):
    """返回是否应立即移除块级元素内部的空白"""
    if not el or not el.name:
        return False
    if re_html_heading.match(el.name) is not None:
        return True
    return el.name in (
        "p",
        "blockquote",
        "article",
        "div",
        "section",
        "header",
        "footer",
        "nav",
        "main",
        "aside",
        "ol",
        "ul",
        "li",
        "dl",
        "dt",
        "dd",
        "table",
        "thead",
        "tbody",
        "tfoot",
        "tr",
        "td",
        "th",
        "figure",
        "figcaption",
    )


def should_remove_whitespace_outside(el):
    """返回是否应立即移除块级元素外部的空白"""
    return should_remove_whitespace_inside(el) or (el and el.name == "pre")


def _is_block_content_element(el):
    """
    在块上下文中，返回：
    - True 表示内容元素（标签和非空白文本）
    - False 表示非内容元素（空白文本、注释、文档类型）
    """
    if isinstance(el, Tag):
        return True
    elif isinstance(el, (Comment, Doctype)):
        return False  # （NavigableString 的子类，必须先测试）
    elif isinstance(el, NavigableString):
        return el.strip() != ""
    else:
        return False


def _prev_block_content_sibling(el):
    """返回第一个前一个内容元素兄弟，否则返回 None"""
    while el is not None:
        el = el.previous_sibling
        if _is_block_content_element(el):
            return el
    return None


def _next_block_content_sibling(el):
    """返回第一个下一个内容元素兄弟，否则返回 None"""
    while el is not None:
        el = el.next_sibling
        if _is_block_content_element(el):
            return el
    return None


@dataclass
class Options:
    """转换选项"""

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
    keep_inline_images_in: List[str] = field(default_factory=list)
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

    def __init__(self, **options):
        """
        初始化转换器

        Args:
            **options: 转换选项，覆盖默认值
        """
        # 创建选项实例
        self.options = Options(**options)

        # 验证 strip 和 convert 互斥
        if self.options.strip is not None and self.options.convert is not None:
            raise ValueError("您可以指定要移除的标签或要转换的标签，但不能同时指定两者")

        # 如果将字符串或列表传递给 bs4_options，假设它是 'features' 规范
        if not isinstance(self.options.bs4_options, dict):
            self.options.bs4_options = {"features": self.options.bs4_options}

        # 初始化转换函数缓存
        self.convert_fn_cache = {}

    def convert(self, html):
        """
        将 HTML 字符串转换为 Markdown

        Args:
            html: HTML 字符串

        Returns:
            Markdown 字符串
        """
        bs4_kwargs = (
            self.options.bs4_options
            if isinstance(self.options.bs4_options, dict)
            else {"features": self.options.bs4_options}
        )
        soup = BeautifulSoup(html, **bs4_kwargs)
        return self.convert_soup(soup)

    def convert_soup(self, soup):
        """
        将 BeautifulSoup 对象转换为 Markdown

        Args:
            soup: BeautifulSoup 对象

        Returns:
            Markdown 字符串
        """
        return self.process_tag(soup, parent_tags=set())

    def process_element(self, node, parent_tags=None):
        """
        处理元素节点

        Args:
            node: 要处理的节点
            parent_tags: 父标签集合

        Returns:
            处理后的字符串
        """
        if isinstance(node, NavigableString):
            return self.process_text(node, parent_tags=parent_tags)
        else:
            return self.process_tag(node, parent_tags=parent_tags)

    def process_tag(self, node, parent_tags=None):
        """
        处理标签节点

        Args:
            node: 要处理的标签节点
            parent_tags: 父标签集合

        Returns:
            处理后的字符串
        """
        # 对于顶层元素，使用空集初始化父上下文
        if parent_tags is None:
            parent_tags = set()

        # 收集要处理的子元素，忽略块元素内/外边界相邻的仅空白文本元素
        should_remove_inside = should_remove_whitespace_inside(node)

        def _can_ignore(el):
            """判断元素是否可以忽略"""
            if isinstance(el, Tag):
                # 标签总是被处理
                return False
            elif isinstance(el, (Comment, Doctype)):
                # 注释和文档类型元素总是被忽略
                # （NavigableString 的子类，必须先测试）
                return True
            elif isinstance(el, NavigableString):
                if str(el).strip() != "":
                    # 非空白文本节点总是被处理
                    return False
                elif should_remove_inside and (
                    not el.previous_sibling or not el.next_sibling
                ):
                    # 在块元素内部（不包括 <pre>），忽略相邻的空白元素
                    return True
                elif should_remove_whitespace_outside(
                    el.previous_sibling
                ) or should_remove_whitespace_outside(el.next_sibling):
                    # 在块元素外部（包括 <pre>），忽略相邻的空白元素
                    return True
                else:
                    return False
            elif el is None:
                return True
            else:
                raise ValueError("意外的元素类型：%s" % type(el))

        children_to_convert = [el for el in node.children if not _can_ignore(el)]

        # 创建此标签父上下文的副本，然后更新它以包含此标签，
        # 以便向下传播到子元素
        parent_tags_for_children = set(parent_tags)
        parent_tags_for_children.add(node.name)

        # 如果此标签是标题或表格单元格，添加 '_inline' 父伪标签
        if re_html_heading.match(node.name) is not None or node.name in {  # 标题
            "td",
            "th",
        }:  # 表格单元格
            parent_tags_for_children.add("_inline")

        # 如果此标签是预格式化元素，添加 '_noformat' 父伪标签
        if node.name in {"pre", "code", "kbd", "samp"}:
            parent_tags_for_children.add("_noformat")

        # 将子元素转换为结果字符串列表
        child_strings = [
            self.process_element(el, parent_tags=parent_tags_for_children)
            for el in children_to_convert
        ]

        # 移除空字符串值
        child_strings = [s for s in child_strings if s]

        # 如果需要，在子元素边界处折叠换行符
        if node.name == "pre" or node.find_parent("pre"):
            # 在 <pre> 块内，不折叠换行符
            pass
        else:
            # 在子元素边界处折叠换行符
            updated_child_strings = [""]  # 使第一次回溯工作
            for child_string in child_strings:
                # 将前导/尾随换行符与内容分离
                match = re_extract_newlines.match(child_string)
                if match:
                    leading_nl, content, trailing_nl = match.groups()
                else:
                    leading_nl, content, trailing_nl = "", child_string, ""

                # 如果最后一个子元素有尾随换行符，且此子元素有前导换行符，
                # 则使用较大的换行符计数，限制为 2
                if updated_child_strings[-1] and leading_nl:
                    prev_trailing_nl = updated_child_strings.pop()  # 将被折叠的值替换
                    num_newlines = min(2, max(len(prev_trailing_nl), len(leading_nl)))
                    leading_nl = "\n" * num_newlines

                # 将结果添加到更新的子字符串列表中
                updated_child_strings.extend([leading_nl, content, trailing_nl])

            child_strings = updated_child_strings

        # 将所有子文本字符串连接成单个字符串
        text = "".join(child_strings)

        # 应用此标签的最终转换函数
        convert_fn = self.get_conv_fn_cached(node.name)
        
        if convert_fn is not None:
            text = convert_fn(node, text, parent_tags=parent_tags)

        return text

    def convert__document_(self, el, text, parent_tags):
        """
        BeautifulSoup 对象的最终文档级格式化（node.name == "[document]"）

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            格式化后的字符串
        """
        if self.options.strip_document == StripMode.LSTRIP:
            text = text.lstrip("\n")  # 移除前导分隔换行符
        elif self.options.strip_document == StripMode.RSTRIP:
            text = text.rstrip("\n")  # 移除尾随分隔换行符
        elif self.options.strip_document == StripMode.STRIP:
            text = text.strip("\n")  # 移除前导和尾随分隔换行符
        elif self.options.strip_document is None:
            pass  # 保持前导和尾随分隔换行符不变
        else:
            raise ValueError(
                "strip_document 的值无效：%s" % self.options.strip_document
            )

        return text

    def process_text(self, el, parent_tags=None):
        """
        处理文本节点

        Args:
            el: 文本节点
            parent_tags: 父标签集合

        Returns:
            处理后的字符串
        """
        # 对于顶层元素，使用空集初始化父上下文
        if parent_tags is None:
            parent_tags = set()

        text = str(el) or ""

        # 如果我们不在预格式化元素内，则规范化空白
        if "pre" not in parent_tags:
            if self.options.wrap:
                text = re_all_whitespace.sub(" ", text)
            else:
                text = re_newline_whitespace.sub("\n", text)
                text = re_whitespace.sub(" ", text)

        # 如果我们不在预格式化或代码元素内，则转义特殊字符
        if "_noformat" not in parent_tags:
            text = self.escape(text, parent_tags)

        # 在开始处或块级元素之后移除前导空白
        # 在结束处或块级元素之前移除尾随空白
        if should_remove_whitespace_outside(el.previous_sibling) or (
            should_remove_whitespace_inside(el.parent) and not el.previous_sibling
        ):
            text = text.lstrip(" \t\r\n")
        if should_remove_whitespace_outside(el.next_sibling) or (
            should_remove_whitespace_inside(el.parent) and not el.next_sibling
        ):
            text = text.rstrip()

        return text

    def get_conv_fn_cached(self, tag_name):
        """
        给定标签名称，使用缓存返回转换函数

        Args:
            tag_name: 标签名称

        Returns:
            转换函数
        """
        # 如果转换函数不在缓存中，则添加它
        if tag_name not in self.convert_fn_cache:
            self.convert_fn_cache[tag_name] = self.get_conv_fn(tag_name)

        # 返回缓存条目
        return self.convert_fn_cache[tag_name]

    def get_conv_fn(self, tag_name):
        """
        给定标签名称，查找并返回转换函数

        Args:
            tag_name: 标签名称

        Returns:
            转换函数
        """
        tag_name = tag_name.lower()

        # 处理 strip/convert 排除选项
        if not self.should_convert_tag(tag_name):
            return None

        # 首先按标签名称查找显式定义的转换函数
        convert_fn_name = "convert_%s" % re_make_convert_fn_name.sub("_", tag_name)
        convert_fn = getattr(self, convert_fn_name, None)
        if convert_fn:
            return convert_fn

        # 如果标签是任何标题，使用 convert_hN() 函数处理
        match = re_html_heading.match(tag_name)
        if match:
            n = int(match.group(1))  # 从 <hN> 获取 N 的值
            return lambda el, text, parent_tags: self.convert_hN(
                n, el, text, parent_tags
            )

        # 未找到转换函数
        return None

    def should_convert_tag(self, tag):
        """
        给定标签名称，根据 strip/convert 选项返回是否转换

        Args:
            tag: 标签名称

        Returns:
            是否转换该标签
        """
        strip = self.options.strip
        convert = self.options.convert
        if strip is not None:
            return tag not in strip
        elif convert is not None:
            return tag in convert
        else:
            return True

    def escape(self, text, parent_tags):
        """
        转义 Markdown 特殊字符

        Args:
            text: 要转义的文本
            parent_tags: 父标签集合

        Returns:
            转义后的文本
        """
        if not text:
            return ""
        if self.options.escape_misc:
            text = re_escape_misc_chars.sub(r"\\\1", text)
            text = re_escape_misc_dash_sequences.sub(r"\1\\\2", text)
            text = re_escape_misc_hashes.sub(r"\1\\\2", text)
            text = re_escape_misc_list_items.sub(r"\1\\\2", text)

        if self.options.escape_asterisks:
            text = text.replace("*", r"\*")
        if self.options.escape_underscores:
            text = text.replace("_", r"\_")

        return text

    def underline(self, text, pad_char):
        """
        使用下划线格式化文本

        Args:
            text: 文本
            pad_char: 填充字符

        Returns:
            格式化后的字符串
        """
        text = (text or "").rstrip()
        return "\n\n%s\n%s\n\n" % (text, pad_char * len(text)) if text else ""

    def convert_a(self, el, text, parent_tags):
        """
        转换 <a> 标签

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 链接
        """
        if "_noformat" in parent_tags:
            return text
        prefix, suffix, text = chomp(text)
        if not text:
            return ""
        href = el.get("href")
        title = el.get("title")
        # 有关替换请参见 #29：文本节点下划线被转义
        if (
            self.options.autolinks
            and text.replace(r"\_", "_") == href
            and not title
            and not self.options.default_title
        ):
            # 快捷语法
            return "<%s>" % href
        if self.options.default_title and not title:
            title = href
        title_part = ' "%s"' % title.replace('"', r"\"") if title else ""
        return (
            "%s[%s](%s%s)%s" % (prefix, text, href, title_part, suffix)
            if href
            else text
        )

    convert_b = abstract_inline_conversion(
        lambda self: 2 * self.options.strong_em_symbol.value
    )

    def convert_blockquote(self, el, text, parent_tags):
        """
        转换 <blockquote> 标签

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 引用块
        """
        # 处理一些提前退出的场景
        text = (text or "").strip(" \t\r\n")
        if "_inline" in parent_tags:
            return " " + text + " "
        if not text:
            return "\n"

        # 用引用标记缩进行
        def _indent_for_blockquote(match):
            line_content = match.group(1)
            return "> " + line_content if line_content else ">"

        text = re_line_with_content.sub(_indent_for_blockquote, text)

        return "\n" + text + "\n\n"

    def convert_br(self, el, text, parent_tags):
        """
        转换 <br> 标签

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 换行
        """
        if "_inline" in parent_tags:
            return " "

        if self.options.newline_style == NewlineStyle.BACKSLASH:
            return "\\\n"
        else:
            return "  \n"

    def convert_code(self, el, text, parent_tags):
        """
        转换 <code> 标签

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 行内代码
        """
        if "_noformat" in parent_tags:
            return text

        prefix, suffix, text = chomp(text)
        if not text:
            return ""

        # 查找文本中连续反引号的最大数量，然后用多一个反引号分隔代码范围
        max_backticks = max(
            (len(match) for match in re.findall(re_backtick_runs, text)), default=0
        )
        markup_delimiter = "`" * (max_backticks + 1)

        # 如果最大反引号数大于零，则添加空格以避免将内部反引号解释为字面量
        if max_backticks > 0:
            text = " " + text + " "

        return "%s%s%s%s%s" % (prefix, markup_delimiter, text, markup_delimiter, suffix)

    convert_del = abstract_inline_conversion(lambda self: "~~")

    def convert_div(self, el, text, parent_tags):
        """
        转换 <div> 标签

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 块
        """
        if "_inline" in parent_tags:
            return " " + text.strip() + " "
        text = text.strip()
        return "\n\n%s\n\n" % text if text else ""

    convert_article = convert_div
    convert_section = convert_div
    convert_header = convert_div
    convert_footer = convert_div
    convert_nav = convert_div
    convert_main = convert_div
    convert_aside = convert_div

    convert_em = abstract_inline_conversion(
        lambda self: self.options.strong_em_symbol.value
    )

    convert_kbd = convert_code

    def convert_dd(self, el, text, parent_tags):
        """
        转换 <dd> 标签（定义列表描述）

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 定义描述
        """
        text = (text or "").strip()
        if "_inline" in parent_tags:
            return " " + text + " "
        if not text:
            return "\n"

        # 将定义内容行缩进四个空格
        def _indent_for_dd(match):
            line_content = match.group(1)
            return "    " + line_content if line_content else ""

        text = re_line_with_content.sub(_indent_for_dd, text)

        # 将定义标记插入到第一行缩进空白中
        text = ":" + text[1:]

        return "%s\n" % text

    # 定义列表的格式如下：
    #   https://pandoc.org/MANUAL.html#definition-lists
    #   https://michelf.ca/projects/php-markdown/extra/#def-list
    convert_dl = convert_div

    def convert_dt(self, el, text, parent_tags):
        """
        转换 <dt> 标签（定义列表术语）

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 定义术语
        """
        # 从术语文本中移除换行符
        text = (text or "").strip()
        text = re_all_whitespace.sub(" ", text)
        if "_inline" in parent_tags:
            return " " + text + " "
        if not text:
            return "\n"

        # TODO - 将连续的 <dt> 元素格式化为直接相邻的行：
        #   https://michelf.ca/projects/php-markdown/extra/#def-list

        return "\n\n%s\n" % text

    def convert_hN(self, n, el, text, parent_tags):
        """
        转换 <hN> 标签

        Args:
            n: 标题级别
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 标题
        """
        # convert_hN() 转换 <hN> 标签，其中 N 是任何整数
        if "_inline" in parent_tags:
            return text

        # Markdown 不支持深度 n > 6 的标题
        n = max(1, min(6, n))

        style = self.options.heading_style
        text = text.strip()
        if style == HeadingStyle.UNDERLINED and n <= 2:
            line = "=" if n == 1 else "-"
            return self.underline(text, line)
        text = re_all_whitespace.sub(" ", text)
        hashes = "#" * n
        if style == HeadingStyle.ATX_CLOSED:
            return "\n\n%s %s %s\n\n" % (hashes, text, hashes)
        return "\n\n%s %s\n\n" % (hashes, text)

    def convert_hr(self, el, text, parent_tags):
        """
        转换 <hr> 标签

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 水平线
        """
        return "\n\n---\n\n"

    convert_i = convert_em

    def convert_img(self, el, text, parent_tags):
        """
        转换 <img> 标签

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 图片
        """
        alt = el.attrs.get("alt", None) or ""
        src = el.attrs.get("src", None) or ""
        title = el.attrs.get("title", None) or ""
        title_part = ' "%s"' % title.replace('"', r"\"") if title else ""
        if (
            "_inline" in parent_tags
            and el.parent.name not in self.options.keep_inline_images_in
        ):
            return alt

        return "![%s](%s%s)" % (alt, src, title_part)

    def convert_video(self, el, text, parent_tags):
        """
        转换 <video> 标签

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 视频（转换为链接或图片链接）
        """
        if (
            "_inline" in parent_tags
            and el.parent.name not in self.options.keep_inline_images_in
        ):
            return text
        src = el.attrs.get("src", None) or ""
        if not src:
            sources = el.find_all("source", attrs={"src": True})
            if sources:
                src = sources[0].attrs.get("src", None) or ""
        poster = el.attrs.get("poster", None) or ""
        if src and poster:
            return "[![%s](%s)](%s)" % (text, poster, src)
        if src:
            return "[%s](%s)" % (text, src)
        if poster:
            return "![%s](%s)" % (text, poster)
        return text

    def convert_audio(self, el, text, parent_tags):
        """
        转换 <audio> 标签

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 音频（转换为链接）
        """
        if (
            "_inline" in parent_tags
            and el.parent.name not in self.options.keep_inline_images_in
        ):
            return text
        src = el.attrs.get("src", None) or ""
        if not src:
            sources = el.find_all("source", attrs={"src": True})
            if sources:
                src = sources[0].attrs.get("src", None) or ""
        if src:
            return "[%s](%s)" % (text, src)
        return text

    def convert_list(self, el, text, parent_tags):
        """
        转换列表标签

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 列表
        """
        # 将列表转换为内联是未定义的
        # 忽略列表的内联转换父级

        before_paragraph = False
        next_sibling = _next_block_content_sibling(el)
        if next_sibling and next_sibling.name not in ["ul", "ol"]:
            before_paragraph = True
        if "li" in parent_tags:
            # 如果我们在嵌套列表中，移除尾随换行符
            return "\n" + text.rstrip()
        return "\n\n" + text + ("\n" if before_paragraph else "")

    convert_ul = convert_list
    convert_ol = convert_list

    def convert_li(self, el, text, parent_tags):
        """
        转换 <li> 标签

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 列表项
        """
        # 处理一些提前退出的场景
        text = (text or "").strip()
        if not text:
            return "\n"

        # 确定要使用的列表项标记字符
        parent = el.parent
        if parent is not None and parent.name == "ol":
            if parent.get("start") and str(parent.get("start")).isnumeric():
                start = int(parent.get("start"))
            else:
                start = 1
            bullet = "%s." % (start + len(el.find_previous_siblings("li")))
        else:
            depth = -1
            while el:
                if el.name == "ul":
                    depth += 1
                el = el.parent
            bullets = self.options.bullets
            bullet = bullets[depth % len(bullets)]
        bullet = bullet + " "
        bullet_width = len(bullet)
        bullet_indent = " " * bullet_width

        # 按标记宽度缩进内容行
        def _indent_for_li(match):
            line_content = match.group(1)
            return bullet_indent + line_content if line_content else ""

        text = re_line_with_content.sub(_indent_for_li, text)

        # 将标记插入到第一行缩进空白中
        text = bullet + text[bullet_width:]

        return "%s\n" % text

    def convert_p(self, el, text, parent_tags):
        """
        转换 <p> 标签

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 段落
        """
        if "_inline" in parent_tags:
            return " " + text.strip(" \t\r\n") + " "
        text = text.strip(" \t\r\n")
        if self.options.wrap:
            # 保留由 <br> 标签产生的换行符（和前面的空白）
            # 输入中的换行符已被空格替换
            if self.options.wrap_width is not None:
                lines = text.split("\n")
                new_lines = []
                for line in lines:
                    line = line.lstrip(" \t\r\n")
                    line_no_trailing = line.rstrip()
                    trailing = line[len(line_no_trailing) :]
                    line = fill(
                        line,
                        width=self.options.wrap_width,
                        break_long_words=False,
                        break_on_hyphens=False,
                    )
                    new_lines.append(line + trailing)
                text = "\n".join(new_lines)
        return "\n\n%s\n\n" % text if text else ""

    def convert_pre(self, el, text, parent_tags):
        """
        转换 <pre> 标签

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 代码块
        """
        if not text:
            return ""
        code_language = self.options.code_language

        if self.options.code_language_callback:
            code_language = self.options.code_language_callback(el) or code_language

        if self.options.strip_pre == StripMode.STRIP:
            text = strip_pre(text)  # 移除所有前导/尾随换行符
        elif self.options.strip_pre == StripMode.STRIP_ONE:
            text = strip1_pre(text)  # 移除一个前导/尾随换行符
        elif self.options.strip_pre is None:
            pass  # 保持前导和尾随换行符不变
        else:
            raise ValueError("strip_pre 的值无效：%s" % self.options.strip_pre)

        return "\n\n```%s\n%s\n```\n\n" % (code_language, text)

    def convert_q(self, el, text, parent_tags):
        """
        转换 <q> 标签（行内引用）

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 引用文本
        """
        return '"' + text + '"'

    def convert_script(self, el, text, parent_tags):
        """
        转换 <script> 标签（忽略脚本内容）

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            空字符串
        """
        return ""

    def convert_style(self, el, text, parent_tags):
        """
        转换 <style> 标签（忽略样式内容）

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            空字符串
        """
        return ""

    convert_s = convert_del
    convert_strong = convert_b
    convert_samp = convert_code
    convert_sub = abstract_inline_conversion(lambda self: self.options.sub_symbol)
    convert_sup = abstract_inline_conversion(lambda self: self.options.sup_symbol)

    def convert_table(self, el, text, parent_tags):
        """
        转换 <table> 标签

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 表格
        """
        return "\n\n" + text.strip() + "\n\n"

    def convert_caption(self, el, text, parent_tags):
        """
        转换 <caption> 标签

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 表格标题
        """
        return text.strip() + "\n\n"

    def convert_figcaption(self, el, text, parent_tags):
        """
        转换 <figcaption> 标签

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 图片说明
        """
        return "\n\n" + text.strip() + "\n\n"

    def convert_td(self, el, text, parent_tags):
        """
        转换 <td> 标签

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 表格单元格
        """
        colspan = 1
        if "colspan" in el.attrs and el["colspan"].isdigit():
            colspan = max(1, min(1000, int(el["colspan"])))
        return " " + text.strip().replace("\n", " ") + " |" * colspan

    def convert_th(self, el, text, parent_tags):
        """
        转换 <th> 标签

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 表格标题单元格
        """
        colspan = 1
        if "colspan" in el.attrs and el["colspan"].isdigit():
            colspan = max(1, min(1000, int(el["colspan"])))
        return " " + text.strip().replace("\n", " ") + " |" * colspan

    def convert_tr(self, el, text, parent_tags):
        """
        转换 <tr> 标签

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 表格行
        """
        cells = el.find_all(["td", "th"])
        is_first_row = el.find_previous_sibling() is None
        is_headrow = all([cell.name == "th" for cell in cells]) or (
            el.parent.name == "thead"
            # 避免在 thead 中有多个 tr
            and len(el.parent.find_all("tr")) == 1
        )
        is_head_row_missing = (is_first_row and not el.parent.name == "tbody") or (
            is_first_row
            and el.parent.name == "tbody"
            and len(el.parent.parent.find_all(["thead"])) < 1
        )
        overline = ""
        underline = ""
        full_colspan = 0
        for cell in cells:
            if "colspan" in cell.attrs and cell["colspan"].isdigit():
                full_colspan += max(1, min(1000, int(cell["colspan"])))
            else:
                full_colspan += 1
        if (
            is_headrow or (is_head_row_missing and self.options.table_infer_header)
        ) and is_first_row:
            # 第一行且：
            # - 是标题行或
            # - 标题行缺失且启用了标题推断
            # 打印标题下划线
            underline += "| " + " | ".join(["---"] * full_colspan) + " |" + "\n"
        elif (is_head_row_missing and not self.options.table_infer_header) or (
            is_first_row
            and (
                el.parent.name == "table"
                or (el.parent.name == "tbody" and not el.parent.find_previous_sibling())
            )
        ):
            # 标题行缺失且禁用了标题推断或：
            # 第一行，不是标题行，且：
            #  - 父级是 table 或
            #  - 父级是表格开头的 tbody
            # 在此行上方打印空标题
            overline += "| " + " | ".join([""] * full_colspan) + " |" + "\n"
            overline += "| " + " | ".join(["---"] * full_colspan) + " |" + "\n"
        return overline + "|" + text + "\n" + underline

    def convert_mark(self, el, text, parent_tags):
        """
        转换 <mark> 标签（高亮文本）

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 高亮文本（使用 == 标记）
        """
        if "_noformat" in parent_tags:
            return text
        prefix, suffix, text = chomp(text)
        if not text:
            return ""
        return "%s==%s==%s" % (prefix, text, suffix)

    def convert_abbr(self, el, text, parent_tags):
        """
        转换 <abbr> 标签（缩写）

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 缩写文本（保留原文本）
        """
        return text

    def convert_time(self, el, text, parent_tags):
        """
        转换 <time> 标签

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 时间文本
        """
        return text

    def convert_address(self, el, text, parent_tags):
        """
        转换 <address> 标签

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 地址文本
        """
        if "_inline" in parent_tags:
            return " " + text.strip() + " "
        text = text.strip()
        return "\n\n%s\n\n" % text if text else ""

    def convert_details(self, el, text, parent_tags):
        """
        转换 <details> 标签（可折叠详情）

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 详情块（使用 HTML 语法）
        """
        summary = el.find("summary")
        if summary:
            summary_text = self.process_tag(summary, parent_tags=parent_tags)
            # 移除 summary 元素，避免重复处理
            summary.extract()
            content = self.process_tag(el, parent_tags=parent_tags)
            return "\n\n<details>\n<summary>%s</summary>\n\n%s\n</details>\n\n" % (
                summary_text,
                content,
            )
        return "\n\n<details>\n\n%s\n</details>\n\n" % text

    def convert_summary(self, el, text, parent_tags):
        """
        转换 <summary> 标签（详情摘要）

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 摘要文本
        """
        return text

    def convert_progress(self, el, text, parent_tags):
        """
        转换 <progress> 标签（进度条）

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 进度文本
        """
        value = el.get("value", "")
        max_value = el.get("max", "")
        if value and max_value:
            return "进度：%s/%s" % (value, max_value)
        elif value:
            return "进度：%s" % value
        return text

    def convert_meter(self, el, text, parent_tags):
        """
        转换 <meter> 标签（度量衡）

        Args:
            el: 元素
            text: 文本内容
            parent_tags: 父标签集合

        Returns:
            Markdown 度量文本
        """
        value = el.get("value", "")
        min_value = el.get("min", "")
        max_value = el.get("max", "")
        if value and min_value and max_value:
            return "度量：%s（范围：%s-%s）" % (value, min_value, max_value)
        elif value:
            return "度量：%s" % value
        return text


def convert(html, **options):
    """
    将 HTML 转换为 Markdown 的便捷函数

    Args:
        html: HTML 字符串
        **options: 转换选项

    Returns:
        Markdown 字符串
    """
    return MarkdownConverter(**options).convert(html)
