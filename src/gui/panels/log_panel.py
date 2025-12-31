# -*- coding: utf-8 -*-
"""
日志查看面板
查看系统运行日志
"""

import wx
from pathlib import Path
import sys
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.gui.themes.themes import get_theme_color
from src.core.logger import get_logger, LogViewer


class LogPanel(wx.Panel):
    """日志查看面板"""

    def __init__(self, parent):
        """初始化日志面板"""
        super().__init__(parent)
        self.logger = get_logger()
        self.log_viewer = LogViewer(self.logger)
        self.timer = None
        self.init_ui()
        self.start_timer()

    def init_ui(self):
        """初始化UI"""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 顶部工具栏
        toolbar = self.create_toolbar()
        sizer.Add(toolbar, 0, wx.EXPAND | wx.ALL, 5)
        
        # 过滤器
        filter_panel = self.create_filter_panel()
        sizer.Add(filter_panel, 0, wx.EXPAND | wx.ALL, 5)
        
        # 日志列表
        self.create_log_list(sizer)
        
        # 日志详情
        self.create_log_detail(sizer)
        
        self.SetSizer(sizer)

    def create_toolbar(self):
        """创建工具栏"""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 清空日志
        clear_btn = wx.Button(panel, label="清空日志", style=wx.BU_EXACTFIT)
        clear_btn.Bind(wx.EVT_BUTTON, self.on_clear_logs)
        
        # 刷新
        refresh_btn = wx.Button(panel, label="刷新", style=wx.BU_EXACTFIT)
        refresh_btn.Bind(wx.EVT_BUTTON, self.on_refresh)
        
        # 导出日志
        export_btn = wx.Button(panel, label="导出日志", style=wx.BU_EXACTFIT)
        export_btn.Bind(wx.EVT_BUTTON, self.on_export)
        
        sizer.Add(clear_btn, 0, wx.ALL, 2)
        sizer.Add(refresh_btn, 0, wx.ALL, 2)
        sizer.Add(export_btn, 0, wx.ALL, 2)
        sizer.AddStretchSpacer()
        
        # 自动刷新开关
        self.auto_refresh_chk = wx.CheckBox(panel, label="自动刷新")
        self.auto_refresh_chk.SetValue(True)
        sizer.Add(self.auto_refresh_chk, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)
        
        panel.SetSizer(sizer)
        return panel

    def create_filter_panel(self):
        """创建过滤器面板"""
        panel = wx.Panel(self)
        panel.SetBackgroundColour(get_theme_color('bg_secondary'))
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 日志级别过滤
        level_label = wx.StaticText(panel, label="日志级别:")
        self.level_combo = wx.ComboBox(panel, value="ALL", 
                                     choices=["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                                     style=wx.CB_READONLY)
        
        # 最大行数
        lines_label = wx.StaticText(panel, label="最大行数:")
        self.lines_spin = wx.SpinCtrl(panel, value="100", min=10, max=1000)
        
        # 搜索
        search_label = wx.StaticText(panel, label="搜索:")
        self.search_text = wx.TextCtrl(panel, value="", style=wx.TE_PROCESS_ENTER)
        self.search_text.Bind(wx.EVT_TEXT_ENTER, self.on_search)
        
        sizer.Add(level_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        sizer.Add(self.level_combo, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        sizer.Add(lines_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        sizer.Add(self.lines_spin, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        sizer.Add(search_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        sizer.Add(self.search_text, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        
        # 绑定事件
        self.level_combo.Bind(wx.EVT_COMBOBOX, self.on_filter_changed)
        
        panel.SetSizer(sizer)
        return panel

    def create_log_list(self, parent_sizer):
        """创建日志列表"""
        list_group = wx.StaticBox(self, label="日志列表")
        list_sizer = wx.StaticBoxSizer(list_group, wx.VERTICAL)
        
        # 使用列表控件
        self.log_list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | 
                                    wx.LC_HRULES | wx.LC_VRULES)
        self.log_list.SetBackgroundColour(get_theme_color('bg_secondary'))
        
        # 添加列
        self.log_list.InsertColumn(0, "时间", width=150)
        self.log_list.InsertColumn(1, "级别", width=80)
        self.log_list.InsertColumn(2, "名称", width=100)
        self.log_list.InsertColumn(3, "消息", width=500)
        
        list_sizer.Add(self.log_list, 1, wx.EXPAND)
        
        # 绑定选择事件
        self.log_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_log_selected)
        
        parent_sizer.Add(list_sizer, 1, wx.EXPAND | wx.ALL, 5)

    def create_log_detail(self, parent_sizer):
        """创建日志详情"""
        detail_group = wx.StaticBox(self, label="日志详情")
        detail_sizer = wx.StaticBoxSizer(detail_group, wx.VERTICAL)
        
        self.log_detail_text = wx.TextCtrl(self, value="", 
                                         style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH)
        self.log_detail_text.SetMinSize((-1, 100))
        
        detail_sizer.Add(self.log_detail_text, 1, wx.EXPAND | wx.ALL, 5)
        
        parent_sizer.Add(detail_sizer, 0, wx.EXPAND | wx.ALL, 5)

    def start_timer(self):
        """启动定时器，用于自动刷新"""
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        self.timer.Start(2000)  # 每2秒刷新一次

    def on_timer(self, event):
        """定时器事件"""
        if self.auto_refresh_chk.GetValue():
            self.refresh_logs()

    def refresh_logs(self):
        """刷新日志列表"""
        # 清空当前列表
        self.log_list.DeleteAllItems()
        
        # 获取过滤参数
        level = self.level_combo.GetValue()
        max_lines = self.lines_spin.GetValue()
        
        # 获取日志
        logs = self.log_viewer.get_recent_logs(count=max_lines, filter_level=level)
        
        # 过滤搜索
        search_text = self.search_text.GetValue().lower().strip()
        if search_text:
            logs = [log for log in logs if search_text in log.lower()]
        
        # 填充列表
        for log in logs:
            entry = self.log_viewer.format_log_entry(log)
            index = self.log_list.InsertItem(self.log_list.GetItemCount(), entry['timestamp'])
            self.log_list.SetItem(index, 1, entry['level'])
            self.log_list.SetItem(index, 2, entry['name'])
            self.log_list.SetItem(index, 3, entry['message'])
            
            # 设置级别颜色
            if entry['level'] == 'ERROR' or entry['level'] == 'CRITICAL':
                self.log_list.SetItemTextColour(index, wx.Colour(get_theme_color('error')))
            elif entry['level'] == 'WARNING':
                self.log_list.SetItemTextColour(index, wx.Colour(get_theme_color('warning')))

    def on_log_selected(self, event):
        """日志选择事件"""
        item = event.GetItem()
        index = item.GetIndex()
        
        # 获取日志内容
        timestamp = self.log_list.GetItemText(index, 0)
        level = self.log_list.GetItemText(index, 1)
        name = self.log_list.GetItemText(index, 2)
        message = self.log_list.GetItemText(index, 3)
        
        # 格式化详情
        detail = f"""时间: {timestamp}
级别: {level}
名称: {name}
消息: {message}
"""
        self.log_detail_text.SetValue(detail)

    def on_clear_logs(self, event):
        """清空日志"""
        result = wx.MessageBox("确定要清空所有日志吗？", "确认", 
                             wx.YES_NO | wx.ICON_QUESTION)
        if result == wx.YES:
            self.logger.clear_logs()
            self.refresh_logs()
            wx.MessageBox("日志已清空", "成功", wx.OK | wx.ICON_INFORMATION)

    def on_refresh(self, event):
        """刷新日志"""
        self.refresh_logs()

    def on_filter_changed(self, event):
        """过滤器改变事件"""
        self.refresh_logs()

    def on_search(self, event):
        """搜索事件"""
        self.refresh_logs()

    def on_export(self, event):
        """导出日志"""
        # 保存对话框
        wildcard = "Text Files (*.txt)|*.txt|All Files (*.*)|*.*"
        dlg = wx.FileDialog(self, "导出日志", wildcard=wildcard, 
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        
        if dlg.ShowModal() == wx.ID_OK:
            filepath = dlg.GetPath()
            try:
                # 收集所有显示的日志
                lines = []
                for i in range(self.log_list.GetItemCount()):
                    timestamp = self.log_list.GetItemText(i, 0)
                    level = self.log_list.GetItemText(i, 1)
                    name = self.log_list.GetItemText(i, 2)
                    message = self.log_list.GetItemText(i, 3)
                    lines.append(f"{timestamp} - {name} - {level} - {message}")
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write("\n".join(lines))
                
                wx.MessageBox("导出成功", "成功", wx.OK | wx.ICON_INFORMATION)
            except Exception as e:
                wx.MessageBox(f"导出失败: {e}", "错误", wx.OK | wx.ICON_ERROR)
        
        dlg.Destroy()

    def stop_timer(self):
        """停止定时器"""
        if self.timer:
            self.timer.Stop()
