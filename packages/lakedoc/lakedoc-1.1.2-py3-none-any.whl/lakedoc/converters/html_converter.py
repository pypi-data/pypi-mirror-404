"""
HTML 转换器

作者：
    gupingan [gupingan6@outlook.com]

特性：
    - 将 Lake 文档转换为 HTML 格式
    - 基于 md_converter 模块实现
    - html -> md -> html
"""

from typing import Optional, Set, List, Dict, Callable
from pathlib import Path
from bs4.element import Tag
import markdown
from lakedoc.utils import debug as debug_module
from .base import LakeBaseConverter
from .md_converter import MarkdownConverter
from .ht2md import (
    HeadingStyle,
    NewlineStyle,
    StrongEmSymbol,
    StripMode,
)


class HTMLConverter(LakeBaseConverter):
    """
    HTML 转换器，继承自 LakeBaseConverter

    设计原则：
    1. 使用 md_converter 将原始 HTML 转换为 Markdown
    2. 使用 markdown 库将 Markdown 转换为标准 HTML
    3. 保留原始 HTML 的样式和结构
    """

    name = "html"
    suffix = ".html"

    def __init__(
        self,
        raw_html: str,
        bs4_builder: str = "html.parser",
        title: Optional[str] = None,
        remove_tags: Optional[Set[str]] = None,
        diagram_as_code: bool = False,
        diagram_as_code_cond: Optional[Callable[[str, str, str],bool]] = None,
        autolinks: bool = True,
        bullets: str = "*+-",
        code_language: str = "",
        code_language_callback: Optional[Callable[[Tag], Optional[str]]] = None,
        convert: Optional[List[str]] = None,
        default_title: bool = False,
        escape_asterisks: bool = True,
        escape_underscores: bool = True,
        escape_misc: bool = False,
        heading_style: HeadingStyle = HeadingStyle.ATX,
        keep_inline_images_in: Optional[List[str]] = None,
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
        md_extensions: Optional[List[str]] = None,
        extension_configs: Optional[Dict[str, Dict]] = None,
    ):
        """
        Lake Doc -> HTML Doc

        :param raw_html: 未经过处理的 HTML 内容（最原生的）
        :param bs4_builder: BeautifulSoup 的树构建器，默认为 'html.parser'
        :param title: 指定设置转换后 HTML内容的标题，默认为 None
        :param remove_tags: 处理 html 时应该删除哪些标签，默认为 {'meta', 'link', 'script', 'style'}
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
        :param md_extensions: Markdown 扩展列表
        :param extension_configs: Markdown 扩展配置
        """
        # 初始化基础属性
        self.raw_html = raw_html
        self.title = title
        self.assets = Path(__file__).parent.parent.parent / "assets"

        # 初始化 md_converter（作为内部转换器）
        md_options = {
            "bs4_builder": bs4_builder,
            "title": title,
            "remove_tags": remove_tags,
            "diagram_as_code": diagram_as_code,
            "diagram_as_code_cond": diagram_as_code_cond,
            "autolinks": autolinks,
            "bullets": bullets,
            "code_language": code_language,
            "code_language_callback": code_language_callback,
            "convert": convert,
            "default_title": default_title,
            "escape_asterisks": escape_asterisks,
            "escape_underscores": escape_underscores,
            "escape_misc": escape_misc,
            "heading_style": heading_style,
            "keep_inline_images_in": keep_inline_images_in,
            "newline_style": newline_style,
            "strip": strip,
            "strip_document": strip_document,
            "strip_pre": strip_pre,
            "strong_em_symbol": strong_em_symbol,
            "sub_symbol": sub_symbol,
            "sup_symbol": sup_symbol,
            "table_infer_header": table_infer_header,
            "wrap": wrap,
            "wrap_width": wrap_width,
        }

        self._md_converter = MarkdownConverter(raw_html, **md_options)

        # Markdown 扩展配置
        self.md_extensions = md_extensions or [
            "markdown.extensions.extra",
            "markdown.extensions.codehilite",
            "markdown.extensions.toc",
            "markdown.extensions.tables",
            "markdown.extensions.fenced_code",
            "pymdownx.caret",
            "pymdownx.mark",
            "pymdownx.tilde",
        ]
        self.extension_configs = extension_configs or {}

    def convert(self) -> str:
        """执行 HTML -> Markdown -> HTML 的转换"""
        debug_module.debug_section("HTML 转换开始")
        debug_module.debug(f"标题: {self.title}", level=1)
        debug_module.debug(f"Markdown 扩展: {self.md_extensions}", level=1)

        # 1. 使用 md_converter 将原始 HTML 转换为 Markdown
        md_data = self._md_converter.convert()

        # 2. 使用 markdown 库将 Markdown 转换为标准 HTML
        html_data = self._markdown_to_html(md_data)

        # 3. 添加 HTML 文档结构
        html_data = self._wrap_html_document(html_data)

        debug_module.debug_section("HTML 转换完成")
        debug_module.debug(f"最终输出长度: {len(html_data)} 字符", level=1)

        return html_data

    def _markdown_to_html(self, md_content: str) -> str:
        """
        将 Markdown 内容转换为 HTML

        :param md_content: Markdown 内容
        :return: HTML 内容
        """
        debug_module.debug_subsection("Markdown 到 HTML 转换", level=1)

        # 使用 markdown 库转换
        html_content = markdown.markdown(
            md_content,
            extensions=self.md_extensions,
            extension_configs=self.extension_configs,
        )

        debug_module.debug(f"转换后 HTML 长度: {len(html_content)} 字符", level=2)

        return html_content

    def _wrap_html_document(self, body_content: str) -> str:
        """
        将 HTML 内容包装为完整的 HTML 文档

        :param body_content: HTML 主体内容
        :return: 完整的 HTML 文档
        """
        debug_module.debug_subsection("包装 HTML 文档", level=1)

        # 构建 HTML 文档结构
        html_doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.title or 'Lake Document'}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3, h4, h5, h6 {{
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            line-height: 1.25;
        }}
        h1 {{ font-size: 2em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }}
        h2 {{ font-size: 1.5em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }}
        h3 {{ font-size: 1.25em; }}
        h4 {{ font-size: 1em; }}
        h5 {{ font-size: 0.875em; }}
        h6 {{ font-size: 0.85em; color: #6a737d; }}
        code {{
            padding: 0.2em 0.4em;
            margin: 0;
            font-size: 85%;
            background-color: rgba(27, 31, 35, 0.05);
            border-radius: 3px;
        }}
        pre {{
            padding: 16px;
            overflow: auto;
            font-size: 85%;
            line-height: 1.45;
            background-color: #f6f8fa;
            border-radius: 3px;
        }}
        blockquote {{
            padding: 0 1em;
            color: #6a737d;
            border-left: 0.25em solid #dfe2e5;
            margin: 0 0 16px 0;
        }}
        table {{
            border-spacing: 0;
            border-collapse: collapse;
            margin-bottom: 16px;
        }}
        table th, table td {{
            padding: 6px 13px;
            border: 1px solid #dfe2e5;
        }}
        table th {{
            font-weight: 600;
            background-color: #f6f8fa;
        }}
        img {{
            max-width: 100%;
            height: auto;
        }}
        a {{
            color: #0366d6;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
{body_content}
</body>
</html>"""

        debug_module.debug(f"完整 HTML 文档长度: {len(html_doc)} 字符", level=2)

        return html_doc
