# Python Special Heatmap

#### 介绍
基于 MATLAB 版 [special heatmap](https://github.com/slandarer/matlab-special-heatmap) 的 Python 复现。本项目使用 `matplotlib` 实现具有多种形状（正方形、圆形、六边形、饼图等）和三角矩阵布局的高级热图绘制。

### 1 基础使用 (Basic use)

#### 1.1 绘制正数热图 (Draw positive heat map)

```python
import numpy as np
import matplotlib.pyplot as plt
from special_heatmap import SHeatmap

data = np.random.rand(15, 15)
shm = SHeatmap(data, fmt='sq')
shm.draw()
plt.show()
```

#### 1.2 绘制含负数热图 (Contains negative numbers)
```python
data = np.random.rand(15, 15) - 0.5
shm = SHeatmap(data, fmt='sq')
shm.draw()
plt.show()
```

#### 1.3 绘制有文本和 NaN 的热图 (Draw heat map with texts and NaN)

```python
data = np.random.rand(12, 12) - 0.5
data[3, 3] = np.nan
shm = SHeatmap(data, fmt='sq')
shm.draw()
shm.set_text()
plt.show()
```

### 2 各类型热图绘制 (Various Formats)

支持的格式 (`fmt` 参数):
- `sq`    : 正方形 (默认)
- `pie`   : 饼图
- `circ`  : 圆形
- `oval`  : 椭圆形
- `hex`   : 六边形
- `asq`   : 自动调整大小的正方形
- `acirc` : 自动调整大小的圆形

```python
shm = SHeatmap(data, fmt='pie')
shm.draw()
```

### 3 设置为上三角或下三角 (Triangular Layouts)

支持以下布局类型 (`set_type` 方法):
- `triu`   : 上三角部分
- `tril`   : 下三角部分
- `triu0`  : 不含对角线的上三角部分
- `tril0`  : 不含对角线的下三角部分

```python
data = np.random.rand(12, 12)
shm = SHeatmap(data, fmt='sq')
shm.set_type('tril')
shm.draw()
shm.set_text()
plt.show()
```

### 4 安装与运行

本项目使用 `uv` 进行环境管理。

```bash
# 克隆仓库后进入目录
cd python_reproduction

# 创建虚拟环境并安装依赖
uv sync

# 运行演示脚本
uv run demo_basic.py
```

### 已实现功能
- [x] 基础形状绘制 (sq, pie, circ, oval, hex, asq, acirc)
- [x] 自动颜色映射 (Sequential & Diverging)
- [x] NaN 值特殊渲染 (灰块 + '×')
- [x] 数值文本标注
- [x] 上下三角矩阵显示

---
*Original MATLAB project by [slandarer](https://github.com/slandarer)*