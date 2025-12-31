# -*- coding: utf-8 -*-
"""
进度监控面板
实时显示任务执行进度
"""

import wx
import wx.grid
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.gui.themes.themes import get_theme_color
from src.core.task_manager import get_task_manager, TaskStatus
from src.core.logger import get_logger


class ProgressPanel(wx.Panel):
    """进度监控面板"""

    def __init__(self, parent):
        """初始化进度面板"""
        super().__init__(parent)
        self.task_manager = get_task_manager()
        self.logger = get_logger()
        self.timer = None
        self.init_ui()
        self.start_timer()

    def init_ui(self):
        """初始化UI"""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 顶部统计
        stats_panel = self.create_stats_panel()
        sizer.Add(stats_panel, 0, wx.EXPAND | wx.ALL, 5)
        
        # 进度列表
        list_panel = self.create_progress_list()
        sizer.Add(list_panel, 1, wx.EXPAND | wx.ALL, 5)
        
        # 任务进度详情
        detail_panel = self.create_progress_detail()
        sizer.Add(detail_panel, 0, wx.EXPAND | wx.ALL, 5)
        
        self.SetSizer(sizer)

    def create_stats_panel(self):
        """创建统计面板"""
        panel = wx.Panel(self)
        panel.SetBackgroundColour(get_theme_color('bg_secondary'))
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 总任务数
        self.total_label = wx.StaticText(panel, label="总任务数: 0")
        sizer.Add(self.total_label, 0, wx.ALL, 10)
        
        # 执行中
        self.running_label = wx.StaticText(panel, label="执行中: 0", 
                                          style=wx.ST_NO_AUTORESIZE)
        sizer.Add(self.running_label, 0, wx.ALL, 10)
        
        # 已完成
        self.completed_label = wx.StaticText(panel, label="已完成: 0", 
                                            style=wx.ST_NO_AUTORESIZE)
        sizer.Add(self.completed_label, 0, wx.ALL, 10)
        
        # 失败
        self.failed_label = wx.StaticText(panel, label="失败: 0", 
                                         style=wx.ST_NO_AUTORESIZE)
        sizer.Add(self.failed_label, 0, wx.ALL, 10)
        
        # 待处理
        self.pending_label = wx.StaticText(panel, label="待处理: 0", 
                                          style=wx.ST_NO_AUTORESIZE)
        sizer.Add(self.pending_label, 0, wx.ALL, 10)
        
        panel.SetSizer(sizer)
        return panel

    def create_progress_list(self):
        """创建进度列表"""
        list_group = wx.StaticBox(self, label="任务进度列表")
        list_sizer = wx.StaticBoxSizer(list_group, wx.VERTICAL)
        
        # 使用网格显示任务列表
        self.progress_grid = wx.grid.Grid(self)
        self.progress_grid.CreateGrid(0, 5)
        self.progress_grid.SetColLabelValue(0, "任务ID")
        self.progress_grid.SetColLabelValue(1, "任务标题")
        self.progress_grid.SetColLabelValue(2, "状态")
        self.progress_grid.SetColLabelValue(3, "进度")
        self.progress_grid.SetColLabelValue(4, "开始时间")
        
        # 设置列宽
        self.progress_grid.SetColSize(0, 80)
        self.progress_grid.SetColSize(1, 200)
        self.progress_grid.SetColSize(2, 80)
        self.progress_grid.SetColSize(3, 100)
        self.progress_grid.SetColSize(4, 150)
        
        # 设置网格属性
        self.progress_grid.SetGridLineColour(get_theme_color('border'))
        self.progress_grid.SetDefaultCellBackgroundColour(get_theme_color('bg_primary'))
        self.progress_grid.SetRowLabelSize(0)
        
        # 只读
        self.progress_grid.EnableEditing(False)
        self.progress_grid.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.on_cell_selected)
        
        list_sizer.Add(self.progress_grid, 1, wx.EXPAND)
        return list_sizer

    def create_progress_detail(self):
        """创建进度详情"""
        detail_group = wx.StaticBox(self, label="进度详情")
        detail_sizer = wx.StaticBoxSizer(detail_group, wx.VERTICAL)
        
        # 进度条
        progress_label = wx.StaticText(self, label="任务进度:")
        self.progress_bar = wx.Gauge(self, range=100, style=wx.GA_HORIZONTAL)
        self.progress_text = wx.StaticText(self, label="0%")
        
        detail_sizer.Add(progress_label, 0, wx.ALL, 5)
        detail_sizer.Add(self.progress_bar, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        detail_sizer.Add(self.progress_text, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        
        # 状态信息
        self.status_text = wx.StaticText(self, label="状态: 未选择任务")
        detail_sizer.Add(self.status_text, 0, wx.ALL, 5)
        
        # 消息信息
        msg_label = wx.StaticText(self, label="当前消息:")
        self.msg_text = wx.TextCtrl(self, value="", style=wx.TE_READONLY | wx.TE_MULTILINE)
        self.msg_text.SetMinSize((-1, 60))
        detail_sizer.Add(msg_label, 0, wx.ALL, 5)
        detail_sizer.Add(self.msg_text, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        
        return detail_sizer

    def start_timer(self):
        """启动定时器，用于刷新进度"""
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        self.timer.Start(1000)  # 每秒刷新一次

    def on_timer(self, event):
        """定时器事件"""
        self.update_stats()
        self.refresh_progress_list()

    def update_stats(self):
        """更新统计信息"""
        total = self.task_manager.get_task_count()
        running = self.task_manager.get_task_count(TaskStatus.IN_PROGRESS)
        completed = self.task_manager.get_task_count(TaskStatus.COMPLETED)
        failed = self.task_manager.get_task_count(TaskStatus.FAILED)
        pending = self.task_manager.get_task_count(TaskStatus.PENDING)
        
        self.total_label.SetLabel(f"总任务数: {total}")
        self.running_label.SetLabel(f"执行中: {running}")
        self.completed_label.SetLabel(f"已完成: {completed}")
        self.failed_label.SetLabel(f"失败: {failed}")
        self.pending_label.SetLabel(f"待处理: {pending}")

    def refresh_progress_list(self):
        """刷新进度列表"""
        tasks = self.task_manager.get_all_tasks()
        
        # 保存当前选中行
        current_row = self.progress_grid.GetGridCursorRow()
        
        # 清空并重新填充
        if self.progress_grid.GetNumberRows() > 0:
            self.progress_grid.DeleteRows(0, self.progress_grid.GetNumberRows())
        
        self.progress_grid.AppendRows(len(tasks))
        
        for row, task in enumerate(tasks):
            self.progress_grid.SetCellValue(row, 0, task.task_id[:8] + "...")
            self.progress_grid.SetCellValue(row, 1, task.title)
            self.progress_grid.SetCellValue(row, 2, task.status.value)
            self.progress_grid.SetCellValue(row, 3, f"{task.progress}%")
            if task.started_at:
                self.progress_grid.SetCellValue(row, 4, 
                                               task.started_at.strftime("%H:%M:%S"))
            else:
                self.progress_grid.SetCellValue(row, 4, "-")
            
            # 设置状态颜色
            if task.status == TaskStatus.IN_PROGRESS:
                self.progress_grid.SetCellTextColour(row, 2, 
                                                    wx.Colour(get_theme_color('primary')))
            elif task.status == TaskStatus.COMPLETED:
                self.progress_grid.SetCellTextColour(row, 2, 
                                                    wx.Colour(get_theme_color('success')))
            elif task.status == TaskStatus.FAILED:
                self.progress_grid.SetCellTextColour(row, 2, 
                                                    wx.Colour(get_theme_color('error')))

    def on_cell_selected(self, event):
        """单元格选择事件"""
        row = event.GetRow()
        tasks = self.task_manager.get_all_tasks()
        
        if row < len(tasks):
            task = tasks[row]
            self.update_progress_detail(task)
        
        event.Skip()

    def update_progress_detail(self, task):
        """更新进度详情"""
        self.progress_bar.SetValue(task.progress)
        self.progress_text.SetLabel(f"{task.progress}%")
        self.status_text.SetLabel(f"状态: {task.status.value}")
        self.msg_text.SetValue(task.error if task.error else "任务执行中...")

    def stop_timer(self):
        """停止定时器"""
        if self.timer:
            self.timer.Stop()
