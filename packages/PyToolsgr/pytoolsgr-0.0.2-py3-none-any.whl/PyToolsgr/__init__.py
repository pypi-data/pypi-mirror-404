from ursina import *
import os
import time
import datetime

class PyToolsgr:
    """PyToolsgr游戏工具类，基于ursina实现"""
    
    # 日志相关属性
    _log_file = None
    _last_log_time = 0
    _log_interval = 10 * 60  # 10分钟
    
    @staticmethod
    def _get_log_file():
        """获取当前日志文件，每10分钟新建一个"""
        current_time = time.time()
        
        # 检查是否需要新建日志文件
        if PyToolsgr._log_file is None or (current_time - PyToolsgr._last_log_time) >= PyToolsgr._log_interval:
            # 创建log目录
            log_dir = os.path.join(os.path.dirname(__file__), 'log')
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # 生成日志文件名
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            log_file_path = os.path.join(log_dir, f'log_{timestamp}.txt')
            
            # 关闭旧的日志文件
            if PyToolsgr._log_file:
                PyToolsgr._log_file.close()
            
            # 打开新的日志文件
            PyToolsgr._log_file = open(log_file_path, 'a', encoding='utf-8')
            PyToolsgr._last_log_time = current_time
            
            # 写入日志头
            PyToolsgr._log(f"=== 日志文件创建: {timestamp} ===", level="INFO")
        
        return PyToolsgr._log_file
    
    @staticmethod
    def _log(message, level="INFO"):
        """写入日志
        
        Args:
            message: 日志消息
            level: 日志级别
        """
        log_file = PyToolsgr._get_log_file()
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        # 写入日志文件
        log_file.write(log_entry)
        log_file.flush()  # 立即写入
        
        # 同时输出到控制台
        print(log_entry.rstrip())
    
    @staticmethod
    def OS(os_type):
        """设置操作系统类型
        
        Args:
            os_type: 操作系统类型，可选值：'Windows', 'MacOS', 'Linux'
        """
        PyToolsgr._log(f"设置操作系统: {os_type}")
        # Ursina会自动检测操作系统，这里仅做记录
    
    @staticmethod
    def game(resolution, fullscreen, title, resizable, fps_limit, show_fps, physics, mode):
        """创建游戏窗口
        
        Args:
            resolution: 分辨率数组，如 (1080, 720)
            fullscreen: 是否全屏
            title: 窗口标题
            resizable: 是否可以调整窗口大小
            fps_limit: 最大帧率
            show_fps: 是否显示帧率
            physics: 是否开启物理引擎
            mode: 2d或3d
        
        Returns:
            Ursina实例
        """
        # 创建游戏实例
        app = Ursina()
        
        # 设置窗口参数
        window.size = resolution
        window.fullscreen = fullscreen
        window.title = title
        window.resizable = resizable
        window.fps_limit = fps_limit
        window.show_fps = show_fps
        
        # 设置2d或3d模式
        if mode == '2d':
            camera.orthographic = True
            camera.fov = 10
        else:  # 3d
            camera.orthographic = False
            camera.fov = 90
        
        # 物理引擎设置（Ursina默认使用内置物理）
        if physics:
            PyToolsgr._log("物理引擎已启用")
        
        return app
    
    @staticmethod
    def beijing(color):
        """设置背景颜色
        
        Args:
            color: 背景颜色，如 (0, 0, 0) 黑色
        """
        camera.clear_color = color
        PyToolsgr._log(f"设置背景颜色: {color}")
    
    @staticmethod
    def New(obj_type, size, *args, **kwargs):
        """创建游戏对象
        
        Args:
            obj_type: 对象类型，可选值：'Block', 'PNG', 'Text', 'Player'
            size: 对象大小，如 (100, 100)
            *args: 其他参数
            **kwargs: 关键字参数
        
        Returns:
            创建的游戏对象
        """
        # 处理参数
        position = kwargs.get('position', (0, 0))
        obj_color = kwargs.get('color', color.white)
        texture = kwargs.get('texture', None)
        text = kwargs.get('text', '')
        font_size = kwargs.get('font_size', 20)
        phy_size = kwargs.get('phy_', None)
        
        # 创建不同类型的对象
        if obj_type == 'Block':
            obj = Entity(
                model='quad',
                texture='white_cube',
                color=obj_color,
                position=position,
                scale=(size[0]/100, size[1]/100)
            )
            if phy_size:
                obj.collider = 'box'
        
        elif obj_type == 'PNG':
            obj = Entity(
                model='quad',
                texture=texture if texture else 'white_cube',
                position=position,
                scale=(size[0]/100, size[1]/100)
            )
        
        elif obj_type == 'Text':
            obj = Text(
                text=text,
                position=position,
                scale=(size[0]/100, size[1]/100),
                font_size=font_size
            )
        
        elif obj_type == 'Player':
            obj = Entity(
                model='quad',
                texture=texture if texture else 'white_cube',
                position=position,
                scale=(size[0]/100, size[1]/100),
                collider='box'
            )
        
        else:
            PyToolsgr._log(f"未知对象类型: {obj_type}", level="ERROR")
            return None
        
        PyToolsgr._log(f"创建对象: {obj_type}, 大小: {size}, 位置: {position}")
        return obj
    
    @staticmethod
    def look(obj):
        """显示对象
        
        Args:
            obj: 要显示的对象
        """
        if obj:
            obj.visible = True
            PyToolsgr._log(f"显示对象: {obj}")
    
    @staticmethod
    def look_n(obj):
        """隐藏对象
        
        Args:
            obj: 要隐藏的对象
        """
        if obj:
            obj.visible = False
            PyToolsgr._log(f"隐藏对象: {obj}")
    
    @staticmethod
    def look_a(obj_list):
        """显示多个对象
        
        Args:
            obj_list: 要显示的对象列表
        """
        for obj in obj_list:
            PyToolsgr.look(obj)
    
    @staticmethod
    def look_n_a(obj_list):
        """隐藏多个对象
        
        Args:
            obj_list: 要隐藏的对象列表
        """
        for obj in obj_list:
            PyToolsgr.look_n(obj)
    
    @staticmethod
    def set_pos(obj, position):
        """设置对象位置
        
        Args:
            obj: 要设置位置的对象
            position: 新位置，如 (100, 100)
        """
        if obj:
            obj.position = (position[0]/100, position[1]/100)
            PyToolsgr._log(f"设置对象位置: {obj} -> {position}")
    
    @staticmethod
    def set_pos_a(obj_list, position):
        """设置多个对象位置
        
        Args:
            obj_list: 要设置位置的对象列表
            position: 新位置，如 (100, 100)
        """
        for obj in obj_list:
            PyToolsgr.set_pos(obj, position)

# 版本信息
__version__ = '0.0.2'
__author__ = 'l-love-china'
__license__ = 'MIT'

# 导出类
__all__ = ['PyToolsgr']