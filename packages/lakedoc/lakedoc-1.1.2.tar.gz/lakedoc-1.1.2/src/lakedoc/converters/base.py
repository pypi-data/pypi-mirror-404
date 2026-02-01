from typing import Optional, Dict


# 全局转换器注册表，用于存储尚未注册到上下文的转换器
_converter_registry: Dict[str, type] = {}


class LakeBaseConverter(object):
    """
    转换器基类，提供通用的转换器注册功能
    """

    # 转换器名称
    name: Optional[str] = None

    # 转换器后缀
    suffix: Optional[str] = None

    def __init_subclass__(cls, **kwargs):
        """
        子类化时自动注册转换器
        """
        super().__init_subclass__(**kwargs)

        # 只有在定义了 name 和 suffix 时才自动注册
        if hasattr(cls, "name") and hasattr(cls, "suffix") and cls.name and cls.suffix:
            # 先注册到全局注册表
            _converter_registry[cls.name] = cls

            # 尝试注册到上下文（如果上下文已初始化）
            try:
                from lakedoc.context import get_context

                ctx = get_context()
                ctx.register(cls.name, cls, is_cover=False)
            except (ImportError, AttributeError):
                # 如果上下文尚未初始化，跳过注册
                # 转换器将在上下文初始化时从注册表中注册
                pass

    def __repr__(self):
        return f"<{self.__class__.__name__}: name={self.name}>"

    def convert(self):
        """执行转换，子类必须实现此方法"""
        raise NotImplementedError
