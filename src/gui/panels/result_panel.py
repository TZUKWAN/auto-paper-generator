# -*- coding: utf-8 -*-
"""
结果查看面板
展示任务执行结果
"""

import wx
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.gui.themes.themes import get_theme_color
from src.core.task_manager import get_task_manager, TaskStatus


class ResultPanel(wx.Panel):
    """结果查看面板"""

    def __init__(self, parent):
        """初始化结果面板"""
        super().__init__(parent)
        self.task_manager = get_task_manager()
        self.current_task = None
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 顶部工具栏
        toolbar = self.create_toolbar()
        sizer.Add(toolbar, 0, wx.EXPAND | wx.ALL, 5)
        
        # 任务选择
        select_panel = self.create_task_selector(sizer)
        
        # 结果显示
        self.create_result_display(sizer)
        
        self.SetSizer(sizer)

    def create_toolbar(self):
        """创建工具栏"""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 导出结果
        export_btn = wx.Button(panel, label="导出结果", style=wx.BU_EXACTFIT)
        export_btn.Bind(wx.EVT_BUTTON, self.on_export)
        
        # 复制结果
        copy_btn = wx.Button(panel, label="复制结果", style=wx.BU_EXACTFIT)
        copy_btn.Bind(wx.EVT_BUTTON, self.on_copy)
        
        # 清空结果
        clear_btn = wx.Button(panel, label="清空", style=wx.BU_EXACTFIT)
        clear_btn.Bind(wx.EVT_BUTTON, self.on_clear)
        
        # 打印
        print_btn = wx.Button(panel, label="打印", style=wx.BU_EXACTFIT)
        print_btn.Bind(wx.EVT_BUTTON, self.on_print)
        
        sizer.Add(export_btn, 0, wx.ALL, 2)
        sizer.Add(copy_btn, 0, wx.ALL, 2)
        sizer.Add(clear_btn, 0, wx.ALL, 2)
        sizer.Add(print_btn, 0, wx.ALL, 2)
        sizer.AddStretchSpacer()
        
        panel.SetSizer(sizer)
        return panel

    def create_task_selector(self, parent_sizer):
        """创建任务选择器"""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        label = wx.StaticText(panel, label="选择任务:")
        self.task_combo = wx.ComboBox(panel, value="", style=wx.CB_READONLY)
        
        # 填充任务列表
        self.refresh_task_list()
        
        sizer.Add(label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        sizer.Add(self.task_combo, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        
        # 刷新按钮
        refresh_btn = wx.Button(panel, label="刷新", style=wx.BU_EXACTFIT)
        refresh_btn.Bind(wx.EVT_BUTTON, self.on_refresh_tasks)
        sizer.Add(refresh_btn, 0, wx.ALL, 5)
        
        panel.SetSizer(sizer)
        parent_sizer.Add(panel, 0, wx.EXPAND | wx.ALL, 5)
        
        # 绑定选择事件
        self.task_combo.Bind(wx.EVT_COMBOBOX, self.on_task_selected)
        
        return panel

    def create_result_display(self, parent_sizer):
        """创建结果显示区"""
        # 使用选项卡切换不同视图
        self.notebook = wx.Notebook(self)
        
        # 文本视图
        text_panel = wx.Panel(self.notebook)
        text_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 标题
        title_label = wx.StaticText(text_panel, label="结果内容:")
        self.result_text = wx.TextCtrl(text_panel, value="", 
                                      style=wx.TE_MULTILINE | wx.TE_RICH | wx.HSCROLL)
        self.result_text.SetFont(wx.Font(9, wx.FONTFAMILY_MODERN, 
                                        wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        text_sizer.Add(title_label, 0, wx.ALL, 5)
        text_sizer.Add(self.result_text, 1, wx.EXPAND | wx.ALL, 5)
        text_panel.SetSizer(text_sizer)
        self.notebook.AddPage(text_panel, "文本视图")
        
        # HTML视图
        html_panel = wx.Panel(self.notebook)
        html_sizer = wx.BoxSizer(wx.VERTICAL)
        
        html_label = wx.StaticText(html_panel, label="HTML预览:")
        self.result_html = wx.html2.WebView.New(html_panel)
        if self.result_html:
            html_sizer.Add(html_label, 0, wx.ALL, 5)
            html_sizer.Add(self.result_html, 1, wx.EXPAND | wx.ALL, 5)
        else:
            error_label = wx.StaticText(html_panel, label="WebView不可用")
            html_sizer.Add(error_label, 0, wx.ALL, 10)
        
        html_panel.SetSizer(html_sizer)
        self.notebook.AddPage(html_panel, "HTML视图")
        
        # JSON视图
        json_panel = wx.Panel(self.notebook)
        json_sizer = wx.BoxSizer(wx.VERTICAL)
        
        json_label = wx.StaticText(json_panel, label="JSON数据:")
        self.result_json = wx.TextCtrl(json_panel, value="", 
                                      style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH)
        
        json_sizer.Add(json_label, 0, wx.ALL, 5)
        json_sizer.Add(self.result_json, 1, wx.EXPAND | wx.ALL, 5)
        json_panel.SetSizer(json_sizer)
        self.notebook.AddPage(json_panel, "JSON视图")
        
        parent_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)

    def refresh_task_list(self):
        """刷新任务列表"""
        self.task_combo.Clear()
        
        # 获取所有已完成的任务
        tasks = self.task_manager.get_all_tasks(TaskStatus.COMPLETED)
        for task in tasks:
            display_text = f"{task.title} ({task.task_id[:8]}...)"
            self.task_combo.Append(display_text, task.task_id)

    def on_task_selected(self, event):
        """任务选择事件"""
        task_id = self.task_combo.GetClientData(self.task_combo.GetSelection())
        if task_id:
            task = self.task_manager.get_task(task_id)
            if task:
                self.display_result(task)

    def display_result(self, task):
        """显示任务结果"""
        self.current_task = task
        
        # 文本视图
        result_str = self.format_result_as_text(task)
        self.result_text.SetValue(result_str)
        
        # HTML视图
        if self.result_html:
            html_str = self.format_result_as_html(task)
            self.result_html.SetPage(html_str, "")
        
        # JSON视图
        json_str = self.format_result_as_json(task)
        self.result_json.SetValue(json_str)

    def format_result_as_text(self, task) -> str:
        """格式化为文本"""
        lines = []
        lines.append("=" * 60)
        lines.append(f"任务标题: {task.title}")
        lines.append(f"任务ID: {task.task_id}")
        lines.append(f"任务类型: {task.task_type}")
        lines.append(f"状态: {task.status.value}")
        lines.append(f"进度: {task.progress}%")
        lines.append(f"创建时间: {task.created_at}")
        if task.started_at:
            lines.append(f"开始时间: {task.started_at}")
        if task.completed_at:
            lines.append(f"完成时间: {task.completed_at}")
        lines.append("=" * 60)
        lines.append("\n任务结果:")
        lines.append("-" * 60)
        
        if task.result:
            if isinstance(task.result, dict):
                for key, value in task.result.items():
                    lines.append(f"{key}: {value}")
            elif isinstance(task.result, list):
                for item in task.result:
                    lines.append(f"- {item}")
            else:
                lines.append(str(task.result))
        else:
            lines.append("暂无结果")
        
        if task.error:
            lines.append("\n" + "-" * 60)
            lines.append(f"错误信息: {task.error}")
        
        return "\n".join(lines)

    def format_result_as_html(self, task) -> str:
        """格式化为HTML"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{task.title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5; }}
                .container {{ background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                h1 {{ color: #0078D7; }}
                .info {{ background-color: #f0f0f0; padding: 10px; border-radius: 4px; margin: 10px 0; }}
                .result {{ margin-top: 20px; }}
                pre {{ background-color: #f9f9f9; padding: 10px; border-radius: 4px; overflow-x: auto; }}
                .error {{ background-color: #ffe6e6; padding: 10px; border-radius: 4px; color: #d13438; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{task.title}</h1>
                <div class="info">
                    <p><strong>任务ID:</strong> {task.task_id}</p>
                    <p><strong>任务类型:</strong> {task.task_type}</p>
                    <p><strong>状态:</strong> {task.status.value}</p>
                    <p><strong>进度:</strong> {task.progress}%</p>
                </div>
                <div class="result">
                    <h2>任务结果</h2>
                    <pre>{str(task.result) if task.result else '暂无结果'}</pre>
                </div>
                {f'<div class="error"><strong>错误信息:</strong> {task.error}</div>' if task.error else ''}
            </div>
        </body>
        </html>
        """
        return html

    def format_result_as_json(self, task) -> str:
        """格式化为JSON"""
        import json
        data = {
            'task_id': task.task_id,
            'title': task.title,
            'description': task.description,
            'task_type': task.task_type,
            'status': task.status.value,
            'progress': task.progress,
            'created_at': task.created_at.isoformat(),
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'result': task.result,
            'error': task.error
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    def on_export(self, event):
        """导出结果"""
        if not self.current_task:
            wx.MessageBox("请先选择任务", "提示", wx.OK | wx.ICON_WARNING)
            return
        
        # 保存对话框
        wildcard = "Text Files (*.txt)|*.txt|All Files (*.*)|*.*"
        dlg = wx.FileDialog(self, "导出结果", wildcard=wildcard, 
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        
        if dlg.ShowModal() == wx.ID_OK:
            filepath = dlg.GetPath()
            try:
                content = self.format_result_as_text(self.current_task)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                wx.MessageBox("导出成功", "成功", wx.OK | wx.ICON_INFORMATION)
            except Exception as e:
                wx.MessageBox(f"导出失败: {e}", "错误", wx.OK | wx.ICON_ERROR)
        
        dlg.Destroy()

    def on_copy(self, event):
        """复制结果"""
        if not self.current_task:
            wx.MessageBox("请先选择任务", "提示", wx.OK | wx.ICON_WARNING)
            return
        
        content = self.format_result_as_text(self.current_task)
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(content))
            wx.TheClipboard.Close()
            wx.MessageBox("已复制到剪贴板", "成功", wx.OK | wx.ICON_INFORMATION)

    def on_clear(self, event):
        """清空结果"""
        self.result_text.SetValue("")
        self.result_json.SetValue("")
        if self.result_html:
            self.result_html.SetPage("", "")
        self.current_task = None

    def on_print(self, event):
        """打印结果"""
        wx.MessageBox("打印功能开发中...", "提示", wx.OK | wx.ICON_INFORMATION)

    def on_refresh_tasks(self, event):
        """刷新任务列表"""
        self.refresh_task_list()
