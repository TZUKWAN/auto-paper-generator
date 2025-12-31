# -*- coding: utf-8 -*-
"""
编码处理工具
处理中文字符编码问题
"""

import sys
import locale


class EncodingHelper:
    """编码处理工具类"""

    # 支持的中文编码列表
    CHINESE_ENCODINGS = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5']
    
    # 常用支持中文的字体
    CHINESE_FONTS = [
        'Microsoft YaHei UI',  # 微软雅黑
        'SimHei',  # 黑体
        'SimSun',  # 宋体
        'Arial Unicode MS',  # Arial Unicode
        'WenQuanYi Micro Hei',  # 文泉驿微米黑
    ]

    @staticmethod
    def get_system_encoding() -> str:
        """获取系统默认编码"""
        return sys.getdefaultencoding()

    @staticmethod
    def get_locale_encoding() -> str:
        """获取区域设置编码"""
        try:
            return locale.getpreferredencoding()
        except:
            return 'utf-8'

    @staticmethod
    def try_decode(data: bytes, encodings: list = None) -> tuple:
        """
        尝试用多种编码解码数据
        
        Args:
            data: 要解码的字节数据
            encodings: 要尝试的编码列表，默认使用中文编码列表
            
        Returns:
            (解码后的字符串, 使用的编码) 元组
        """
        if encodings is None:
            encodings = EncodingHelper.CHINESE_ENCODINGS
        
        for encoding in encodings:
            try:
                text = data.decode(encoding)
                return text, encoding
            except UnicodeDecodeError:
                continue
        
        # 如果所有编码都失败，使用utf-8并忽略错误
        return data.decode('utf-8', errors='ignore'), 'utf-8'

    @staticmethod
    def safe_read_text(filepath: str, encodings: list = None) -> tuple:
        """
        安全读取文本文件，尝试多种编码
        
        Args:
            filepath: 文件路径
            encodings: 要尝试的编码列表
            
        Returns:
            (文件内容, 使用的编码) 元组
        """
        with open(filepath, 'rb') as f:
            data = f.read()
        
        return EncodingHelper.try_decode(data, encodings)

    @staticmethod
    def get_available_font(font_list: list = None) -> str:
        """
        获取第一个可用的中文字体
        
        Args:
            font_list: 要检查的字体列表，默认使用CHINESE_FONTS
            
        Returns:
            第一个可用的字体名称
        """
        import wx
        
        if font_list is None:
            font_list = EncodingHelper.CHINESE_FONTS
        
        for font_name in font_list:
            try:
                # 尝试创建字体测试是否可用
                test_font = wx.Font(9, wx.FONTFAMILY_DEFAULT, 
                                    wx.FONTSTYLE_NORMAL, 
                                    wx.FONTWEIGHT_NORMAL,
                                    faceName=font_name)
                if test_font.GetFaceName() == font_name:
                    return font_name
            except:
                continue
        
        # 如果都不可用，返回默认
        return wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT).GetFaceName()

    @staticmethod
    def ensure_utf8(text: str) -> str:
        """
        确保文本是UTF-8编码的字符串
        
        Args:
            text: 输入文本
            
        Returns:
            UTF-8编码的字符串
        """
        if isinstance(text, bytes):
            return text.decode('utf-8', errors='ignore')
        elif not isinstance(text, str):
            return str(text)
        return text


# 全局函数
def safe_decode(data: bytes) -> str:
    """安全解码字节数据"""
    return EncodingHelper.try_decode(data)[0]


def safe_encode(text: str, encoding: str = 'utf-8') -> bytes:
    """安全编码字符串"""
    return text.encode(encoding, errors='ignore')
