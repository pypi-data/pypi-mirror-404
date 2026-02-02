# PyToolsgr - 2D/3D Game Engine based on Ursina

PyToolsgr是一个基于Ursina的轻量级2/3D游戏引擎，旨在简化游戏开发流程，提供直观的API和丰富的功能。

## 特性

- 🎮 简单易用的2D/3D游戏开发API
- 🚀 基于Ursina引擎，继承其高性能和灵活性
- 📦 开箱即用的游戏对象和组件系统
- 🎨 内置精灵、动画、粒子效果支持
- 🎯 碰撞检测和物理系统
- 🎵 音频管理
- 📱 跨平台支持（Windows, MacOS, Linux）
- 📖 详细的文档和示例

## 安装

通过pip安装PyToolsgr：

```bash
pip install PyToolsgr
```

## 快速开始

### 创建窗口

```python
from PyToolsgr import PyToolsgr

# 设置操作系统
PyToolsgr.OS('Windows')

# 窗口参数
resolution = (1080, 720)  # 窗口大小
fullscreen = False      # 是否全屏
title = 'PyToolsgr'     # 窗口标题
resizable = True        # 是否可以调整窗口大小
fps_limit = 60          # 最大帧率
show_fps = True         # 是否显示帧率
physics = True          # 是否开启物理引擎
mode = '2d'             # 2d或3d

# 创建游戏窗口
game = PyToolsgr.game(
    resolution=resolution,
    fullscreen=fullscreen,
    title=title,
    resizable=resizable,
    fps_limit=fps_limit,
    show_fps=show_fps,
    physics=physics,
    mode=mode
)

# 运行游戏
game.run()
```

## 核心概念
 - 有2个模式
 - 复杂模式:可以有更强的功能但是更难
 - 极简模式:新手能轻松上手不需要看复杂的文档
### 游戏对象
"player" 玩家
"NPC" 游戏NPC
“block”方块，一个基本单位，不一定是正方形
"PNG" PNG 的贴图

## 帮助文档

### 创建窗口

```python
PyToolsgr.OS(OS) # Windows , MacOS , Linux

game = PyToolsgr.game(分辨率数组,是否全屏,窗口标题,是否可以调整窗口大小,最大帧率,是否显示帧率,是否开启物理引擎,2d或3d)
```

**示例代码：**

```python
from PyToolsgr import *
PyToolsgr.OS('Windows') # 或MacOS , Linux

x = (1080,720) # 窗口大小
all = True # 是否全屏
title = 'PyToolsgr' # 窗口标题
y = True # 是否可以调整窗口大小
fps = 60 # 最大帧率
fpsx = True # 是否显示帧率
phy = True # 是否开启物理引擎
mode = '2d' # 2d或3d

game = PyToolsgr.game(x,all,title,y,fps,fpsx,phy,mode)  

game.run()
```
## 许可证

cfk 使用 MIT 许可证，详情请查看 [LICENSE](LICENSE) 文件。

## 鸣谢

- [Ursina](https://www.ursinaengine.org/) - 基础游戏引擎
- [Python](https://www.python.org/) - 编程语言

## 联系方式

- 项目主页: [https://github.com/l-love-china/PyToolsgr](https://github.com/l-love-china/PyToolsgr)
- PyPI: [https://pypi.org/project/PyToolsgr/](https://pypi.org/project/PyToolsgr/)