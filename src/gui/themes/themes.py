# -*- coding: utf-8 -*-
"""
主题管理器
实现亮色/暗色主题切换功能
"""

import wx
from typing import Dict, Tuple, Any


class ThemeManager:
    """主题管理器，统一管理界面颜色方案"""

    # 主题定义
    THEMES = {
        'light': {
            # 基础颜色
            'bg_primary': '#FFFFFF',           # 主背景
            'bg_secondary': '#F5F5F5',         # 次背景
            'bg_accent': '#E1F0FF',            # 强调背景
            'fg_primary': '#333333',           # 主文字
            'fg_secondary': '#666666',        # 次文字
            'fg_disabled': '#999999',         # 禁用文字
            
            # 主题色 - Office蓝
            'primary': '#0078D7',              # 主色
            'primary_light': '#106EBE',        # 浅主色
            'primary_dark': '#005A9E',         # 深主色
            'primary_hover': '#0063B1',        # 悬停色
            
            # 功能色
            'success': '#107C10',              # 成功
            'error': '#D13438',                # 错误
            'warning': '#FFA500',              # 警告
            'info': '#0078D7',                 # 信息
            
            # 边框颜色
            'border': '#E0E0E0',              # 普通边框
            'border_focus': '#0078D7',        # 焦点边框
            'border_light': '#F0F0F0',        # 浅边框
            
            # 控件颜色
            'button_bg': '#0078D7',            # 按钮背景
            'button_fg': '#FFFFFF',            # 按钮文字
            'button_hover': '#106EBE',        # 按钮悬停
            'input_bg': '#FFFFFF',            # 输入框背景
            'input_fg': '#333333',            # 输入框文字
            'panel_bg': '#FFFFFF',             # 面板背景
            'statusbar_bg': '#F0F0F0',        # 状态栏背景
        },
        'dark': {
            # 基础颜色
            'bg_primary': '#2D2D30',           # 主背景
            'bg_secondary': '#3E3E42',         # 次背景
            'bg_accent': '#1E3A5F',            # 强调背景
            'fg_primary': '#FFFFFF',           # 主文字
            'fg_secondary': '#CCCCCC',         # 次文字
            'fg_disabled': '#888888',          # 禁用文字
            
            # 主题色 - 深色模式蓝
            'primary': '#60CDFF',             # 主色
            'primary_light': '#4AB8F0',        # 浅主色
            'primary_dark': '#37A2D8',        # 深主色
            'primary_hover': '#7FE0FF',        # 悬停色
            
            # 功能色
            'success': '#3CCF3C',             # 成功
            'error': '#FF5A5F',               # 错误
            'warning': '#FFB800',              # 警告
            'info': '#60CDFF',                # 信息
            
            # 边框颜色
            'border': '#4A4A4C',              # 普通边框
            'border_focus': '#60CDFF',        # 焦点边框
            'border_light': '#3E3E42',        # 浅边框
            
            # 控件颜色
            'button_bg': '#60CDFF',            # 按钮背景
            'button_fg': '#2D2D30',            # 按钮文字
            'button_hover': '#7FE0FF',        # 按钮悬停
            'input_bg': '#3E3E42',            # 输入框背景
            'input_fg': '#FFFFFF',            # 输入框文字
            'panel_bg': '#2D2D30',             # 面板背景
            'statusbar_bg': '#007ACC',        # 状态栏背景
        }
    }

    # 当前主题
    _current_theme = 'light'

    @classmethod
    def set_theme(cls, theme_name: str) -> None:
        """设置当前主题"""
        if theme_name in cls.THEMES:
            cls._current_theme = theme_name

    @classmethod
    def get_current_theme(cls) -> str:
        """获取当前主题名称"""
        return cls._current_theme

    @classmethod
    def get_color(cls, color_key: str, theme_name: str = None) -> wx.Colour:
        """
        获取主题颜色
        
        Args:
            color_key: 颜色键名
            theme_name: 主题名称，默认使用当前主题
            
        Returns:
            wx.Colour对象
        """
        if theme_name is None:
            theme_name = cls._current_theme
        
        if theme_name not in cls.THEMES:
            theme_name = 'light'
        
        color_hex = cls.THEMES[theme_name].get(color_key, '#000000')
        return wx.Colour(color_hex)

    @classmethod
    def apply_theme_to_window(cls, window: wx.Window, theme_name: str = None) -> None:
        """
        应用主题到窗口
        
        Args:
            window: wx.Window对象
            theme_name: 主题名称，默认使用当前主题
        """
        if theme_name is None:
            theme_name = cls._current_theme
        
        colors = cls.THEMES[theme_name]
        
        # 设置背景色
        window.SetBackgroundColour(wx.Colour(colors['bg_primary']))
        window.SetForegroundColour(wx.Colour(colors['fg_primary']))
        
        # 递归应用到子窗口
        for child in window.GetChildren():
            cls.apply_theme_to_control(child, theme_name)
        
        window.Refresh()

    @classmethod
    def apply_theme_to_control(cls, control: wx.Window, theme_name: str) -> None:
        """应用主题到单个控件"""
        colors = cls.THEMES[theme_name]
        
        # 根据控件类型设置不同颜色
        if isinstance(control, wx.Button):
            control.SetBackgroundColour(wx.Colour(colors['button_bg']))
            control.SetForegroundColour(wx.Colour(colors['button_fg']))
        elif isinstance(control, (wx.TextCtrl, wx.ComboBox)):
            control.SetBackgroundColour(wx.Colour(colors['input_bg']))
            control.SetForegroundColour(wx.Colour(colors['input_fg']))
        elif isinstance(control, (wx.Panel, wx.StaticBox)):
            control.SetBackgroundColour(wx.Colour(colors['panel_bg']))
            control.SetForegroundColour(wx.Colour(colors['fg_primary']))
        elif isinstance(control, wx.StaticText):
            control.SetBackgroundColour(wx.Colour(colors['bg_primary']))
            control.SetForegroundColour(wx.Colour(colors['fg_secondary']))
        elif isinstance(control, wx.StatusBar):
            control.SetBackgroundColour(wx.Colour(colors['statusbar_bg']))
            control.SetForegroundColour(wx.Colour(colors['fg_primary']))
        else:
            # 默认设置
            control.SetBackgroundColour(wx.Colour(colors['bg_primary']))
            control.SetForegroundColour(wx.Colour(colors['fg_primary']))
        
        control.Refresh()

    @classmethod
    def get_font(cls, size: int = 9, bold: bool = False) -> wx.Font:
        """
        获取字体
        
        Args:
            size: 字体大小
            bold: 是否加粗
            
        Returns:
            wx.Font对象
        """
        from src.utils.encoding_helper import EncodingHelper
        
        font_name = EncodingHelper.get_available_font()
        weight = wx.FONTWEIGHT_BOLD if bold else wx.FONTWEIGHT_NORMAL
        
        return wx.Font(size, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, 
                       weight, faceName=font_name)


# 全局函数
def get_theme_color(color_key: str) -> wx.Colour:
    """获取当前主题颜色"""
    return ThemeManager.get_color(color_key)


def apply_theme(window: wx.Window) -> None:
    """应用当前主题到窗口"""
    ThemeManager.apply_theme_to_window(window)


def set_theme(theme_name: str) -> None:
    """设置主题"""
    ThemeManager.set_theme(theme_name)
