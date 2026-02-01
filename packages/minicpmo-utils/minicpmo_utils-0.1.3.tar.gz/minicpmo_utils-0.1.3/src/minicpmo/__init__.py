"""MiniCPM-o 顶层工具包 `minicpmo`。

这个包聚合了语音 / 音频相关子包，并预留统一的 utils 入口：

- 顶层子包：
  - cosyvoice
  - stepaudio2
  - matcha
  - s3tokenizer
- 工具入口：
  - from minicpmo.utils import ...
"""

from .version import __version__

# Eager re-exports to allow:
#   from minicpmo import cosyvoice, stepaudio2, matcha
# 而不需要懒加载。
# import cosyvoice as cosyvoice
# import stepaudio2 as stepaudio2
# import matcha as matcha

# __all__ = ["__version__", "cosyvoice", "stepaudio2", "matcha"]

