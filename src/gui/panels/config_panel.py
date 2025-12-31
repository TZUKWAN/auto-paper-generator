# -*- coding: utf-8 -*-
"""
配置面板
提供系统配置和模型配置界面
"""

import wx
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.gui.themes.themes import ThemeManager, get_theme_color
from src.core.config_manager import get_config_manager


class ConfigPanel(wx.Panel):
    """配置面板"""

    def __init__(self, parent):
        """初始化配置面板"""
        super().__init__(parent)
        self.config_manager = get_config_manager()
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 创建选项卡
        self.notebook = wx.Notebook(self)
        self.notebook.SetBackgroundColour(get_theme_color('bg_primary'))
        
        # 添加选项卡页面
        self.create_system_config_tab()
        self.create_model_config_tab()
        self.create_expert_review_tab()
        self.create_search_config_tab()
        
        sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)
        
        # 添加按钮
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        save_btn = wx.Button(self, label="保存配置", style=wx.BU_EXACTFIT)
        reset_btn = wx.Button(self, label="重置默认", style=wx.BU_EXACTFIT)
        refresh_btn = wx.Button(self, label="刷新", style=wx.BU_EXACTFIT)
        
        button_sizer.Add(save_btn, 0, wx.ALL, 5)
        button_sizer.Add(reset_btn, 0, wx.ALL, 5)
        button_sizer.Add(refresh_btn, 0, wx.ALL, 5)
        button_sizer.AddStretchSpacer()
        
        sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        self.SetSizer(sizer)
        
        # 绑定事件
        save_btn.Bind(wx.EVT_BUTTON, self.on_save)
        reset_btn.Bind(wx.EVT_BUTTON, self.on_reset)
        refresh_btn.Bind(wx.EVT_BUTTON, self.on_refresh)
        
        # 加载配置
        self.load_config()

    def create_system_config_tab(self):
        """创建系统配置选项卡"""
        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 配置项
        controls = []
        
        # 最大重试次数
        controls.append(self.create_labeled_control(
            panel, "最大重试次数:", 
            wx.SpinCtrl(panel, value="3", min=1, max=10),
            "system.max_retries"
        ))
        
        # 超时时间
        controls.append(self.create_labeled_control(
            panel, "超时时间(秒):", 
            wx.SpinCtrl(panel, value="60", min=10, max=300),
            "system.timeout"
        ))
        
        # 日志级别
        controls.append(self.create_labeled_control(
            panel, "日志级别:", 
            wx.ComboBox(panel, value="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"]),
            "system.log_level"
        ))
        
        # 添加控件到sizer
        for label, control, key in controls:
            sizer.Add(label, 0, wx.ALL | wx.EXPAND, 5)
            sizer.Add(control, 0, wx.ALL | wx.EXPAND, 5)
        
        sizer.AddStretchSpacer()
        panel.SetSizer(sizer)
        self.notebook.AddPage(panel, "系统配置")
        
        # 保存控件引用
        self.system_controls = [(control, key) for label, control, key in controls]

    def create_model_config_tab(self):
        """创建模型配置选项卡"""
        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 模型类型选择
        model_type_label = wx.StaticText(panel, label="主要模型:")
        model_type = wx.ComboBox(panel, value="ollama", 
                                choices=["ollama", "openai", "claude", "gemini"])
        sizer.Add(model_type_label, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(model_type, 0, wx.ALL | wx.EXPAND, 5)
        
        # 分隔线
        sizer.Add(wx.StaticLine(panel), 0, wx.EXPAND | wx.ALL, 5)
        
        # Ollama配置
        ollama_group = wx.StaticBox(panel, label="Ollama配置")
        ollama_sizer = wx.StaticBoxSizer(ollama_group, wx.VERTICAL)
        
        base_url = self.create_text_ctrl(panel, "Base URL:", 
                                        self.config_manager.get("models.ollama.base_url", "http://localhost:11434"))
        ollama_sizer.Add(base_url[0], 0, wx.ALL | wx.EXPAND, 5)
        ollama_sizer.Add(base_url[1], 0, wx.ALL | wx.EXPAND, 5)
        
        model_name = self.create_text_ctrl(panel, "模型名称:",
                                          self.config_manager.get("models.ollama.model", "llama3.1:8b"))
        ollama_sizer.Add(model_name[0], 0, wx.ALL | wx.EXPAND, 5)
        ollama_sizer.Add(model_name[1], 0, wx.ALL | wx.EXPAND, 5)
        
        temperature = self.create_spin_ctrl(panel, "Temperature:", 
                                          self.config_manager.get("models.ollama.temperature", 0.7), 0, 200)
        ollama_sizer.Add(temperature[0], 0, wx.ALL | wx.EXPAND, 5)
        ollama_sizer.Add(temperature[1], 0, wx.ALL | wx.EXPAND, 5)
        
        max_tokens = self.create_spin_ctrl(panel, "Max Tokens:",
                                         self.config_manager.get("models.ollama.max_tokens", 4000), 100, 8000)
        ollama_sizer.Add(max_tokens[0], 0, wx.ALL | wx.EXPAND, 5)
        ollama_sizer.Add(max_tokens[1], 0, wx.ALL | wx.EXPAND, 5)
        
        sizer.Add(ollama_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.AddStretchSpacer()
        panel.SetSizer(sizer)
        self.notebook.AddPage(panel, "模型配置")
        
        # 保存控件引用
        self.model_controls = {
            'model_type': model_type,
            'ollama': {
                'base_url': base_url[1],
                'model': model_name[1],
                'temperature': temperature[1],
                'max_tokens': max_tokens[1]
            }
        }

    def create_expert_review_tab(self):
        """创建专家审稿配置选项卡"""
        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 启用专家审稿
        enabled_chk = wx.CheckBox(panel, label="启用专家审稿")
        enabled_chk.SetValue(self.config_manager.get("expert_review.enabled", True))
        sizer.Add(enabled_chk, 0, wx.ALL, 5)
        
        # 审稿步骤
        steps_label = wx.StaticText(panel, label="审稿步骤:")
        steps_text = wx.TextCtrl(panel, value="结构审查,内容审查,语言审查", style=wx.TE_MULTILINE)
        sizer.Add(steps_label, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(steps_text, 1, wx.EXPAND | wx.ALL, 5)
        
        # 接受阈值
        threshold = self.create_spin_ctrl(panel, "接受阈值 (%):",
                                         int(self.config_manager.get("expert_review.acceptance_threshold", 0.8) * 100),
                                         0, 100)
        sizer.Add(threshold[0], 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(threshold[1], 0, wx.ALL | wx.EXPAND, 5)
        
        sizer.AddStretchSpacer()
        panel.SetSizer(sizer)
        self.notebook.AddPage(panel, "专家审稿")
        
        # 保存控件引用
        self.expert_controls = {
            'enabled': enabled_chk,
            'steps': steps_text,
            'threshold': threshold[1]
        }

    def create_search_config_tab(self):
        """创建搜索配置选项卡"""
        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 最大结果数
        max_results = self.create_spin_ctrl(panel, "最大搜索结果:",
                                            self.config_manager.get("search.max_results", 10), 1, 100)
        sizer.Add(max_results[0], 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(max_results[1], 0, wx.ALL | wx.EXPAND, 5)
        
        # 超时时间
        timeout = self.create_spin_ctrl(panel, "搜索超时(秒):",
                                      self.config_manager.get("search.timeout", 30), 5, 120)
        sizer.Add(timeout[0], 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(timeout[1], 0, wx.ALL | wx.EXPAND, 5)
        
        sizer.AddStretchSpacer()
        panel.SetSizer(sizer)
        self.notebook.AddPage(panel, "搜索配置")
        
        # 保存控件引用
        self.search_controls = {
            'max_results': max_results[1],
            'timeout': timeout[1]
        }

    def create_labeled_control(self, parent, label_text, control, key):
        """创建带标签的控件"""
        label = wx.StaticText(parent, label=label_text)
        return (label, control, key)

    def create_text_ctrl(self, parent, label_text, value):
        """创建文本输入控件"""
        label = wx.StaticText(parent, label=label_text)
        control = wx.TextCtrl(parent, value=value)
        return (label, control)

    def create_spin_ctrl(self, parent, label_text, value, min_val, max_val):
        """创建数值输入控件"""
        label = wx.StaticText(parent, label=label_text)
        control = wx.SpinCtrl(parent, value=str(value), min=min_val, max=max_val)
        return (label, control)

    def load_config(self):
        """加载配置到界面"""
        # 系统配置
        for control, key in self.system_controls:
            value = self.config_manager.get(key)
            if value is not None:
                if isinstance(control, wx.SpinCtrl):
                    control.SetValue(value)
                elif isinstance(control, wx.ComboBox):
                    control.SetValue(str(value))

    def save_config(self):
        """保存界面配置"""
        # 保存系统配置
        for control, key in self.system_controls:
            if isinstance(control, wx.SpinCtrl):
                self.config_manager.set(key, control.GetValue())
            elif isinstance(control, wx.ComboBox):
                self.config_manager.set(key, control.GetValue())
        
        # 保存模型配置
        self.config_manager.set('models.primary', self.model_controls['model_type'].GetValue())
        self.config_manager.set('models.ollama.base_url', self.model_controls['ollama']['base_url'].GetValue())
        self.config_manager.set('models.ollama.model', self.model_controls['ollama']['model'].GetValue())
        self.config_manager.set('models.ollama.temperature', 
                                self.model_controls['ollama']['temperature'].GetValue() / 100.0)
        self.config_manager.set('models.ollama.max_tokens', 
                                self.model_controls['ollama']['max_tokens'].GetValue())
        
        # 保存专家审稿配置
        self.config_manager.set('expert_review.enabled', 
                                self.expert_controls['enabled'].GetValue())
        steps_text = self.expert_controls['steps'].GetValue()
        self.config_manager.set('expert_review.review_steps', 
                                [s.strip() for s in steps_text.split(',')])
        self.config_manager.set('expert_review.acceptance_threshold',
                                self.expert_controls['threshold'].GetValue() / 100.0)
        
        # 保存搜索配置
        self.config_manager.set('search.max_results', 
                                self.search_controls['max_results'].GetValue())
        self.config_manager.set('search.timeout',
                                self.search_controls['timeout'].GetValue())
        
        # 保存到文件
        self.config_manager.save_config()

    def on_save(self, event):
        """保存按钮事件"""
        self.save_config()
        wx.MessageBox("配置已保存", "成功", wx.OK | wx.ICON_INFORMATION)

    def on_reset(self, event):
        """重置按钮事件"""
        result = wx.MessageBox("确定要重置为默认配置吗？", "确认", 
                             wx.YES_NO | wx.ICON_QUESTION)
        if result == wx.YES:
            self.config_manager.reset_to_defaults()
            self.load_config()
            wx.MessageBox("配置已重置", "成功", wx.OK | wx.ICON_INFORMATION)

    def on_refresh(self, event):
        """刷新按钮事件"""
        self.config_manager.reload()
        self.load_config()
        wx.MessageBox("配置已刷新", "成功", wx.OK | wx.ICON_INFORMATION)
