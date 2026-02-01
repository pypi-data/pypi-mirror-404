"""
Markdown 转换器

作者：
    gupingan [gupingan6@outlook.com]

特性：
    - 能够良好的处理换行和段落的缩进（还原率极高）
    - 支持转换的基本语法：标题、段落、粗/斜体、引用、分隔线、超链接、静态图片、Emoji、GIF图……
    - 支持转换的进阶语法：代码块、列表、内嵌 HTML、数学公式……
    - 大多数文本的转换将携带颜色（前景色、背景色）转换，表格将直接嵌入到 Markdown 内容中
    - 解决相邻<em>标签转换后的斜体二义性、相邻的<strong>标签转换后的粗体二义性两个问题

注意：
    部分语法暂未适配，可能存在失效（丢失、直接显示、乱码），如果需要适配，请提供文档库给我，并标明相关位置
"""

from typing import Optional, Callable, List, Dict, Set
from urllib.parse import unquote
from pathlib import Path
from bs4 import BeautifulSoup, FeatureNotFound
from bs4.element import Tag
from lakedoc.utils import string, debug as debug_module, errors
from .base import LakeBaseConverter
from .ht2md import (
    MarkdownConverter as MDConverter,
    HeadingStyle,
    NewlineStyle,
    StrongEmSymbol,
    StripMode,
)


