# -*- coding: utf-8 -*-
"""
主窗口
采用Office风格布局，提供专业的商务界面
"""

import wx
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.gui.themes.themes import ThemeManager, get_theme_color
from src.gui.panels.config_panel import ConfigPanel
from src.gui.panels.task_panel import TaskPanel
from src.gui.panels.progress_panel import ProgressPanel
from src.gui.panels.result_panel import ResultPanel
from src.gui.panels.log_panel import LogPanel
from src.core.logger import get_logger
from src.core.config_manager import get_config_manager


class MainWindow(wx.Frame):
    """主窗口类 - Office风格布局"""

    def __init__(self):
        """初始化主窗口"""
        # 初始化窗口
        super().__init__(
            None,
            title="商业计划书自动化系统",
            size=(1400, 900),
            style=wx.DEFAULT_FRAME_STYLE | wx.CLIP_CHILDREN
        )
        
        # 初始化核心组件
        self.logger = get_logger()
        self.config_manager = get_config_manager()
        
        # 面板引用
        self.config_panel = None
        self.task_panel = None
        self.progress_panel = None
        self.result_panel = None
        self.log_panel = None
        
        # 当前活动面板
        self.current_panel = None
        
        # 初始化UI
        self.init_ui()
        
        # 绑定事件
        self.bind_events()
        
        # 应用主题
        self.apply_theme()
        
        # 加载配置
        self.load_config()
        
        self.logger.info("主窗口初始化完成")

    def init_ui(self):
        """初始化用户界面"""
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_toolbar()
        
        # 创建状态栏
        self.create_status_bar()
        
        # 创建主布局
        self.create_main_layout()
        
        # 设置窗口图标（如果有的话）
        self.set_window_properties()

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = wx.MenuBar()
        
        # 文件菜单
        file_menu = wx.Menu()
        new_task_item = file_menu.Append(wx.ID_NEW, "新建任务\tCtrl+N", "创建新任务")
        open_config_item = file_menu.Append(wx.ID_OPEN, "打开配置\tCtrl+O", "打开配置文件")
        save_config_item = file_menu.Append(wx.ID_SAVE, "保存配置\tCtrl+S", "保存当前配置")
        file_menu.AppendSeparator()
        exit_item = file_menu.Append(wx.ID_EXIT, "退出\tAlt+F4", "退出程序")
        
        # 编辑菜单
        edit_menu = wx.Menu()
        preferences_item = edit_menu.Append(wx.ID_PREFERENCES, "首选项", "打开首选项设置")
        edit_menu.AppendSeparator()
        theme_item = edit_menu.Append(wx.ID_ANY, "切换主题", "切换亮色/暗色主题")
        
        # 视图菜单
        view_menu = wx.Menu()
        config_view_item = view_menu.AppendCheckItem(wx.ID_ANY, "系统配置", "显示系统配置面板")
        task_view_item = view_menu.AppendCheckItem(wx.ID_ANY, "任务管理", "显示任务管理面板")
        progress_view_item = view_menu.AppendCheckItem(wx.ID_ANY, "进度监控", "显示进度监控面板")
        result_view_item = view_menu.AppendCheckItem(wx.ID_ANY, "结果查看", "显示结果查看面板")
        log_view_item = view_menu.AppendCheckItem(wx.ID_ANY, "日志查看", "显示日志查看面板")
        
        # 工具菜单
        tools_menu = wx.Menu()
        export_item = tools_menu.Append(wx.ID_ANY, "导出结果", "导出生成结果")
        import_item = tools_menu.Append(wx.ID_ANY, "导入数据", "导入相关数据")
        tools_menu.AppendSeparator()
        clear_cache_item = tools_menu.Append(wx.ID_ANY, "清除缓存", "清除系统缓存")
        
        # 帮助菜单
        help_menu = wx.Menu()
        help_item = help_menu.Append(wx.ID_HELP, "帮助文档\tF1", "查看帮助文档")
        about_item = help_menu.Append(wx.ID_ABOUT, "关于", "关于本程序")
        
        # 添加菜单到菜单栏
        menubar.Append(file_menu, "文件(&F)")
        menubar.Append(edit_menu, "编辑(&E)")
        menubar.Append(view_menu, "视图(&V)")
        menubar.Append(tools_menu, "工具(&T)")
        menubar.Append(help_menu, "帮助(&H)")
        
        self.SetMenuBar(menubar)
        
        # 绑定菜单事件
        self.Bind(wx.EVT_MENU, self.on_new_task, new_task_item)
        self.Bind(wx.EVT_MENU, self.on_save_config, save_config_item)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        self.Bind(wx.EVT_MENU, self.on_preferences, preferences_item)
        self.Bind(wx.EVT_MENU, self.on_switch_theme, theme_item)
        self.Bind(wx.EVT_MENU, self.on_show_config, config_view_item)
        self.Bind(wx.EVT_MENU, self.on_show_task, task_view_item)
        self.Bind(wx.EVT_MENU, self.on_show_progress, progress_view_item)
        self.Bind(wx.EVT_MENU, self.on_show_result, result_view_item)
        self.Bind(wx.EVT_MENU, self.on_show_log, log_view_item)
        self.Bind(wx.EVT_MENU, self.on_export, export_item)
        self.Bind(wx.EVT_MENU, self.on_about, about_item)

    def create_toolbar(self):
        """创建工具栏"""
        toolbar = self.CreateToolBar(style=wx.TB_HORIZONTAL | wx.TB_FLAT | wx.TB_TEXT)
        toolbar.SetToolBitmapSize((32, 32))
        
        # 创建工具栏按钮
        toolbar.AddTool(wx.ID_NEW, "新建任务", wx.ArtProvider.GetBitmap(wx.ART_NEW, wx.ART_TOOLBAR, (32, 32)), "创建新任务")
        toolbar.AddSeparator()
        toolbar.AddTool(wx.ID_SAVE, "保存配置", wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR, (32, 32)), "保存当前配置")
        toolbar.AddSeparator()
        toolbar.AddTool(wx.ID_REFRESH, "刷新", wx.ArtProvider.GetBitmap(wx.ART_UNDO, wx.ART_TOOLBAR, (32, 32)), "刷新当前视图")
        toolbar.AddSeparator()
        toolbar.AddTool(wx.ID_ABOUT, "关于", wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_TOOLBAR, (32, 32)), "关于本程序")
        
        toolbar.Realize()
        
        # 绑定工具栏事件
        self.Bind(wx.EVT_TOOL, self.on_new_task, id=wx.ID_NEW)
        self.Bind(wx.EVT_TOOL, self.on_save_config, id=wx.ID_SAVE)
        self.Bind(wx.EVT_TOOL, self.on_about, id=wx.ID_ABOUT)

    def create_status_bar(self):
        """创建状态栏"""
        self.statusbar = self.CreateStatusBar(3)
        self.statusbar.SetStatusWidths([-3, -2, -1])
        self.update_statusbar("就绪", "", "")

    def update_statusbar(self, message: str = "", task_info: str = "", time_str: str = ""):
        """更新状态栏"""
        if not time_str:
            import datetime
            time_str = datetime.datetime.now().strftime("%H:%M:%S")
        self.statusbar.SetStatusText(message, 0)
        self.statusbar.SetStatusText(task_info, 1)
        self.statusbar.SetStatusText(time_str, 2)

    def create_main_layout(self):
        """创建主布局"""
        # 主面板
        main_panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 创建分割器窗口
        splitter = wx.SplitterWindow(main_panel, style=wx.SP_3D | wx.SP_LIVE_UPDATE)
        
        # 创建左侧导航面板
        left_panel = self.create_navigation_panel(splitter)
        
        # 创建右侧工作区面板
        self.workspace_panel = wx.Panel(splitter)
        self.workspace_sizer = wx.BoxSizer(wx.VERTICAL)
        self.workspace_panel.SetSizer(self.workspace_sizer)
        
        # 设置分割比例
        splitter.SplitVertically(left_panel, self.workspace_panel, 220)
        splitter.SetMinimumPaneSize(150)
        splitter.SetSashGravity(0.25)
        
        # 添加到主布局
        main_sizer.Add(splitter, 1, wx.EXPAND)
        main_panel.SetSizer(main_sizer)
        
        # 显示默认面板（系统配置）
        self.show_config_panel()

    def create_navigation_panel(self, parent):
        """创建左侧导航面板"""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 标题
        title_text = wx.StaticText(panel, label="功能导航")
        title_font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title_text.SetFont(title_font)
        sizer.Add(title_text, 0, wx.ALL, 5)
        sizer.Add(wx.StaticLine(panel), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        
        # 创建树形控件
        self.nav_tree = wx.TreeCtrl(panel, style=wx.TR_DEFAULT_STYLE | wx.TR_SINGLE)
        self.nav_tree.SetBackgroundColour(get_theme_color('bg_secondary'))
        
        # 添加根节点
        root = self.nav_tree.AddRoot("主菜单")
        
        # 添加功能节点（直接传递数据，不使用已弃用的 TreeItemData）
        config_node = self.nav_tree.AppendItem(root, "系统配置", data="config")
        task_node = self.nav_tree.AppendItem(root, "任务管理", data="task")
        progress_node = self.nav_tree.AppendItem(root, "进度监控", data="progress")
        result_node = self.nav_tree.AppendItem(root, "结果查看", data="result")
        log_node = self.nav_tree.AppendItem(root, "日志查看", data="log")
        
        # 展开根节点
        self.nav_tree.Expand(root)
        
        sizer.Add(self.nav_tree, 1, wx.EXPAND | wx.ALL, 5)
        
        # 绑定树形控件事件
        self.nav_tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_tree_selection_changed)
        self.nav_tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_tree_item_activated)
        
        panel.SetSizer(sizer)
        return panel

    def bind_events(self):
        """绑定窗口事件"""
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_SIZE, self.on_size)

    def set_window_properties(self):
        """设置窗口属性"""
        # 居中显示
        self.Center()
        
        # 设置最小尺寸
        self.SetMinSize((1000, 600))

    def show_config_panel(self):
        """显示系统配置面板"""
        self.clear_workspace()
        self.config_panel = ConfigPanel(self.workspace_panel)
        self.workspace_sizer.Add(self.config_panel, 1, wx.EXPAND)
        self.workspace_sizer.Layout()
        self.current_panel = self.config_panel
        self.update_statusbar("系统配置", "显示系统配置")

    def show_task_panel(self):
        """显示任务管理面板"""
        self.clear_workspace()
        self.task_panel = TaskPanel(self.workspace_panel)
        self.workspace_sizer.Add(self.task_panel, 1, wx.EXPAND)
        self.workspace_sizer.Layout()
        self.current_panel = self.task_panel
        self.update_statusbar("任务管理", "显示任务管理")

    def show_progress_panel(self):
        """显示进度监控面板"""
        self.clear_workspace()
        self.progress_panel = ProgressPanel(self.workspace_panel)
        self.workspace_sizer.Add(self.progress_panel, 1, wx.EXPAND)
        self.workspace_sizer.Layout()
        self.current_panel = self.progress_panel
        self.update_statusbar("进度监控", "显示进度监控")

    def show_result_panel(self):
        """显示结果查看面板"""
        self.clear_workspace()
        self.result_panel = ResultPanel(self.workspace_panel)
        self.workspace_sizer.Add(self.result_panel, 1, wx.EXPAND)
        self.workspace_sizer.Layout()
        self.current_panel = self.result_panel
        self.update_statusbar("结果查看", "显示结果查看")

    def show_log_panel(self):
        """显示日志查看面板"""
        self.clear_workspace()
        self.log_panel = LogPanel(self.workspace_panel)
        self.workspace_sizer.Add(self.log_panel, 1, wx.EXPAND)
        self.workspace_sizer.Layout()
        self.current_panel = self.log_panel
        self.update_statusbar("日志查看", "显示日志查看")

    def clear_workspace(self):
        """清除工作区"""
        if self.current_panel:
            self.workspace_sizer.Clear()
            self.current_panel.Destroy()
            self.current_panel = None

    def apply_theme(self):
        """应用当前主题"""
        ThemeManager.apply_theme_to_window(self)
        self.Refresh()

    def load_config(self):
        """加载配置"""
        try:
            self.config_manager.load_config()
            self.logger.info("配置加载成功")
        except Exception as e:
            self.logger.error(f"配置加载失败: {e}")
            wx.MessageBox(f"配置加载失败: {e}", "错误", wx.OK | wx.ICON_ERROR)

    def save_config(self):
        """保存配置"""
        try:
            success = self.config_manager.save_config()
            if success:
                self.logger.info("配置保存成功")
                wx.MessageBox("配置保存成功", "成功", wx.OK | wx.ICON_INFORMATION)
            else:
                raise Exception("保存失败")
        except Exception as e:
            self.logger.error(f"配置保存失败: {e}")
            wx.MessageBox(f"配置保存失败: {e}", "错误", wx.OK | wx.ICON_ERROR)

    # 事件处理器
    def on_new_task(self, event):
        """新建任务事件"""
        self.show_task_panel()
        if self.task_panel:
            self.task_panel.on_new_task(event)

    def on_save_config(self, event):
        """保存配置事件"""
        self.save_config()

    def on_exit(self, event):
        """退出事件"""
        self.Close()

    def on_preferences(self, event):
        """首选项事件"""
        self.show_config_panel()

    def on_switch_theme(self, event):
        """切换主题事件"""
        current = ThemeManager.get_current_theme()
        new_theme = 'dark' if current == 'light' else 'light'
        ThemeManager.set_theme(new_theme)
        self.apply_theme()
        self.logger.info(f"主题切换为: {new_theme}")

    def on_show_config(self, event):
        """显示配置面板"""
        self.show_config_panel()

    def on_show_task(self, event):
        """显示任务面板"""
        self.show_task_panel()

    def on_show_progress(self, event):
        """显示进度面板"""
        self.show_progress_panel()

    def on_show_result(self, event):
        """显示结果面板"""
        self.show_result_panel()

    def on_show_log(self, event):
        """显示日志面板"""
        self.show_log_panel()

    def on_export(self, event):
        """导出事件"""
        wx.MessageBox("导出功能开发中...", "提示", wx.OK | wx.ICON_INFORMATION)

    def on_about(self, event):
        """关于事件"""
        info = wx.adv.AboutDialogInfo()
        info.SetName("商业计划书自动化系统")
        info.SetVersion("2.0.0")
        info.SetDescription("基于AI的商业计划书自动化生成工具\n使用wxPython构建的专业商务界面")
        info.SetCopyright("(C) 2024")
        info.SetWebSite("https://github.com/your-repo")
        wx.adv.AboutBox(info)

    def on_tree_selection_changed(self, event):
        """树形控件选择改变事件"""
        item = event.GetItem()
        if not item.IsOk():
            return
        
        data = self.nav_tree.GetItemData(item)
        if data:
            panel_type = data.GetData()
            if panel_type == "config":
                self.show_config_panel()
            elif panel_type == "task":
                self.show_task_panel()
            elif panel_type == "progress":
                self.show_progress_panel()
            elif panel_type == "result":
                self.show_result_panel()
            elif panel_type == "log":
                self.show_log_panel()

    def on_tree_item_activated(self, event):
        """树形控件项目激活事件"""
        self.on_tree_selection_changed(event)

    def on_close(self, event):
        """关闭窗口事件"""
        self.logger.info("程序退出")
        event.Skip()

    def on_size(self, event):
        """窗口大小改变事件"""
        event.Skip()
