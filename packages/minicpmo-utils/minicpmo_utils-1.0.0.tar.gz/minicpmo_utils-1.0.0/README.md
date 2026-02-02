## minicpmo-utils

一个统一安装的工具包（一个 PyPI 分发包），把仓库里的 `cosyvoice` 与 `stepaudio2` 一起打进同一个 wheel，并预留 `minicpmo` 作为后续扩展 utils 的统一入口。

### 安装方式

- 从源码本地安装（开发态，可编辑，默认只装公共依赖）：
```bash
cd minicpmo-utils
pip install -e .
```

- 如果只想安装 cosyvoice 相关依赖（TTS）：
```bash
pip install -e .[tts]
```

- 如果只想安装 stepaudio2 / streaming 相关依赖：
```bash
pip install -e .[streaming]
```

- 同时安装 cosyvoice + stepaudio2 相关依赖：
```bash
pip install -e .[tts,streaming]
```

- 构建并安装 wheel（推荐分发）：
```bash
cd minicpmo-utils
python -m build        # 生成 dist/*.whl
pip install \"dist/minicpmo_utils-0.1.0-py3-none-any.whl[tts,streaming]\"
```

### 导入方式

包会暴露以下顶层模块，安装后可直接使用：
- `import cosyvoice`
- `import stepaudio2`
- `import matcha`
- `import minicpmo`

也支持通过统一入口导入子包：
```python
from minicpmo import cosyvoice, stepaudio2, matcha
```

以及通过统一的 utils 入口使用通用工具函数，例如：

```python
from minicpmo.utils import get_video_frame_audio_segments
```