class MarkdownConverter(LakeBaseConverter):
    """
    Markdown 转换器，继承自 LakeBaseConverter，使用 ht2md 作为核心转换引擎

    设计原则：
    1. LakeBaseConverter 提供基础 HTML 处理功能（如 create_html、render_styles）
    2. ht2md.MDConverter 提供核心 HTML 到 Markdown 的转换能力
    3. 本类整合两者，提供语雀特有的标签转换（如 card、font 等）
    """

    name = "markdown"
    suffix = ".md"

    def __init__(
        self,
        raw_html: str,
        bs4_builder: str = "html.parser",
        title: Optional[str] = None,
        remove_tags: Optional[Set[str]] = None,
        diagram_as_code: bool = False,
        diagram_as_code_cond: Optional[Callable[[str, str, str], bool]] = None,
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
    ):
        """
        Lake Doc -> Markdown Doc

        :param raw_html: 未经过处理的 HTML 内容（最原生的）
        :param bs4_builder: BeautifulSoup 的树构建器，默认为 'html.parser'
        :param title: 指定设置转换后 Markdown内容顶行的标题，默认为 None
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
        """
        # 基础属性
        self.assets = Path(__file__).parent.parent.parent / "assets"
        self.raw_html = raw_html
        self.bs4_builder = bs4_builder
        self.remove_tags = remove_tags or {"meta", "link", "script", "style"}
        self.soup = self.create_bs4soup()

        # ht2md.MDConverter
        ht2md_options = {
            "bs4_options": bs4_builder,
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
            "keep_inline_images_in": keep_inline_images_in or [],
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

        self._ht2md_converter = MDConverter(**ht2md_options)

        # 其它属性
        self.title = title
        self.diagram_as_code = diagram_as_code
        self.diagram_as_code_cond = diagram_as_code_cond
        self.card_counter = {}

    def render_styles(self, el):
        """
        根据 element 对象，渲染出对应的合法样式
        :param el: bs4 中的 PageElement 对象
        """
        if "style" not in el.attrs:
            return None

        raw_style = el.attrs["style"]
        raw_styles = [si.strip() for si in raw_style.split(";") if ":" in si]
        styles: Dict[str, str] = {
            si.split(":", 1)[0].strip(): si.split(":", 1)[-1].strip()
            for si in raw_styles
        }

        if debug_module.is_debug_enabled():
            style_keys = list(styles.keys())
            if style_keys:
                debug_module.debug(
                    f"处理样式: <{el.name}> {style_keys}", level=3, color="magenta"
                )

        if "color" in styles or "background-color" in styles:
            if el.parent and el in el.parent.contents and el.string:
                new_tag = BeautifulSoup(
                    f'<font style="{raw_style}">{el.string}</font>', self.bs4_builder
                ).font
                el = el.replace_with(new_tag)
                debug_module.debug(
                    f"应用颜色样式: <{el.name}>", level=3, color="magenta"
                )

        if "text-indent" in styles:
            text_indent = string.extract_integer(styles["text-indent"])
            prefix = "<span>&#8195;</span>" * text_indent
            if el.parent:
                el.insert_before(BeautifulSoup(prefix, self.bs4_builder))
                debug_module.debug(
                    f"应用 text-indent: {text_indent}", level=3, color="magenta"
                )
        elif "padding-left" in styles:
            text_indent = string.extract_integer(styles["padding-left"])
            prefix = "<span>&#8195;</span>" * text_indent
            if el.parent:
                el.insert_before(BeautifulSoup(prefix, self.bs4_builder))
                debug_module.debug(
                    f"应用 padding-left: {text_indent}", level=3, color="magenta"
                )

    def create_html(self) -> str:
        """
        处理、创建更加合法的 HTML 内容

        :return: HTML 字符串内容
        """
        debug_module.debug_section("处理 HTML 内容")
        debug_module.debug(f"待删除标签: {self.remove_tags}", level=1)

        tag_count = 0
        removed_count = 0
        styled_count = 0

        for tag in self.soup.find_all(True):
            tag_count += 1
            self.render_styles(tag)

            if tag.name in self.remove_tags:
                tag.extract()
                removed_count += 1
                debug_module.debug(f"删除标签: <{tag.name}>", level=2, color="yellow")

        debug_module.debug(f"总标签数: {tag_count}", level=1)
        debug_module.debug(f"删除标签数: {removed_count}", level=1)
        debug_module.debug(f"处理样式标签数: {styled_count}", level=1)

        result = str(self.soup)
        debug_module.debug(f"处理后 HTML 长度: {len(result)} 字符", level=1)

        return result

    def convert(self) -> str:
        """执行 HTML 到 Markdown 的转换"""
        debug_module.debug_section("Markdown 转换开始")
        debug_module.debug(f"标题: {self.title}", level=1)

        # 1. 使用 create_html 处理 HTML（移除标签、渲染样式等）
        html_data = self.create_html()

        # 2. 使用 ht2md 转换器进行核心转换
        # 先注册自定义转换方法
        self._register_custom_converters()
        md_data = self._ht2md_converter.convert(html_data)

        # 3. 添加标题
        md_data = self.add_title(md_data)

        debug_module.debug_section("Markdown 转换完成")
        debug_module.debug(f"最终输出长度: {len(md_data)} 字符", level=1)

        return md_data

    def _register_custom_converters(self):
        """注册自定义转换方法到 ht2md 转换器"""
        setattr(self._ht2md_converter, "convert_card", self.convert_card)
        setattr(self._ht2md_converter, "convert_font", self.convert_font)
        setattr(self._ht2md_converter, "convert_li", self.convert_li)

    def convert_font(self, el, text, parent_tags):
        """转换 font 标签（保留颜色样式）"""
        if debug_module.is_debug_enabled():
            style = el.get("style", "")
            debug_module.debug(
                f"转换 font 标签: style={style[:50] if len(style) > 50 else style}",
                level=3,
            )
        return str(el) if text else ""

    def convert_card(self, el, text, parent_tags):
        """转换 card 标签（语雀特有的卡片组件）"""
        card_type = el.attrs["name"]

        # 统计 card 类型
        self.card_counter[card_type] = self.card_counter.get(card_type, 0) + 1

        if debug_module.is_debug_enabled():
            debug_module.debug(f"转换 card: type={card_type}", level=3)

        if card_type == "hr":
            if debug_module.is_debug_enabled():
                debug_module.debug("  -> 分隔线", level=4)
            return "---\n"
        elif card_type in ("image", "flowchart2", "board"):
            card_data = string.decode_card_value(el.attrs.get("value", ""))
            src = card_data.get("src", "")
            if debug_module.is_debug_enabled():
                debug_module.debug(f"  -> 图片: {src[:50]}...", level=4)
            return f"  ![图片未加载]({src})\n"
        elif card_type == "table":
            card_data = string.decode_card_value(el.attrs.get("value", ""))
            if debug_module.is_debug_enabled():
                html_len = len(card_data.get("html", ""))
                debug_module.debug(f"  -> 表格: HTML长度={html_len}", level=4)
            return f'{card_data["html"]}\n'
        elif card_type == "codeblock":
            card_data = string.decode_card_value(el.attrs.get("value", ""))
            mode = card_data.get("mode", "")
            code = card_data.get("code", "")
            if debug_module.is_debug_enabled():
                code_len = len(code)
                debug_module.debug(
                    f"  -> 代码块: mode={mode} | 长度={code_len}", level=4
                )
            return f"\n```{mode}\n{code}\n```\n"
        elif card_type == "diagram":
            if debug_module.is_debug_enabled():
                debug_module.debug(
                    f"  -> unquoted: {unquote(el.attrs.get('value', ''))}", level=4
                )
            card_data = string.decode_card_value(el.attrs.get("value", ""))
            # issue #1 https://github.com/gupingan/lakedoc/issues/1
            src = card_data.get("url", "")
            code_type = card_data.get("type", "plaintext")
            raw_code_data = card_data.get("code", "")

            # 检查是否应该转换为代码块
            should_convert_to_code = False
            if self.diagram_as_code:
                if self.diagram_as_code_cond is None or self.diagram_as_code_cond(
                    src, code_type, raw_code_data
                ):
                    should_convert_to_code = True

            if debug_module.is_debug_enabled():
                debug_module.debug(
                    f"  -> diagram: type={code_type} | has_url={bool(src)} | to_code={should_convert_to_code}",
                    level=4,
                )

            if src and not should_convert_to_code:
                # 基于图表 src 图片渲染（默认行为）
                return f"![图表]({src})\n"
            else:
                # 当 URL 不存在时或转换为代码块时展示
                code_data = raw_code_data.replace("\\n", "<br/>")
                return f"\n```{code_type}\n{code_data}\n```\n"
        elif card_type == "math":
            card_data = string.decode_card_value(el.attrs.get("value", ""))
            code = card_data.get("code", "")
            is_center = "center" in el.parent.get("style", "")
            if debug_module.is_debug_enabled():
                debug_module.debug(
                    f"  -> 数学公式: center={is_center} | 长度={len(code)}", level=4
                )
            if is_center:
                return f"$$\n{code}\n$$"
            return f"$${code}$$"
        elif card_type == "yuqueinline":
            card_data = string.decode_card_value(el.attrs.get("value", ""))
            src = card_data.get("src", "")
            title = card_data.get("detail", {}).get("title", "未获取到超链接显示名")
            elicit_type = card_data.get("detail", {}).get("type", "doc")
            if debug_module.is_debug_enabled():
                debug_module.debug(
                    f"  -> 语雀内联: type={elicit_type} | title={title}", level=4
                )
            if elicit_type.lower() == "doc":
                doc_icon = str(
                    (self.assets / "doc-type-default.svg").absolute().resolve()
                )
                return f"![图标]({doc_icon})[{title}]({src})"
            return f"[{title}]({src})"
        elif card_type == "bookmarkInline":
            card_data = string.decode_card_value(el.attrs.get("value", ""))
            src = card_data.get("src", "")
            title = card_data.get("detail", {}).get("title", "未获取到超链接显示名")
            icon_url = card_data.get("detail", {}).get("icon")
            if debug_module.is_debug_enabled():
                debug_module.debug(
                    f"  -> 书签内联: title={title} | has_icon={bool(icon_url)}",
                    level=4,
                )
            if icon_url:
                return f"![图标]({icon_url})[{title}]({src})"
            return f"[{title}]({src})"
        elif card_type == "imageGallery":
            card_data = string.decode_card_value(el.attrs.get("value", ""))
            image_list = card_data.get("imageList", [])
            if debug_module.is_debug_enabled():
                debug_module.debug(f"  -> 图片画廊: 数量={len(image_list)}", level=4)
            image_gallery = []
            total_width = sum(
                image.get("original", {}).get("width", 0) for image in image_list
            )
            for image in image_list:
                image_title = image.get("title", "图片无标题")
                image_src = image.get("src")
                width = image.get("original", {}).get("width", 0)
                if not width or total_width <= 0:
                    image_gallery.append(f"![图片-{image_title}]({image_src})")
                else:
                    width_percent = int((width / total_width) * 100) - 1
                    image_gallery.append(
                        f'<img src="{image_src}" alt="{image_title}"  width="{width_percent}%"/>'
                    )
            return f"{''.join(image_gallery)}\n"
        elif card_type == "localdoc":
            card_data = string.decode_card_value(el.attrs.get("value", ""))
            src = card_data.get("src", "")
            name = card_data.get("name", "文件")
            if debug_module.is_debug_enabled():
                debug_module.debug(f"  -> 本地文档: name={name} | src={src}", level=4)
            return f"[{name}]({src})\n"
        return ""

    def convert_li(self, el, text, parent_tags):
        """转换 <li> 标签（支持 data-lake-indent）"""
        parent = el.parent

        # 获取缩进
        indent = 0
        if parent and parent.name in ("ul", "ol"):
            if "data-lake-indent" in parent.attrs:
                indent = int(parent.attrs["data-lake-indent"])

        prefix = "\t" * indent

        if debug_module.is_debug_enabled():
            debug_module.debug(f"转换列表项: indent={indent}", level=3)

        # 有序列表
        if parent is not None and parent.name == "ol":
            start = 1
            start_attr = parent.get("start")
            if start_attr and str(start_attr).isnumeric():
                start = int(start_attr)
            bullet = f"{start + parent.index(el)}."
        else:
            # 无序列表 - 根据嵌套深度选择符号
            depth = -1
            current = el
            while current:
                if current.name == "ul":
                    depth += 1
                current = current.parent
            # 使用 getattr 避免 Pylance 类型检查错误
            # type: ignore[attr-defined]
            options = getattr(self._ht2md_converter, "options", None)  # type: ignore[attr-defined]
            bullets = options.bullets if options else "*+-"  # type: ignore[attr-defined]
            bullet = bullets[depth % len(bullets)]

        return f'{prefix}{bullet} {(text or "").strip()}\n'

    def create_bs4soup(self) -> BeautifulSoup:
        """
        创建 soup 对象（导入、加工、返回）
        合并基础版本和重写版本，添加合并相邻 em/strong 标签的逻辑

        :return: BeautifulSoup 对象
        """
        debug_module.debug_section("创建 BeautifulSoup 对象")

        raw_data = self.raw_html.replace("\n", "").replace("\r", "").strip()
        debug_module.debug(f"原始 HTML 长度: {len(self.raw_html)} 字符", level=1)
        debug_module.debug(f"处理后 HTML 长度: {len(raw_data)} 字符", level=1)
        debug_module.debug(f"使用解析器: {self.bs4_builder}", level=1)

        try:
            soup = BeautifulSoup(raw_data, self.bs4_builder)
            debug_module.debug(f"BeautifulSoup 对象创建成功", level=1, color="green")
        except FeatureNotFound:
            debug_module.debug(
                f"解析器 {self.bs4_builder} 未找到", level=1, color="red"
            )
            raise errors.LakeBuilderNotFoundError(self.bs4_builder)

        debug_module.debug_subsection("合并相邻标签", level=1)

        # feature: 合并相邻的 em 标签，防止转换后出现 *ab**cd* 这种难以解析的 md 语法
        em_count = 0
        merged_em_count = 0
        for em_tag in soup.find_all("em"):
            em_count += 1
            next_sibling = em_tag.find_next_sibling()
            # 如果存在相邻<em>标签
            while next_sibling and next_sibling.name == "em":
                # 将其子元素拓展到到第1个<em>标签中
                em_tag.extend(next_sibling.contents)
                next_sibling.extract()
                next_sibling = em_tag.find_next_sibling()
                merged_em_count += 1

        strong_count = 0
        merged_strong_count = 0
        for strong_tag in soup.find_all("strong"):
            strong_count += 1
            next_sibling = strong_tag.find_next_sibling()
            while next_sibling and next_sibling.name == "strong":
                strong_tag.extend(next_sibling.contents)
                next_sibling.extract()
                next_sibling = strong_tag.find_next_sibling()
                merged_strong_count += 1

        debug_module.debug(
            f"em 标签总数: {em_count} | 合并数: {merged_em_count}", level=2
        )
        debug_module.debug(
            f"strong 标签总数: {strong_count} | 合并数: {merged_strong_count}", level=2
        )

        return soup

    def add_title(self, data: str):
        """
        如果传入的数据不是 None，那么将其添加到转换内容顶部（支持 md 语法）
        :param data: title 顶行数据（一般是文档的标题名称）
        :return: 处理好的 Markdown 内容
        """
        debug_module.debug_subsection("添加标题", level=1)

        if self.title is not None:
            debug_module.debug(f"添加标题: {self.title}", level=2)
            if data.startswith("\n\n"):
                data = f"{self.title}{data[1:]}"
            else:
                data = f"{self.title}\n{data}"
        else:
            debug_module.debug("无标题", level=2)
            if data.startswith("\n\n"):
                data = data[1:]

        return data
