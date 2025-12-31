# -*- coding: utf-8 -*-
"""
任务管理面板
提供任务创建、编辑、删除和管理功能
"""

import wx
import wx.dataview as dv
from pathlib import Path
import sys
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.gui.themes.themes import get_theme_color
from src.core.task_manager import get_task_manager, TaskStatus
from src.core.logger import get_logger


class TaskPanel(wx.Panel):
    """任务管理面板"""

    def __init__(self, parent):
        """初始化任务面板"""
        super().__init__(parent)
        self.task_manager = get_task_manager()
        self.logger = get_logger()
        self.current_task_id = None
        self.init_ui()
        self.refresh_task_list()

    def init_ui(self):
        """初始化UI"""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 顶部工具栏
        toolbar = self.create_toolbar()
        sizer.Add(toolbar, 0, wx.EXPAND | wx.ALL, 5)
        
        # 任务列表
        self.create_task_list(sizer)
        
        # 任务详情
        self.create_task_detail(sizer)
        
        self.SetSizer(sizer)

    def create_toolbar(self):
        """创建工具栏"""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 新建任务
        new_btn = wx.Button(panel, label="新建任务", style=wx.BU_EXACTFIT)
        new_btn.Bind(wx.EVT_BUTTON, self.on_new_task)
        
        # 执行任务
        run_btn = wx.Button(panel, label="执行任务", style=wx.BU_EXACTFIT)
        run_btn.Bind(wx.EVT_BUTTON, self.on_run_task)
        
        # 暂停任务
        pause_btn = wx.Button(panel, label="暂停任务", style=wx.BU_EXACTFIT)
        pause_btn.Bind(wx.EVT_BUTTON, self.on_pause_task)
        
        # 删除任务
        delete_btn = wx.Button(panel, label="删除任务", style=wx.BU_EXACTFIT)
        delete_btn.Bind(wx.EVT_BUTTON, self.on_delete_task)
        
        # 清除已完成
        clear_btn = wx.Button(panel, label="清除已完成", style=wx.BU_EXACTFIT)
        clear_btn.Bind(wx.EVT_BUTTON, self.on_clear_completed)
        
        # 刷新
        refresh_btn = wx.Button(panel, label="刷新", style=wx.BU_EXACTFIT)
        refresh_btn.Bind(wx.EVT_BUTTON, self.on_refresh)
        
        sizer.Add(new_btn, 0, wx.ALL, 2)
        sizer.Add(run_btn, 0, wx.ALL, 2)
        sizer.Add(pause_btn, 0, wx.ALL, 2)
        sizer.Add(delete_btn, 0, wx.ALL, 2)
        sizer.Add(clear_btn, 0, wx.ALL, 2)
        sizer.AddStretchSpacer()
        sizer.Add(refresh_btn, 0, wx.ALL, 2)
        
        panel.SetSizer(sizer)
        return panel

    def create_task_list(self, parent_sizer):
        """创建任务列表"""
        list_label = wx.StaticText(self, label="任务列表")
        parent_sizer.Add(list_label, 0, wx.ALL, 5)
        
        # 创建数据视图列表控件
        self.task_list = dv.DataViewListCtrl(self, style=wx.DV_ROW_LINES | wx.DV_VERT_RULES)
        self.task_list.SetBackgroundColour(get_theme_color('bg_secondary'))
        
        # 添加列
        self.task_list.AppendTextColumn("任务ID", width=80, mode=dv.DATAVIEW_CELL_INERT)
        self.task_list.AppendTextColumn("任务标题", width=200, mode=dv.DATAVIEW_CELL_INERT)
        self.task_list.AppendTextColumn("任务类型", width=100, mode=dv.DATAVIEW_CELL_INERT)
        self.task_list.AppendTextColumn("状态", width=80, mode=dv.DATAVIEW_CELL_INERT)
        self.task_list.AppendTextColumn("进度", width=80, mode=dv.DATAVIEW_CELL_INERT)
        self.task_list.AppendTextColumn("创建时间", width=150, mode=dv.DATAVIEW_CELL_INERT)
        
        parent_sizer.Add(self.task_list, 2, wx.EXPAND | wx.ALL, 5)
        
        # 绑定选择事件
        self.task_list.Bind(dv.EVT_DATAVIEW_SELECTION_CHANGED, self.on_task_selected)

    def create_task_detail(self, parent_sizer):
        """创建任务详情"""
        detail_group = wx.StaticBox(self, label="任务详情")
        detail_sizer = wx.StaticBoxSizer(detail_group, wx.VERTICAL)
        
        # 任务ID
        id_label = wx.StaticText(self, label="任务ID:")
        self.id_text = wx.TextCtrl(self, value="", style=wx.TE_READONLY)
        detail_sizer.Add(id_label, 0, wx.ALL | wx.EXPAND, 2)
        detail_sizer.Add(self.id_text, 0, wx.ALL | wx.EXPAND, 2)
        
        # 任务标题
        title_label = wx.StaticText(self, label="任务标题:")
        self.title_text = wx.TextCtrl(self, value="")
        detail_sizer.Add(title_label, 0, wx.ALL | wx.EXPAND, 2)
        detail_sizer.Add(self.title_text, 0, wx.ALL | wx.EXPAND, 2)
        
        # 任务描述
        desc_label = wx.StaticText(self, label="任务描述:")
        self.desc_text = wx.TextCtrl(self, value="", style=wx.TE_MULTILINE)
        self.desc_text.SetMinSize((-1, 100))
        detail_sizer.Add(desc_label, 0, wx.ALL | wx.EXPAND, 2)
        detail_sizer.Add(self.desc_text, 0, wx.ALL | wx.EXPAND, 2)
        
        # 任务类型
        type_label = wx.StaticText(self, label="任务类型:")
        self.type_combo = wx.ComboBox(self, value="generation", 
                                     choices=["generation", "review", "export", "analysis"])
        detail_sizer.Add(type_label, 0, wx.ALL | wx.EXPAND, 2)
        detail_sizer.Add(self.type_combo, 0, wx.ALL | wx.EXPAND, 2)
        
        # 保存按钮
        save_btn = wx.Button(self, label="保存修改", style=wx.BU_EXACTFIT)
        save_btn.Bind(wx.EVT_BUTTON, self.on_save_task)
        detail_sizer.Add(save_btn, 0, wx.ALL, 5)
        
        parent_sizer.Add(detail_sizer, 1, wx.EXPAND | wx.ALL, 5)

    def refresh_task_list(self):
        """刷新任务列表"""
        self.task_list.DeleteAllItems()
        
        tasks = self.task_manager.get_all_tasks()
        for task in tasks:
            self.task_list.AppendItem([
                task.task_id[:8] + "...",
                task.title,
                task.task_type,
                task.status.value,
                f"{task.progress}%",
                task.created_at.strftime("%Y-%m-%d %H:%M:%S")
            ])

    def on_task_selected(self, event):
        """任务选择事件"""
        item = event.GetItem()
        if not item:
            return
        
        row = self.task_list.ItemToRow(item)
        if row >= 0:
            # 获取任务ID（完整ID）
            task_id_value = self.task_list.GetTextValue(row, 0)
            # 由于显示的是缩略ID，需要从任务管理器获取完整ID
            tasks = self.task_manager.get_all_tasks()
            if row < len(tasks):
                task = tasks[row]
                self.current_task_id = task.task_id
                self.show_task_detail(task)

    def show_task_detail(self, task):
        """显示任务详情"""
        self.id_text.SetValue(task.task_id)
        self.title_text.SetValue(task.title)
        self.desc_text.SetValue(task.description or "")
        self.type_combo.SetValue(task.task_type)

    def on_new_task(self, event):
        """新建任务"""
        self.current_task_id = None
        self.id_text.SetValue("")
        self.title_text.SetValue("")
        self.desc_text.SetValue("")
        self.type_combo.SetValue("generation")
        self.title_text.SetFocus()

    def on_run_task(self, event):
        """执行任务"""
        if not self.current_task_id:
            wx.MessageBox("请先选择或创建任务", "提示", wx.OK | wx.ICON_WARNING)
            return
        
        task = self.task_manager.get_task(self.current_task_id)
        if task:
            self.task_manager.update_task_status(self.current_task_id, TaskStatus.IN_PROGRESS)
            self.refresh_task_list()
            wx.MessageBox(f"任务开始执行: {task.title}", "信息", wx.OK | wx.ICON_INFORMATION)

    def on_pause_task(self, event):
        """暂停任务"""
        if not self.current_task_id:
            wx.MessageBox("请先选择任务", "提示", wx.OK | wx.ICON_WARNING)
            return
        
        wx.MessageBox("暂停功能开发中...", "提示", wx.OK | wx.ICON_INFORMATION)

    def on_delete_task(self, event):
        """删除任务"""
        if not self.current_task_id:
            wx.MessageBox("请先选择任务", "提示", wx.OK | wx.ICON_WARNING)
            return
        
        result = wx.MessageBox("确定要删除此任务吗？", "确认", 
                             wx.YES_NO | wx.ICON_QUESTION)
        if result == wx.YES:
            self.task_manager.delete_task(self.current_task_id)
            self.current_task_id = None
            self.refresh_task_list()
            self.on_new_task(None)

    def on_clear_completed(self, event):
        """清除已完成任务"""
        result = wx.MessageBox("确定要清除所有已完成的任务吗？", "确认", 
                             wx.YES_NO | wx.ICON_QUESTION)
        if result == wx.YES:
            count = self.task_manager.clear_completed_tasks()
            self.refresh_task_list()
            wx.MessageBox(f"已清除 {count} 个已完成任务", "成功", 
                         wx.OK | wx.ICON_INFORMATION)

    def on_save_task(self, event):
        """保存任务"""
        title = self.title_text.GetValue().strip()
        if not title:
            wx.MessageBox("请输入任务标题", "错误", wx.OK | wx.ICON_ERROR)
            return
        
        if self.current_task_id:
            # 更新现有任务
            task = self.task_manager.get_task(self.current_task_id)
            if task:
                task.title = title
                task.description = self.desc_text.GetValue()
                task.task_type = self.type_combo.GetValue()
                self.logger.info(f"更新任务: {self.current_task_id}")
        else:
            # 创建新任务
            self.current_task_id = self.task_manager.create_task(
                title=title,
                description=self.desc_text.GetValue(),
                task_type=self.type_combo.GetValue()
            )
            self.id_text.SetValue(self.current_task_id)
            self.logger.info(f"创建任务: {self.current_task_id}")
        
        self.refresh_task_list()
        wx.MessageBox("任务保存成功", "成功", wx.OK | wx.ICON_INFORMATION)

    def on_refresh(self, event):
        """刷新任务列表"""
        self.refresh_task_list()
