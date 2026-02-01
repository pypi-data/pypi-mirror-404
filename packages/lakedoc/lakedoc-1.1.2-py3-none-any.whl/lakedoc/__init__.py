"""**Welcome To LakeDoc**

(*^▽^*) `Open source is limited, but thinking is limitless.`

Convert Lake documents (Yuque) into specified format (currently supports md files).
Able to adapt to most Lake documents.

**Author Info:**
  - **Name:** gupingan(顾平安)
  - **Email:** gupingan6@outlook.com

**License:** MIT

**Quick Start:**

```python
import lakedoc

# 从文件转换并返回结果
result = lakedoc.convert('./input.html')

# 从文件转换并保存
lakedoc.convert('./input.html', saveto='./output.md')

# 从 HTML 内容转换（自动识别包含 <!doctype lake> 的内容）
result = lakedoc.convert('<!doctype lake><html>...</html>')

# 转换内容并保存
lakedoc.convert('<!doctype lake><html>...</html>', saveto='./output.md')

# 添加标题
lakedoc.convert('./input.html', saveto='./output.md', title='# 我的文档')

# 自定义转换器
lakedoc.convert('./input.html', converter='custom')
```

**Debug API:**

```python
import lakedoc

# 启用全局调试模式
lakedoc.enable_debug()

# 禁用全局调试模式
lakedoc.disable_debug()

# 输出调试信息
lakedoc.debug("这是一条调试信息")

# 输出带缩进和颜色的调试信息
lakedoc.debug("这是一条调试信息", level=2, color='red')
```

**Advanced Usage:**

```python
# 继承基类直接注册转换器
from lakedoc import LakeBaseConverter

class PDFConverter(LakeBaseConverter):
    name = "pdf"  # 转换器名称，自动注册，强制字段
    suffix = ".pdf"  # 转换器后缀，强制字段

    def convert(self):
        # 实现你的转换逻辑
        return "converted content"

# 使用 PDF 转换器
lakedoc.convert("...", converter="pdf")
```
"""

__version__ = "1.1.2"
__author__ = "gupingan"

from .context.mod import convert

# 转换器
from .converters import LakeBaseConverter, MarkdownConverter
from .converters.ht2md import (
    HeadingStyle,
    NewlineStyle,
    StrongEmSymbol,
    StripMode,
)

# 工具模块
from .utils import file, string, errors

# 调试模块
from .utils.debug import (
    enable_debug,
    disable_debug,
    debug,
    debug_section,
    debug_subsection,
    is_debug_enabled,
)

__all__ = [
    "convert",
    "LakeBaseConverter",
    "MarkdownConverter",
    "file",
    "string",
    "errors",
    "enable_debug",
    "disable_debug",
    "debug",
    "debug_section",
    "debug_subsection",
    "is_debug_enabled",
    "HeadingStyle",
    "NewlineStyle",
    "StrongEmSymbol",
    "StripMode",
]
