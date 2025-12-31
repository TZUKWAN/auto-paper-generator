# -*- coding: utf-8 -*-
"""
商业计划书自动化系统 - wxPython GUI
主程序入口
"""

import wx
import sys
import io
from pathlib import Path

# 设置控制台输出编码（解决Windows中文乱码问题）
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.gui.main_window import MainWindow
from src.core.logger import get_logger
from src.gui.themes.themes import ThemeManager


class MainApp(wx.App):
    """主应用程序类"""

    def __init__(self):
        """初始化应用程序"""
        self.enableHighDPIAware()
        super().__init__(False)
        
        # 初始化日志
        self.logger = get_logger()
        self.logger.info("=" * 60)
        self.logger.info("商业计划书自动化系统启动")
        self.logger.info("=" * 60)

    def enableHighDPIAware(self):
        """启用高DPI支持"""
        # Windows平台
        if sys.platform == 'win32':
            try:
                from ctypes import windll
                windll.shcore.SetProcessDpiAwareness(1)
            except:
                pass

    def OnInit(self):
        """应用程序初始化"""
        try:
            # 创建主窗口
            self.frame = MainWindow()
            self.frame.Show()
            
            self.logger.info("GUI初始化完成，主窗口已显示")
            return True
            
        except Exception as e:
            self.logger.error(f"GUI初始化失败: {e}")
            wx.MessageBox(f"程序启动失败: {e}", "错误", 
                         wx.OK | wx.ICON_ERROR)
            return False

    def OnExit(self):
        """应用程序退出"""
        self.logger.info("=" * 60)
        self.logger.info("程序退出")
        self.logger.info("=" * 60)
        return super().OnExit()


def check_dependencies():
    """检查依赖是否已安装"""
    missing = []
    
    try:
        import yaml
    except ImportError:
        missing.append("PyYAML")
    
    try:
        import wx
    except ImportError:
        missing.append("wxPython")
    
    if missing:
        print("=" * 60)
        print("缺少必要的依赖包:")
        for dep in missing:
            print(f"  - {dep}")
        print()
        print("请运行以下命令安装依赖:")
        print("  pip install -r requirements.txt")
        print()
        print("或者运行安装脚本:")
        print("  install_deps.bat (Windows)")
        print("  bash install_deps.sh (Linux/Mac)")
        print("=" * 60)
        return False
    
    return True


def main():
    """主函数"""
    print("=" * 60)
    print("商业计划书自动化系统 - wxPython GUI")
    print("版本: 2.0.0")
    print("=" * 60)
    print()
    
    # 检查依赖
    if not check_dependencies():
        input("按任意键退出...")
        sys.exit(1)
    
    try:
        # 创建并运行应用程序
        app = MainApp()
        app.MainLoop()
        
    except Exception as e:
        print(f"程序运行出错: {e}")
        import traceback
        traceback.print_exc()
        input("按任意键退出...")
        sys.exit(1)


if __name__ == '__main__':
    main()
