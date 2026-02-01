from pathlib import Path
from typing import Any
from lakedoc.utils import errors, file
from lakedoc.converters.base import _converter_registry
from .base import LakeBaseContext


class LakeContext(LakeBaseContext):
    def __init__(self):
        self.options = {}
        self.converter_classes: dict = dict()
        self.converter_class = None
        
        # 从全局注册表中注册所有转换器
        self._register_from_registry()
    
    def _register_from_registry(self):
        """
        从全局转换器注册表中注册所有转换器
        """
        for name, converter_class in _converter_registry.items():
            self.register(name, converter_class, is_cover=False)

    def set_options(self, **options):
        self.options = {}
        self.options.update(options)

    def pick(self, converter: str):
        """
        为当前上下文挑选指定的转换器类，该类将设置为属性 `converter_class` 的值
        :param converter: 转换器对应的类型标签
        """
        if not isinstance(converter, str):
            raise errors.LakeContentTypeError(
                "参数 converter", "str", str(type(converter))
            )
        
        if converter not in self.converter_classes:
            raise errors.LakePickNotFoundError(converter)

        self.converter_class = self.converter_classes[converter]
        return self.converter_class

    def convert_content(self, html: str, converter: str = "markdown") -> Any:
        """将 HTML 内容通过指定的转换器转换为对应的内容"""
        if not html.strip():
            raise errors.LakeSourceEmptyError

        self.converter_class = self.pick(converter)

        return self.converter_class(html, **self.options).convert()

    def convert_content_save(
        self,
        html: str,
        save_path=None,
        converter: str = "markdown",
        encoding: str = "utf-8",
    ):
        """将 HTML 内容通过指定的转换器转换为对应的内容并保存"""
        data = self.convert_content(html, converter)
        save_path = save_path or Path("./")
        # 从转换器类获取 suffix
        converter_class = self.converter_classes.get(converter)
        suffix = getattr(converter_class, 'suffix', '.md') if converter_class else '.md'
        file.savefile(data, save_path, encoding, suffix)
        return data

    def convert_file(
        self,
        read_path,
        converter: str = "markdown",
        encoding: str = "utf-8",
    ):
        """从 HTML 文件路径中读取内容并转换"""
        html = file.readfile(read_path, encoding=encoding)
        return self.convert_content(html, converter)

    def convert_file_save(
        self,
        read_path,
        save_path=None,
        converter: str = "markdown",
        encoding: str = "utf-8",
    ):
        """从 HTML 文件路径中读取内容，通过转换后，保存到指定的路径"""
        data = self.convert_file(read_path, converter, encoding)
        save_path = save_path or Path("./")
        # 从转换器类获取 suffix
        converter_class = self.converter_classes.get(converter)
        suffix = getattr(converter_class, 'suffix', '.md') if converter_class else '.md'
        file.savefile(data, save_path, encoding, suffix)
        return data

    def register(
        self,
        converter: str,
        converter_class,
        is_cover: bool = True,
    ):
        """
        注册外部的转换器
        :param converter: 转换器类对应的类型标签，用于查找转换器类（pick/convert）
        :param converter_class: 外部的转换器类（继承于 LakeBaseConverter）
        :param is_cover: 开启后，类型标签一致的旧转换器类将直接被覆盖，默认开启
        """
        if not isinstance(converter, str):
            raise errors.LakeContentTypeError(
                "参数 converter", "str", str(type(converter))
            )

        if is_cover:
            self.converter_classes[converter] = converter_class
        else:
            self.converter_classes.setdefault(converter, converter_class)
