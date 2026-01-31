# Python Special Heatmap

[![PyPI version](https://badge.fury.io/py/special-heatmap.svg)](https://badge.fury.io/py/special-heatmap)
[![License: GPL v2](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)

> **Disclaimer**: This project was implemented with the assistance of AI (Google Gemini).  
> **声明**：本项目代码由 AI (Google Gemini) 辅助生成。

#### 介绍 / Introduction
A Python reproduction of the MATLAB [special heatmap](https://github.com/slandarer/matlab-special-heatmap) project. It uses `matplotlib` to draw advanced heatmaps with various shapes (square, circle, hexagon, pie, etc.) and triangular layouts.

基于 MATLAB 版 [special heatmap](https://github.com/slandarer/matlab-special-heatmap) 的 Python 复现。本项目使用 `matplotlib` 实现具有多种形状（正方形、圆形、六边形、饼图等）和三角矩阵布局的高级热图绘制。

### 1. 安装 / Installation

```bash
pip install special-heatmap
```

### 2. 基础使用 / Basic Use

#### 2.1 绘制非负矩阵热图 (Draw positive heat map)
```python
import numpy as np
import matplotlib.pyplot as plt
from special_heatmap import SHeatmap

data = np.random.rand(15, 15)
shm = SHeatmap(data, fmt='sq')
shm.draw()
plt.show()
```
![Basic Positive](gallery/Basic_positive.png)

#### 2.2 绘制含负数热图 (Contains negative numbers)
```python
data = np.random.rand(15, 15) - 0.5
shm = SHeatmap(data, fmt='sq')
shm.draw()
plt.show()
```
![Basic Negative](gallery/Basic_negative.png)

#### 2.3 绘制有文本和 NaN 的热图 (Draw heat map with texts and NaN)
```python
data = np.random.rand(12, 12) - 0.5
data[3, 3] = np.nan
shm = SHeatmap(data, fmt='sq')
shm.draw()
shm.set_text(fontsize=8)
plt.show()
```
![Basic with Text](gallery/Basic_with_text.png)

### 3. 各类型热图 / Various Formats

支持的格式 (`fmt` 参数): `sq` (Default), `pie`, `circ`, `oval`, `hex`, `asq`, `acirc`.

```python
# 示例：绘制饼图格式
shm = SHeatmap(data, fmt='pie')
shm.draw()
```

| Format | Positive Data (A) | Mixed Data (B) |
| :---: | :---: | :---: |
| **sq** (Square) | ![sq A](gallery/Format_sq_A.png) | ![sq B](gallery/Format_sq_B.png) |
| **pie** (Pie Chart) | ![pie A](gallery/Format_pie_A.png) | ![pie B](gallery/Format_pie_B.png) |
| **circ** (Circle) | ![circ A](gallery/Format_circ_A.png) | ![circ B](gallery/Format_circ_B.png) |
| **hex** (Hexagon) | ![hex A](gallery/Format_hex_A.png) | ![hex B](gallery/Format_hex_B.png) |
| **oval** (Oval) | ![oval A](gallery/Format_oval_A.png) | ![oval B](gallery/Format_oval_B.png) |
| **asq** (Auto-Square) | ![asq A](gallery/Format_asq_A.png) | ![asq B](gallery/Format_asq_B.png) |
| **acirc** (Auto-Circle) | ![acirc A](gallery/Format_acirc_A.png) | ![acirc B](gallery/Format_acirc_B.png) |

### 4. 三角布局 / Triangular Layouts

支持以下布局类型 (`set_type` 方法):
- `triu`   : 上三角 (Upper Triangle)
- `tril`   : 下三角 (Lower Triangle)
- `triu0`  : 上三角无对角线 (Upper without Diagonal)
- `tril0`  : 下三角无对角线 (Lower without Diagonal)

```python
data = np.random.rand(12, 12)
shm = SHeatmap(data, fmt='sq')
shm.set_type('tril') # 设置为下三角
shm.draw()
shm.set_text()
plt.show()
```

| Type | Result |
| :---: | :---: |
| **triu** | ![triu](gallery/Type_triu.png) |
| **tril** | ![tril](gallery/Type_tril.png) |
| **triu0** | ![triu0](gallery/Type_triu0.png) |
| **tril0** | ![tril0](gallery/Type_tril0.png) |

### 5. 开源协议 / License

本项目采用 **GPL v2** 开源协议。详细内容请参阅 [LICENSE](LICENSE) 文件。
This project is licensed under the **GPL v2 License**. See the [LICENSE](LICENSE) file for details.

---
*Original MATLAB project by [slandarer](https://github.com/slandarer)*