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

### 1. 创建窗口

```python
PyToolsgr.OS(OS) # Windows , MacOS , Linux

game = PyToolsgr.game(分辨率数组,是否全屏,窗口标题,是否可以调整窗口大小,最大帧率,是否显示帧率,是否开启物理引擎,2d或3d)
```

### 2. 设置背景颜色

```python
PyToolsgr.beijing((0,0,0)) # 背景颜色，如黑色
```

### 3. 创建游戏对象

```python
# 创建方块
b1 = PyToolsgr.New("Block",(100,100),position=(0,0),color=color.red,phy_=(100,100))

# 创建PNG
png1 = PyToolsgr.New("PNG",(100,100),position=(1,0),texture="image.png")

# 创建文本
t1 = PyToolsgr.New("Text",(100,100),position=(0,1),text="Hello World",font_size=30)

# 创建玩家
p1 = PyToolsgr.New("Player",(100,100),position=(-1,0),texture="player.png")
```

### 4. 显示/隐藏对象

```python
PyToolsgr.look(p1) # 显示单个对象
PyToolsgr.look_n(p1) # 隐藏单个对象
PyToolsgr.look_a([p1,b1]) # 显示多个对象
PyToolsgr.look_n_a([p1,b1]) # 隐藏多个对象
```

### 5. 设置对象位置

```python
PyToolsgr.set_pos(p1,(100,100)) # 设置单个对象位置
PyToolsgr.set_pos_a([p1,b1],(100,100)) # 设置多个对象位置
```

**完整示例代码：**

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

PyToolsgr.beijing((0,0,0)) # 背景颜色

b1 = PyToolsgr.New("Block",(100,100),position=(0,0),color=color.red,phy_=(100,100))
png1 = PyToolsgr.New("PNG",(100,100),position=(1,0))
t1 = PyToolsgr.New("Text",(100,100),position=(0,1),text="Hello World",font_size=30)
p1 = PyToolsgr.New("Player",(100,100),position=(-1,0),texture="white_cube")

PyToolsgr.look(p1) # 显示
PyToolsgr.look_n(p1) # 隐藏
PyToolsgr.look_a([p1,b1]) # 显示多个对象
PyToolsgr.look_n_a([p1,b1]) # 隐藏多个对象
PyToolsgr.set_pos(p1,(100,100)) # 设置位置
PyToolsgr.set_pos_a([p1,b1],(200,200)) # 设置多个对象位置

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