"""
AI Academic Assistant - wxPython GUI (重构版)
重构内容：
- 移除PDF上传功能
- 添加历史记录面板
- 添加及格分数设置
- 添加大纲编辑对话框
"""
import wx
import wx.adv
import wx.lib.newevent
import sys
import threading
import logging
import os
import queue
import json
from datetime import datetime
import webbrowser
import asyncio

# 设置 logger
logger = logging.getLogger(__name__)

# Custom Events
LogEvent, EVT_LOG = wx.lib.newevent.NewEvent()
DoneEvent, EVT_DONE = wx.lib.newevent.NewEvent()
OutlineEvent, EVT_OUTLINE = wx.lib.newevent.NewEvent()
ProgressEvent, EVT_PROGRESS = wx.lib.newevent.NewEvent()  # 进度更新事件

# Import system modules
try:
    from main import main as generate_paper_main
    from config import config
    from core.project_manager import ProjectLiteratureManager
except ImportError as e:
    print(f"Import Error: {e}")

# 历史记录管理
# 历史记录管理
if getattr(sys, 'frozen', False):
    # Frozen: use executable directory
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    # Dev: use script directory
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

HISTORY_FILE = os.path.join(BASE_DIR, "output", "history.json")

def load_history():
    """加载历史记录"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_history(history):
    """保存历史记录"""
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def add_to_history(title, files):
    """添加到历史记录"""
    history = load_history()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if title not in history:
        history[title] = []
    history[title].append({
        'timestamp': timestamp,
        'files': files
    })
    save_history(history)


class OutlineEditorDialog(wx.Dialog):
    """大纲编辑对话框"""
    
    def __init__(self, parent, outline_data):
        super().__init__(parent, title="大纲预览与编辑", size=(800, 700),
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.outline_data = outline_data
        self.result = None
        self.init_ui()
        self.Center()
    
    def init_ui(self):
        panel = wx.ScrolledWindow(self)
        panel.SetScrollRate(5, 5)
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 说明文字
        intro = wx.StaticText(panel, label="请检查并编辑AI生成的大纲。您可以修改标题和思路，确认后将继续生成论文正文。")
        intro.SetForegroundColour(wx.Colour(100, 100, 100))
        main_sizer.Add(intro, 0, wx.ALL, 10)
        
        # 引言部分
        sb_intro = wx.StaticBox(panel, label="引言")
        sbs_intro = wx.StaticBoxSizer(sb_intro, wx.VERTICAL)
        
        grid_intro = wx.FlexGridSizer(2, 2, 5, 10)
        grid_intro.AddGrowableCol(1, 1)
        grid_intro.Add(wx.StaticText(panel, label="标题:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.intro_title = wx.TextCtrl(panel, value=self.outline_data.get('introduction', {}).get('title', '一、引言'))
        grid_intro.Add(self.intro_title, 1, wx.EXPAND)
        grid_intro.Add(wx.StaticText(panel, label="思路:"), 0, wx.ALIGN_TOP)
        self.intro_idea = wx.TextCtrl(panel, value=self.outline_data.get('introduction', {}).get('idea', ''), 
                                       style=wx.TE_MULTILINE, size=(-1, 60))
        grid_intro.Add(self.intro_idea, 1, wx.EXPAND)
        sbs_intro.Add(grid_intro, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(sbs_intro, 0, wx.EXPAND | wx.ALL, 10)
        
        # 动态章节 (3个主体章节，每个3个二级标题)
        self.chapter_controls = []
        chapters = self.outline_data.get('chapters', [])
        
        for i in range(3):
            chapter = chapters[i] if i < len(chapters) else {'title': f'章节{i+2}', 'subsections': []}
            
            sb_ch = wx.StaticBox(panel, label=f"主体章节 {i+1}")
            sbs_ch = wx.StaticBoxSizer(sb_ch, wx.VERTICAL)
            
            # 章节标题
            hbox_title = wx.BoxSizer(wx.HORIZONTAL)
            hbox_title.Add(wx.StaticText(panel, label="章节标题:"), 0, wx.ALIGN_CENTER_VERTICAL)
            ch_title = wx.TextCtrl(panel, value=chapter.get('title', ''))
            hbox_title.Add(ch_title, 1, wx.EXPAND | wx.LEFT, 10)
            sbs_ch.Add(hbox_title, 0, wx.EXPAND | wx.ALL, 5)
            
            subsection_controls = []
            subsections = chapter.get('subsections', [])
            
            for j in range(3):
                sub = subsections[j] if j < len(subsections) else {'title': '', 'idea': ''}
                
                sub_sizer = wx.BoxSizer(wx.HORIZONTAL)
                sub_sizer.Add(wx.StaticText(panel, label=f"  二级{j+1}:"), 0, wx.ALIGN_CENTER_VERTICAL)
                
                sub_title = wx.TextCtrl(panel, value=sub.get('title', ''), size=(250, -1))
                sub_sizer.Add(sub_title, 0, wx.LEFT, 5)
                
                sub_sizer.Add(wx.StaticText(panel, label="思路:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
                sub_idea = wx.TextCtrl(panel, value=sub.get('idea', ''))
                sub_sizer.Add(sub_idea, 1, wx.EXPAND | wx.LEFT, 5)
                
                sbs_ch.Add(sub_sizer, 0, wx.EXPAND | wx.ALL, 3)
                subsection_controls.append({'title': sub_title, 'idea': sub_idea})
            
            main_sizer.Add(sbs_ch, 0, wx.EXPAND | wx.ALL, 10)
            self.chapter_controls.append({'title': ch_title, 'subsections': subsection_controls})
        
        # 结论部分
        sb_conc = wx.StaticBox(panel, label="结论")
        sbs_conc = wx.StaticBoxSizer(sb_conc, wx.VERTICAL)
        
        grid_conc = wx.FlexGridSizer(2, 2, 5, 10)
        grid_conc.AddGrowableCol(1, 1)
        grid_conc.Add(wx.StaticText(panel, label="标题:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.conc_title = wx.TextCtrl(panel, value=self.outline_data.get('conclusion', {}).get('title', '结论'))
        grid_conc.Add(self.conc_title, 1, wx.EXPAND)
        grid_conc.Add(wx.StaticText(panel, label="思路:"), 0, wx.ALIGN_TOP)
        self.conc_idea = wx.TextCtrl(panel, value=self.outline_data.get('conclusion', {}).get('idea', ''),
                                      style=wx.TE_MULTILINE, size=(-1, 60))
        grid_conc.Add(self.conc_idea, 1, wx.EXPAND)
        sbs_conc.Add(grid_conc, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(sbs_conc, 0, wx.EXPAND | wx.ALL, 10)
        
        # 按钮
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_confirm = wx.Button(panel, wx.ID_OK, "确认并开始生成")
        btn_cancel = wx.Button(panel, wx.ID_CANCEL, "取消")
        btn_sizer.Add(btn_confirm, 0, wx.ALL, 5)
        btn_sizer.Add(btn_cancel, 0, wx.ALL, 5)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        panel.SetSizer(main_sizer)
        
        btn_confirm.Bind(wx.EVT_BUTTON, self.on_confirm)
        btn_cancel.Bind(wx.EVT_BUTTON, self.on_cancel)
    
    def on_confirm(self, event):
        """收集编辑后的大纲数据"""
        self.result = {
            'introduction': {
                'title': self.intro_title.GetValue(),
                'idea': self.intro_idea.GetValue()
            },
            'chapters': [],
            'conclusion': {
                'title': self.conc_title.GetValue(),
                'idea': self.conc_idea.GetValue()
            }
        }
        
        for ch_ctrl in self.chapter_controls:
            chapter = {
                'title': ch_ctrl['title'].GetValue(),
                'subsections': []
            }
            for sub_ctrl in ch_ctrl['subsections']:
                chapter['subsections'].append({
                    'title': sub_ctrl['title'].GetValue(),
                    'idea': sub_ctrl['idea'].GetValue()
                })
            self.result['chapters'].append(chapter)
        
        self.EndModal(wx.ID_OK)
    
    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)


class WorkerThread(threading.Thread):
    """后台工作线程"""
    
    def __init__(self, notify_window, project_name, idea, lit_path, outline_data=None):
        threading.Thread.__init__(self)
        self.notify_window = notify_window
        self.project_name = project_name
        self.idea = idea
        self.lit_path = lit_path
        self.outline_data = outline_data
        self._stop_event = threading.Event()
    
    def _create_progress_callback(self):
        """创建进度回调函数"""
        def progress_callback(progress, stage=None, word_count=None, api_calls=None):
            """发送进度事件到UI"""
            wx.PostEvent(self.notify_window, ProgressEvent(
                progress=progress,
                stage=stage or "",
                word_count=word_count,
                api_calls=api_calls
            ))
        return progress_callback

    def run(self):
        try:
            # 创建进度回调
            progress_callback = self._create_progress_callback()
            
            # 发送初始进度
            progress_callback(5, "初始化生成引擎")
            
            # Run the main generation logic
            result = generate_paper_main(
                project_name=self.project_name,
                extra_idea=self.idea,
                literature_txt_path=self.lit_path if self.lit_path else None,
                outline_data=self.outline_data,
                progress_callback=progress_callback  # 传递进度回调
            )
            
            # 完成时发送100%进度
            progress_callback(100, "生成完成")
            
            # 检查 main 返回的字典中的 success 状态
            if isinstance(result, dict) and not result.get('success', True):
                wx.PostEvent(self.notify_window, DoneEvent(result={"success": False, "error": result.get('error', '未知错误')}))
            else:
                wx.PostEvent(self.notify_window, DoneEvent(result={"success": True, "data": result}))
                
        except Exception as e:
            wx.PostEvent(self.notify_window, DoneEvent(result={"success": False, "error": str(e)}))


class OutlineWorkerThread(threading.Thread):
    """大纲生成线程 - 先生成大纲，再通知主界面显示编辑对话框"""
    
    def __init__(self, notify_window, project_name, idea, lit_path):
        threading.Thread.__init__(self)
        self.notify_window = notify_window
        self.project_name = project_name
        self.idea = idea
        self.lit_path = lit_path
    
    def run(self):
        try:
            from core.model_router import ModelRouter
            
            # 初始化模型路由
            router = ModelRouter(config)
            
            # 生成大纲的提示词
            prompt = f"""根据以下论文选题，设计主体内容大纲。

论文题目：{self.project_name}
核心思路：{self.idea if self.idea else '无'}

主体内容分为三部分（不包括引言和结论），三个部分之间要逻辑严谨，层层递进。
每个主体部分包含3个二级标题。

【输出格式】严格按照以下格式输出：

引言标题: 一、引言
引言思路: [简要说明引言的写作方向]

主体1标题: 二、[具体标题]
二级标题1: [具体的学术标题]
二级标题1思路: [核心论点]
二级标题2: [具体的学术标题]
二级标题2思路: [核心论点]
二级标题3: [具体的学术标题]
二级标题3思路: [核心论点]

主体2标题: 三、[具体标题]
二级标题1: [具体的学术标题]
二级标题1思路: [核心论点]
二级标题2: [具体的学术标题]
二级标题2思路: [核心论点]
二级标题3: [具体的学术标题]
二级标题3思路: [核心论点]

主体3标题: 四、[具体标题]
二级标题1: [具体的学术标题]
二级标题1思路: [核心论点]
二级标题2: [具体的学术标题]
二级标题2思路: [核心论点]
二级标题3: [具体的学术标题]
二级标题3思路: [核心论点]

结论标题: 结论
结论思路: [简要说明结论的写作方向]

【重要】请直接输出大纲内容，不要有任何开场白或额外说明。
"""
            wx.PostEvent(self.notify_window, LogEvent(message="📝 正在调用AI生成大纲...\n"))
            
            # 带重试的大纲生成
            max_retries = 3
            last_error = None
            response = None
            
            for attempt in range(max_retries):
                try:
                    response = router.generate(prompt, context="你是学术论文大纲设计专家", max_tokens=8000)
                    if response and len(response.strip()) > 100:
                        break
                    else:
                        wx.PostEvent(self.notify_window, LogEvent(message=f"⚠️ 大纲响应过短，重试({attempt+1}/{max_retries})...\n"))
                except Exception as retry_e:
                    last_error = retry_e
                    wx.PostEvent(self.notify_window, LogEvent(message=f"⚠️ 大纲生成出错({attempt+1}/{max_retries}): {str(retry_e)[:100]}\n"))
                    import time
                    time.sleep(5)  # 等待5秒后重试
            
            if not response or len(response.strip()) < 100:
                raise Exception(f"大纲生成失败，响应为空或过短。最后错误: {last_error}")
            
            # 解析AI返回的大纲
            outline_data = self._parse_outline_response(response)
            
            wx.PostEvent(self.notify_window, LogEvent(message="✅ 大纲生成完成！\n"))
            
            # 发送大纲事件
            wx.PostEvent(self.notify_window, LogEvent(message="🔔 正在发送大纲事件到主界面...\n"))
            wx.PostEvent(self.notify_window, OutlineEvent(outline=outline_data, success=True))
            wx.PostEvent(self.notify_window, LogEvent(message="✔️ 事件已发送，等待对话框弹出...\n"))
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"大纲生成异常: {error_details}")
            wx.PostEvent(self.notify_window, LogEvent(message=f"❌ 大纲生成失败: {str(e)}\n"))
            wx.PostEvent(self.notify_window, OutlineEvent(outline=None, success=False, error=str(e)))
    
    def _parse_outline_response(self, response):
        """解析AI返回的大纲格式 - 超强健壮版"""
        import re
        
        # 默认结构
        outline = {
            'introduction': {'title': '一、引言', 'idea': ''},
            'chapters': [
                {'title': '二、', 'subsections': [{'title': '', 'idea': ''} for _ in range(3)]},
                {'title': '三、', 'subsections': [{'title': '', 'idea': ''} for _ in range(3)]},
                {'title': '四、', 'subsections': [{'title': '', 'idea': ''} for _ in range(3)]}
            ],
            'conclusion': {'title': '结论', 'idea': ''}
        }
        
        # 统一替换中文冒号和全角符号
        response = response.replace('：', ':').replace('（', '(').replace('）', ')')
        
        # 按主体章节分块解析
        # 先提取引言（多模式匹配）
        intro_patterns = [
            r'引言标题[:\s]*(.+?)(?:\n|$)',
            r'一[、.．]\s*引言[:\s]*(.+?)(?:\n|$)',
        ]
        for pattern in intro_patterns:
            intro_match = re.search(pattern, response)
            if intro_match and intro_match.group(1).strip():
                outline['introduction']['title'] = intro_match.group(1).strip()
                break
        
        intro_idea_patterns = [
            r'引言思路[:\s]*(.+?)(?:\n|$)',
            r'引言\s*[:：]?\s*思路[:\s]*(.+?)(?:\n|$)',
            r'引言(?:写作)?方向[:\s]*(.+?)(?:\n|$)',
        ]
        for pattern in intro_idea_patterns:
            intro_idea_match = re.search(pattern, response)
            if intro_idea_match and intro_idea_match.group(1).strip():
                outline['introduction']['idea'] = intro_idea_match.group(1).strip()
                break
        
        # 引言思路保底
        if not outline['introduction'].get('idea'):
            outline['introduction']['idea'] = f"阐述{self.project_name}的研究背景、现实意义、研究问题与方法。"
            logger.warning("引言思路解析失败，使用自动生成的默认思路")
        
        # 提取主体章节（支持"主体N标题"或"第N部分"等多种格式）
        for ch_idx in range(3):
            patterns = [
                rf'主体{ch_idx+1}标题[:\s]*(.+?)(?:\n|$)',
                rf'第{["一","二","三"][ch_idx]}部分[:\s]*(.+?)(?:\n|$)',
            ]
            for pattern in patterns:
                match = re.search(pattern, response)
                if match:
                    outline['chapters'][ch_idx]['title'] = match.group(1).strip()
                    break
        
        # 逐行解析二级标题，跟踪当前主体章节
        lines = response.strip().split('\n')
        current_chapter_idx = -1
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测主体章节切换
            if re.search(r'主体1标题', line):
                current_chapter_idx = 0
            elif re.search(r'主体2标题', line):
                current_chapter_idx = 1
            elif re.search(r'主体3标题', line):
                current_chapter_idx = 2
            
            # 解析二级标题思路（必须在标题之前匹配，因为"二级标题1思路"包含"二级标题1"）
            if re.search(r'二级标题\s*(\d)\s*思路', line) and ':' in line:
                match = re.search(r'二级标题\s*(\d)', line)
                if match:
                    sub_idx = int(match.group(1)) - 1
                    if 0 <= current_chapter_idx < 3 and 0 <= sub_idx < 3:
                        idea = line.split(':', 1)[1].strip()
                        outline['chapters'][current_chapter_idx]['subsections'][sub_idx]['idea'] = idea
            
            # 解析二级标题（不含"思路"）
            elif re.search(r'二级标题\s*(\d)', line) and '思路' not in line and ':' in line:
                match = re.search(r'二级标题\s*(\d)', line)
                if match:
                    sub_idx = int(match.group(1)) - 1
                    if 0 <= current_chapter_idx < 3 and 0 <= sub_idx < 3:
                        title = line.split(':', 1)[1].strip()
                        outline['chapters'][current_chapter_idx]['subsections'][sub_idx]['title'] = title
        
        # 提取结论 - 超级健壮版（多模式匹配）
        # 1. 尝试标准格式
        concl_title_patterns = [
            r'结论标题[:：]\s*(.+?)(?:\n|$)',
            r'(?:五|六)?[、.．]?\s*结论[:：]?\s*(.+?)(?:\n|$)',
            r'Conclusion\s*(?:Title)?[:：]\s*(.+?)(?:\n|$)',
        ]
        for pattern in concl_title_patterns:
            concl_match = re.search(pattern, response, re.IGNORECASE)
            if concl_match and concl_match.group(1).strip():
                outline['conclusion']['title'] = concl_match.group(1).strip()
                logger.debug(f"结论标题匹配成功: {concl_match.group(1).strip()}")
                break
        
        # 如果标题还是空的，设置默认值
        if not outline['conclusion'].get('title'):
            outline['conclusion']['title'] = '结论'
            logger.warning("结论标题解析失败，使用默认值")
            
        # 2. 尝试多种结论思路格式
        concl_idea_patterns = [
            r'结论思路[:：]\s*(.+?)(?:\n|$)',
            r'结论\s*[:：]?\s*思路[:：]\s*(.+?)(?:\n|$)',
            r'结论(?:部分|章节)?(?:的)?(?:写作)?思路[:：]\s*(.+?)(?:\n|$)',
            r'结论(?:部分|章节)?(?:内容|要点|方向)[:：]\s*(.+?)(?:\n|$)',
            r'Conclusion\s*(?:Idea|思路)[:：]\s*(.+?)(?:\n|$)',
        ]
        for pattern in concl_idea_patterns:
            concl_idea_match = re.search(pattern, response, re.IGNORECASE)
            if concl_idea_match and concl_idea_match.group(1).strip():
                outline['conclusion']['idea'] = concl_idea_match.group(1).strip()
                logger.debug(f"结论思路匹配成功: {concl_idea_match.group(1).strip()[:50]}...")
                break
        
        # 3. 如果仍然没有找到结论思路，尝试从全文末尾提取
        if not outline['conclusion'].get('idea'):
            # 查找"结论"后面的第一个非空行作为思路
            concl_section = re.search(r'结论[标题]*[:：].*?\n(.+?)(?:\n\n|$)', response, re.DOTALL)
            if concl_section:
                potential_idea = concl_section.group(1).strip().split('\n')[0]
                if potential_idea and not potential_idea.startswith('主体') and len(potential_idea) > 5:
                    outline['conclusion']['idea'] = potential_idea
                    logger.debug(f"结论思路（从上下文推断）: {potential_idea[:50]}...")
        
        # 4. 最终保底：如果还是没有，使用基于论文主题的默认思路
        if not outline['conclusion'].get('idea'):
            outline['conclusion']['idea'] = f"总结全文研究发现，阐述{self.project_name}的理论贡献与实践意义，并指出未来研究方向。"
            logger.warning(f"结论思路解析失败，使用自动生成的默认思路")
        
        # 日志输出解析结果
        wx.PostEvent(self.notify_window, LogEvent(message=f"📋 解析大纲:\n"))
        wx.PostEvent(self.notify_window, LogEvent(message=f"   引言: {outline['introduction']['title'][:30]}... 思路长度={len(outline['introduction'].get('idea', ''))}\n"))
        for i, ch in enumerate(outline['chapters']):
            filled_subs = len([s for s in ch['subsections'] if s['title']])
            filled_ideas = len([s for s in ch['subsections'] if s['idea']])
            wx.PostEvent(self.notify_window, LogEvent(message=f"   章节{i+1}: {ch['title'][:25]}... ({filled_subs}标题/{filled_ideas}思路)\n"))
        wx.PostEvent(self.notify_window, LogEvent(message=f"   结论: {outline['conclusion']['title'][:20]}... 思路长度={len(outline['conclusion'].get('idea', ''))}\n"))
        
        return outline


class MainFrame(wx.Frame):
    """主窗口"""
    
    def __init__(self):
        super().__init__(None, title="AI Academic Assistant - 桌面版 (Pro)", size=(1100, 850))
        self.SetMinSize((900, 700))
        
        # 保存待处理的数据
        self.pending_title = ""
        self.pending_idea = ""
        self.pending_lit_path = ""
        
        self.init_ui()
        self.Center()
        self.Show()

        # Event Bindings
        self.Bind(EVT_LOG, self.on_log_update)
        self.Bind(EVT_DONE, self.on_task_done)
        self.Bind(EVT_OUTLINE, self.on_outline_ready)
        self.Bind(EVT_PROGRESS, self.on_progress_update)  # 进度事件绑定

        # Setup logging handler to redirect to GUI
        self.setup_logging()
        
        # 进度统计变量
        self.generation_start_time = None
        self.generation_api_calls = 0
        self.generation_word_count = 0

    def setup_logging(self):
        self.log_queue = queue.Queue()
        
        class QueueHandler(logging.Handler):
            def __init__(self, notify_window):
                super().__init__()
                self.notify_window = notify_window

            def emit(self, record):
                msg = self.format(record)
                wx.PostEvent(self.notify_window, LogEvent(message=msg + "\n"))

        root_logger = logging.getLogger()
        handler = QueueHandler(self)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

    def init_ui(self):
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.notebook = wx.Notebook(panel)
        
        # Tabs
        self.task_tab = wx.Panel(self.notebook)
        self.create_task_tab(self.task_tab)
        self.notebook.AddPage(self.task_tab, "任务与生成")

        self.config_tab = wx.Panel(self.notebook)
        self.create_config_tab(self.config_tab)
        self.notebook.AddPage(self.config_tab, "模型配置")
        
        self.search_tab = wx.Panel(self.notebook)
        self.create_search_tab(self.search_tab)
        self.notebook.AddPage(self.search_tab, "网络检索")

        main_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(main_sizer)

    def create_task_tab(self, parent):
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 1. Project Info
        sb_proj = wx.StaticBox(parent, label="1. 项目信息")
        sbs_proj = wx.StaticBoxSizer(sb_proj, wx.VERTICAL)
        
        grid_proj = wx.FlexGridSizer(2, 2, 10, 10)
        grid_proj.AddGrowableCol(1, 1)

        grid_proj.Add(wx.StaticText(parent, label="论文题目:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.title_input = wx.TextCtrl(parent)
        grid_proj.Add(self.title_input, 1, wx.EXPAND)

        grid_proj.Add(wx.StaticText(parent, label="核心思路:"), 0, wx.ALIGN_TOP)
        self.idea_input = wx.TextCtrl(parent, style=wx.TE_MULTILINE, size=(-1, 60))
        grid_proj.Add(self.idea_input, 1, wx.EXPAND)
        
        sbs_proj.Add(grid_proj, 1, wx.EXPAND | wx.ALL, 10)
        sizer.Add(sbs_proj, 0, wx.EXPAND | wx.ALL, 10)

        # 2. Files (只保留文献池，移除PDF)
        sb_files = wx.StaticBox(parent, label="2. 文献池上传")
        sbs_files = wx.StaticBoxSizer(sb_files, wx.VERTICAL)

        hbox_lit = wx.BoxSizer(wx.HORIZONTAL)
        hbox_lit.Add(wx.StaticText(parent, label="文献池 (.txt):"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.lit_path_ctrl = wx.TextCtrl(parent, style=wx.TE_READONLY)
        hbox_lit.Add(self.lit_path_ctrl, 1, wx.EXPAND | wx.LEFT, 10)
        btn_lit = wx.Button(parent, label="浏览...")
        btn_lit.Bind(wx.EVT_BUTTON, self.on_select_lit)
        hbox_lit.Add(btn_lit, 0, wx.LEFT, 5)

        sbs_files.Add(hbox_lit, 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(sbs_files, 0, wx.EXPAND | wx.ALL, 10)

        # 3. 快捷模式切换
        sb_mode = wx.StaticBox(parent, label="3. 生成模式")
        sbs_mode = wx.StaticBoxSizer(sb_mode, wx.HORIZONTAL)
        
        self.mode_fast = wx.RadioButton(parent, label="⚡ 快速模式", style=wx.RB_GROUP)
        self.mode_balanced = wx.RadioButton(parent, label="⚖️ 均衡模式")
        self.mode_quality = wx.RadioButton(parent, label="🎯 质量模式")
        
        # 默认选择均衡模式
        self.mode_balanced.SetValue(True)
        
        # 模式提示
        mode_tips = {
            'fast': "关闭思考链，1-5秒/次",
            'balanced': "关闭思考链，标准参数",  
            'quality': "开启思考链，20-60秒/次"
        }
        
        self.mode_fast.SetToolTip(mode_tips['fast'])
        self.mode_balanced.SetToolTip(mode_tips['balanced'])
        self.mode_quality.SetToolTip(mode_tips['quality'])
        
        # 绑定模式切换事件
        self.mode_fast.Bind(wx.EVT_RADIOBUTTON, self.on_mode_changed)
        self.mode_balanced.Bind(wx.EVT_RADIOBUTTON, self.on_mode_changed)
        self.mode_quality.Bind(wx.EVT_RADIOBUTTON, self.on_mode_changed)
        
        sbs_mode.Add(self.mode_fast, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 10)
        sbs_mode.Add(self.mode_balanced, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 10)
        sbs_mode.Add(self.mode_quality, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 10)
        
        # 模式说明标签
        self.mode_tip_label = wx.StaticText(parent, label="💡 均衡：速度与质量的最佳平衡")
        self.mode_tip_label.SetForegroundColour(wx.Colour(80, 80, 80))
        sbs_mode.Add(self.mode_tip_label, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 10)
        
        sizer.Add(sbs_mode, 0, wx.EXPAND | wx.ALL, 10)

        # 4. 进度显示面板
        sb_progress = wx.StaticBox(parent, label="4. 生成进度")
        sbs_progress = wx.StaticBoxSizer(sb_progress, wx.VERTICAL)
        
        # 进度条
        self.progress_bar = wx.Gauge(parent, range=100, size=(-1, 20))
        self.progress_bar.SetValue(0)
        sbs_progress.Add(self.progress_bar, 0, wx.EXPAND | wx.ALL, 5)
        
        # 进度文本
        progress_text_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.progress_stage_label = wx.StaticText(parent, label="当前阶段: 等待开始")
        self.progress_percent_label = wx.StaticText(parent, label="0%")
        progress_text_sizer.Add(self.progress_stage_label, 1, wx.ALIGN_CENTER_VERTICAL)
        progress_text_sizer.Add(self.progress_percent_label, 0, wx.ALIGN_CENTER_VERTICAL)
        sbs_progress.Add(progress_text_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # 统计信息
        stats_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.stats_words_label = wx.StaticText(parent, label="已生成: 0 字")
        self.stats_api_label = wx.StaticText(parent, label="API调用: 0 次")
        self.stats_time_label = wx.StaticText(parent, label="耗时: 0 秒")
        stats_sizer.Add(self.stats_words_label, 1, wx.ALIGN_CENTER_VERTICAL)
        stats_sizer.Add(self.stats_api_label, 1, wx.ALIGN_CENTER_VERTICAL)
        stats_sizer.Add(self.stats_time_label, 1, wx.ALIGN_CENTER_VERTICAL)
        sbs_progress.Add(stats_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        sizer.Add(sbs_progress, 0, wx.EXPAND | wx.ALL, 10)

        # 5. Action
        self.start_btn = wx.Button(parent, label="🚀 开始生成论文", size=(200, 50))
        self.start_btn.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.start_btn.Bind(wx.EVT_BUTTON, self.on_start)
        sizer.Add(self.start_btn, 0, wx.ALIGN_CENTER | wx.ALL, 15)

        # 4. 日志和历史记录区域 (上下分割)
        splitter = wx.SplitterWindow(parent, style=wx.SP_LIVE_UPDATE)
        
        # 上半部分：日志
        log_panel = wx.Panel(splitter)
        log_sizer = wx.BoxSizer(wx.VERTICAL)
        log_label = wx.StaticText(log_panel, label="生成日志")
        log_label.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        log_sizer.Add(log_label, 0, wx.ALL, 5)
        self.log_ctrl = wx.TextCtrl(log_panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        self.log_ctrl.SetFont(wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        log_sizer.Add(self.log_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        log_panel.SetSizer(log_sizer)
        
        # 下半部分：历史记录
        history_panel = wx.Panel(splitter)
        history_sizer = wx.BoxSizer(wx.VERTICAL)
        history_label = wx.StaticText(history_panel, label="历史生成记录")
        history_label.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        history_sizer.Add(history_label, 0, wx.ALL, 5)
        
        self.history_tree = wx.TreeCtrl(history_panel, style=wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT)
        self.history_tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_history_item_activated)
        self.history_tree.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.on_history_right_click)  # 右键菜单
        history_sizer.Add(self.history_tree, 1, wx.EXPAND | wx.ALL, 5)
        
        # 历史记录按钮栏
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        btn_refresh = wx.Button(history_panel, label="🔄 刷新", size=(70, -1))
        btn_refresh.Bind(wx.EVT_BUTTON, self.on_refresh_history)
        btn_sizer.Add(btn_refresh, 0, wx.ALL, 3)
        
        btn_open_dir = wx.Button(history_panel, label="📂 打开目录", size=(85, -1))
        btn_open_dir.Bind(wx.EVT_BUTTON, self.on_open_output_dir)
        btn_sizer.Add(btn_open_dir, 0, wx.ALL, 3)
        
        btn_delete = wx.Button(history_panel, label="🗑 删除记录", size=(85, -1))
        btn_delete.Bind(wx.EVT_BUTTON, self.on_delete_history)
        btn_sizer.Add(btn_delete, 0, wx.ALL, 3)
        
        history_sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 2)
        
        history_panel.SetSizer(history_sizer)
        
        splitter.SplitHorizontally(log_panel, history_panel, 200)
        splitter.SetMinimumPaneSize(100)
        
        sizer.Add(splitter, 1, wx.EXPAND | wx.ALL, 10)
        
        parent.SetSizer(sizer)
        
        # 加载历史记录
        self.refresh_history_tree()

    def create_config_tab(self, parent):
        # 使用滚动面板以容纳更多内容
        scroll = wx.ScrolledWindow(parent)
        scroll.SetScrollRate(5, 5)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # ==================== 1. 专家审稿设置 ====================
        sb_expert = wx.StaticBox(scroll, label="1. 专家审稿")
        sbs_expert = wx.StaticBoxSizer(sb_expert, wx.VERTICAL)
        self.expert_enable_cb = wx.CheckBox(scroll, label="启用专家审稿 (质量更优，耗时较长)")
        self.expert_enable_cb.SetValue(config.get('expert_review.enabled', True))
        sbs_expert.Add(self.expert_enable_cb, 0, wx.ALL, 5)
        
        # 审稿轮次
        hbox_rounds = wx.BoxSizer(wx.HORIZONTAL)
        hbox_rounds.Add(wx.StaticText(scroll, label="最大审稿轮次:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.rounds_spin = wx.SpinCtrl(scroll, value=str(config.get('expert_review.max_rounds', 3)), 
                                        min=1, max=10, size=(60, -1))
        hbox_rounds.Add(self.rounds_spin, 0, wx.LEFT, 5)
        sbs_expert.Add(hbox_rounds, 0, wx.ALL, 5)
        
        # 及格分数
        hbox_score = wx.BoxSizer(wx.HORIZONTAL)
        hbox_score.Add(wx.StaticText(scroll, label="及格分数 (达到后停止审稿):"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.pass_score_spin = wx.SpinCtrl(scroll, value=str(config.get('expert_review.target_score', 80)),
                                            min=60, max=100, size=(60, -1))
        hbox_score.Add(self.pass_score_spin, 0, wx.LEFT, 5)
        sbs_expert.Add(hbox_score, 0, wx.ALL, 5)
        
        # 提示信息
        score_tip = wx.StaticText(scroll, label="提示：如果修改后分数反而下降，系统会自动回滚到之前的高分版本。")
        score_tip.SetForegroundColour(wx.Colour(100, 100, 100))
        sbs_expert.Add(score_tip, 0, wx.ALL, 5)
        
        sizer.Add(sbs_expert, 0, wx.EXPAND | wx.ALL, 10)

        # ==================== 2. 模型API设置 ====================
        sb_api = wx.StaticBox(scroll, label="2. 模型API设置")
        sbs_api = wx.StaticBoxSizer(sb_api, wx.VERTICAL)
        
        # Provider Selector + Test Button
        hbox_sel = wx.BoxSizer(wx.HORIZONTAL)
        hbox_sel.Add(wx.StaticText(scroll, label="选择预设:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.provider_choice = wx.Choice(scroll, choices=["siliconflow", "openai", "zhipuai", "deepseek", "tongyi"])
        self.provider_choice.Bind(wx.EVT_CHOICE, self.on_provider_changed)
        hbox_sel.Add(self.provider_choice, 1, wx.LEFT, 10)
        
        # API测试按钮
        self.test_api_btn = wx.Button(scroll, label="🔗 测试连接", size=(100, -1))
        self.test_api_btn.Bind(wx.EVT_BUTTON, self.on_test_api)
        hbox_sel.Add(self.test_api_btn, 0, wx.LEFT, 10)
        sbs_api.Add(hbox_sel, 0, wx.EXPAND | wx.ALL, 5)
        
        # Details Grid
        grid = wx.FlexGridSizer(3, 2, 10, 10)
        grid.AddGrowableCol(1, 1)
        
        grid.Add(wx.StaticText(scroll, label="Base URL:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.base_url_input = wx.TextCtrl(scroll)
        grid.Add(self.base_url_input, 1, wx.EXPAND)
        
        grid.Add(wx.StaticText(scroll, label="API Key:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.api_key_input = wx.TextCtrl(scroll, style=wx.TE_PASSWORD)
        grid.Add(self.api_key_input, 1, wx.EXPAND)
        
        grid.Add(wx.StaticText(scroll, label="Model Name:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.model_name_input = wx.TextCtrl(scroll)
        grid.Add(self.model_name_input, 1, wx.EXPAND)
        
        sbs_api.Add(grid, 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(sbs_api, 0, wx.EXPAND | wx.ALL, 10)
        
        # ==================== 3. 思考链配置 ====================
        sb_thinking = wx.StaticBox(scroll, label="3. 思考链配置 (Thinking Chain)")
        sbs_thinking = wx.StaticBoxSizer(sb_thinking, wx.VERTICAL)
        
        # 思考链开关
        self.thinking_enable_cb = wx.CheckBox(scroll, label="启用思考链 (深度推理，质量更高但速度更慢)")
        default_prov = config.get('model_routing.default_provider', 'siliconflow')
        thinking_enabled = config.get(f'model_routing.providers.{default_prov}.enable_thinking', False)
        self.thinking_enable_cb.SetValue(thinking_enabled)
        sbs_thinking.Add(self.thinking_enable_cb, 0, wx.ALL, 5)
        
        # 思考预算
        hbox_budget = wx.BoxSizer(wx.HORIZONTAL)
        hbox_budget.Add(wx.StaticText(scroll, label="思考预算 (tokens):"), 0, wx.ALIGN_CENTER_VERTICAL)
        thinking_budget = config.get(f'model_routing.providers.{default_prov}.thinking_budget', 4096)
        self.thinking_budget_spin = wx.SpinCtrl(scroll, value=str(thinking_budget), 
                                                 min=1000, max=16000, size=(80, -1))
        hbox_budget.Add(self.thinking_budget_spin, 0, wx.LEFT, 5)
        hbox_budget.Add(wx.StaticText(scroll, label="(建议: 2000-8000)"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        sbs_thinking.Add(hbox_budget, 0, wx.ALL, 5)
        
        # 思考链提示
        thinking_tip = wx.StaticText(scroll, label="💡 提示: 关闭=1-5秒/次 | 开启(4096)=20-60秒/次 | 仅DeepSeek/Qwen等模型支持")
        thinking_tip.SetForegroundColour(wx.Colour(80, 80, 80))
        sbs_thinking.Add(thinking_tip, 0, wx.ALL, 5)
        
        sizer.Add(sbs_thinking, 0, wx.EXPAND | wx.ALL, 10)
        
        # ==================== 4. 高级参数 (可折叠) ====================
        sb_advanced = wx.StaticBox(scroll, label="4. 高级参数")
        sbs_advanced = wx.StaticBoxSizer(sb_advanced, wx.VERTICAL)
        
        # Temperature
        hbox_temp = wx.BoxSizer(wx.HORIZONTAL)
        hbox_temp.Add(wx.StaticText(scroll, label="Temperature:"), 0, wx.ALIGN_CENTER_VERTICAL)
        temperature = config.get(f'model_routing.providers.{default_prov}.temperature', 0.7)
        self.temperature_spin = wx.SpinCtrlDouble(scroll, value=str(temperature), 
                                                   min=0.1, max=1.5, inc=0.1, size=(80, -1))
        hbox_temp.Add(self.temperature_spin, 0, wx.LEFT, 5)
        hbox_temp.Add(wx.StaticText(scroll, label="(创造性: 0.1=保守, 1.0=创意)"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        sbs_advanced.Add(hbox_temp, 0, wx.ALL, 5)
        
        # Top-P
        hbox_topp = wx.BoxSizer(wx.HORIZONTAL)
        hbox_topp.Add(wx.StaticText(scroll, label="Top-P:"), 0, wx.ALIGN_CENTER_VERTICAL)
        top_p = config.get(f'model_routing.providers.{default_prov}.top_p', 0.7)
        self.top_p_spin = wx.SpinCtrlDouble(scroll, value=str(top_p), 
                                             min=0.1, max=1.0, inc=0.1, size=(80, -1))
        hbox_topp.Add(self.top_p_spin, 0, wx.LEFT, 5)
        hbox_topp.Add(wx.StaticText(scroll, label="(多样性: 0.1-1.0)"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        sbs_advanced.Add(hbox_topp, 0, wx.ALL, 5)
        
        # Max Tokens
        hbox_maxtokens = wx.BoxSizer(wx.HORIZONTAL)
        hbox_maxtokens.Add(wx.StaticText(scroll, label="Max Tokens:"), 0, wx.ALIGN_CENTER_VERTICAL)
        max_tokens = config.get(f'model_routing.providers.{default_prov}.max_tokens', 100000)
        self.max_tokens_spin = wx.SpinCtrl(scroll, value=str(max_tokens), 
                                            min=1000, max=200000, size=(100, -1))
        hbox_maxtokens.Add(self.max_tokens_spin, 0, wx.LEFT, 5)
        hbox_maxtokens.Add(wx.StaticText(scroll, label="(最大输出长度)"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        sbs_advanced.Add(hbox_maxtokens, 0, wx.ALL, 5)
        
        # [*] 新增：最大引用数量
        hbox_maxcite = wx.BoxSizer(wx.HORIZONTAL)
        hbox_maxcite.Add(wx.StaticText(scroll, label="最大引用数:"), 0, wx.ALIGN_CENTER_VERTICAL)
        max_citations = config.get('citation.max_total', 25)
        self.max_citations_spin = wx.SpinCtrl(scroll, value=str(max_citations), 
                                               min=5, max=100, size=(70, -1))
        hbox_maxcite.Add(self.max_citations_spin, 0, wx.LEFT, 5)
        hbox_maxcite.Add(wx.StaticText(scroll, label="(论文中最多引用多少条文献，建议15-30)"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        sbs_advanced.Add(hbox_maxcite, 0, wx.ALL, 5)
        
        sizer.Add(sbs_advanced, 0, wx.EXPAND | wx.ALL, 10)
        
        # ==================== 初始化和保存 ====================
        # Initialize fields with default provider
        idx = self.provider_choice.FindString(default_prov)
        if idx != wx.NOT_FOUND:
            self.provider_choice.SetSelection(idx)
        self.load_provider_fields(default_prov)

        # Save Button
        save_btn = wx.Button(scroll, label="💾 保存并应用配置", size=(200, 40))
        save_btn.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        save_btn.Bind(wx.EVT_BUTTON, self.on_save_config)
        sizer.Add(save_btn, 0, wx.ALIGN_CENTER | wx.ALL, 20)
        
        scroll.SetSizer(sizer)
        
        # 将滚动面板添加到父容器
        parent_sizer = wx.BoxSizer(wx.VERTICAL)
        parent_sizer.Add(scroll, 1, wx.EXPAND)
        parent.SetSizer(parent_sizer)

    def create_search_tab(self, parent):
        sizer = wx.BoxSizer(wx.VERTICAL)

        sb = wx.StaticBox(parent, label="网络检索设置 (Page Assist)")
        sbs = wx.StaticBoxSizer(sb, wx.VERTICAL)

        self.search_enable_cb = wx.CheckBox(parent, label="启用网络检索")
        self.search_enable_cb.SetValue(config.get('literature.web_search.enabled', True))
        sbs.Add(self.search_enable_cb, 0, wx.ALL, 10)

        # Standard vs Deep
        self.search_mode_rb = wx.RadioBox(parent, label="搜索模式", 
                                           choices=["标准 (Standard)", "深度 (Deep - Headless Browser)"], 
                                           majorDimension=1)
        mode = config.get('literature.web_search.mode', 'deep')
        self.search_mode_rb.SetSelection(1 if mode == 'deep' else 0)
        sbs.Add(self.search_mode_rb, 0, wx.EXPAND | wx.ALL, 10)
        
        # Max Results
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(wx.StaticText(parent, label="最大结果数:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.search_limit_spin = wx.SpinCtrl(parent, 
                                              value=str(config.get('literature.web_search.results_per_query', 10)), 
                                              min=1, max=50)
        hbox.Add(self.search_limit_spin, 0, wx.LEFT, 10)
        sbs.Add(hbox, 0, wx.ALL, 10)
        
        # Info
        info = wx.StaticText(parent, label="注意：深度模式需要下载浏览器组件（首次运行会自动下载），效果类似 Page Assist 插件。\n标准模式速度快但只获取摘要。")
        info.SetForegroundColour(wx.Colour(100, 100, 100))
        sbs.Add(info, 0, wx.ALL, 10)

        sizer.Add(sbs, 0, wx.EXPAND | wx.ALL, 10)
        
        # Save Button
        save_btn = wx.Button(parent, label="仅保存搜索设置", size=(150, 30))
        save_btn.Bind(wx.EVT_BUTTON, self.on_save_search_config)
        sizer.Add(save_btn, 0, wx.ALIGN_CENTER | wx.ALL, 20)
        
        parent.SetSizer(sizer)

    def refresh_history_tree(self):
        """刷新历史记录树"""
        self.history_tree.DeleteAllItems()
        root = self.history_tree.AddRoot("历史记录")
        
        history = load_history()
        for title, records in history.items():
            title_node = self.history_tree.AppendItem(root, f"📄 {title}")
            for record in records:
                time_node = self.history_tree.AppendItem(title_node, f"  ⏰ {record['timestamp']}")
                for file_info in record.get('files', []):
                    if isinstance(file_info, dict):
                        file_path = file_info.get('path', '')
                        file_name = os.path.basename(file_path)
                    else:
                        file_path = file_info
                        file_name = os.path.basename(file_info)
                    file_node = self.history_tree.AppendItem(time_node, f"    📁 {file_name}")
                    self.history_tree.SetItemData(file_node, file_path)
        
        self.history_tree.ExpandAll()

    def on_refresh_history(self, event):
        self.refresh_history_tree()

    def on_history_item_activated(self, event):
        """双击历史项目"""
        item = event.GetItem()
        file_path = self.history_tree.GetItemData(item)
        if file_path and os.path.exists(file_path):
            try:
                os.startfile(file_path)
            except Exception as e:
                wx.MessageBox(f"无法打开文件: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
    
    def on_open_output_dir(self, event):
        """打开输出目录"""
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        if os.path.exists(output_dir):
            try:
                os.startfile(output_dir)
            except Exception as e:
                wx.MessageBox(f"无法打开目录: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
        else:
            wx.MessageBox("输出目录不存在", "提示", wx.OK | wx.ICON_WARNING)
    
    def on_delete_history(self, event):
        """删除选中的历史记录"""
        item = self.history_tree.GetSelection()
        if not item.IsOk():
            wx.MessageBox("请先选择要删除的记录", "提示", wx.OK | wx.ICON_WARNING)
            return
        
        # 获取项目文本用于确认
        item_text = self.history_tree.GetItemText(item)
        
        # 确认删除
        dlg = wx.MessageDialog(
            self, 
            f"确定要删除 '{item_text}' 吗？\n\n注意：这只会删除历史记录，不会删除实际文件。",
            "确认删除",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION
        )
        if dlg.ShowModal() != wx.ID_YES:
            dlg.Destroy()
            return
        dlg.Destroy()
        
        # 从历史记录中删除
        history = load_history()
        
        # 确定是删除整个项目还是单个记录
        parent = self.history_tree.GetItemParent(item)
        if parent == self.history_tree.GetRootItem():
            # 删除整个项目（一级节点）
            for title in list(history.keys()):
                if f"📄 {title}" == item_text:
                    del history[title]
                    break
        else:
            # 删除单个时间记录（二级节点）
            grandparent = self.history_tree.GetItemParent(parent)
            if grandparent == self.history_tree.GetRootItem():
                parent_text = self.history_tree.GetItemText(parent)
                for title in list(history.keys()):
                    if f"📄 {title}" == parent_text:
                        # 删除匹配时间戳的记录
                        history[title] = [r for r in history[title] if f"  ⏰ {r['timestamp']}" != item_text]
                        if not history[title]:
                            del history[title]
                        break
        
        save_history(history)
        self.refresh_history_tree()
        wx.MessageBox("记录已删除", "成功", wx.OK | wx.ICON_INFORMATION)
    
    def on_history_right_click(self, event):
        """历史记录右键菜单"""
        item = event.GetItem()
        if not item.IsOk():
            return
        
        self.history_tree.SelectItem(item)
        file_path = self.history_tree.GetItemData(item)
        
        # 创建右键菜单
        menu = wx.Menu()
        
        if file_path and os.path.exists(file_path):
            item_open = menu.Append(wx.ID_ANY, "📄 打开文件")
            self.Bind(wx.EVT_MENU, lambda e: os.startfile(file_path), item_open)
            
            item_copy = menu.Append(wx.ID_ANY, "📋 复制路径")
            self.Bind(wx.EVT_MENU, lambda e: self._copy_to_clipboard(file_path), item_copy)
            
            item_dir = menu.Append(wx.ID_ANY, "📂 打开所在目录")
            self.Bind(wx.EVT_MENU, lambda e: os.startfile(os.path.dirname(file_path)), item_dir)
            
            menu.AppendSeparator()
        
        item_delete = menu.Append(wx.ID_ANY, "🗑 删除记录")
        self.Bind(wx.EVT_MENU, self.on_delete_history, item_delete)
        
        self.PopupMenu(menu)
        menu.Destroy()
    
    def _copy_to_clipboard(self, text):
        """复制文本到剪贴板"""
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(text))
            wx.TheClipboard.Close()
            wx.MessageBox("路径已复制到剪贴板", "提示", wx.OK | wx.ICON_INFORMATION)

    def load_provider_fields(self, provider_name):
        """加载提供商配置到UI控件"""
        p_conf = config.get(f'model_routing.providers.{provider_name}', {})
        self.base_url_input.SetValue(p_conf.get('base_url', ''))
        self.api_key_input.SetValue(p_conf.get('api_key', ''))
        models = p_conf.get('models', [])
        self.model_name_input.SetValue(models[0] if models else '')
        
        # 加载思考链配置
        self.thinking_enable_cb.SetValue(p_conf.get('enable_thinking', False))
        self.thinking_budget_spin.SetValue(p_conf.get('thinking_budget', 4096))
        
        # 加载高级参数
        self.temperature_spin.SetValue(p_conf.get('temperature', 0.7))
        self.top_p_spin.SetValue(p_conf.get('top_p', 0.7))
        self.max_tokens_spin.SetValue(p_conf.get('max_tokens', 100000))

    def on_provider_changed(self, event):
        provider = self.provider_choice.GetStringSelection()
        self.load_provider_fields(provider)
    
    def on_mode_changed(self, event):
        """快捷模式切换事件处理"""
        provider = self.provider_choice.GetStringSelection()
        
        # 定义模式预设
        mode_presets = {
            'fast': {
                'enable_thinking': False,
                'thinking_budget': 1000,
                'temperature': 0.7,
                'tip': '💡 快速：关闭思考链，1-5秒/次响应'
            },
            'balanced': {
                'enable_thinking': False,
                'thinking_budget': 4096,
                'temperature': 0.7,
                'tip': '💡 均衡：速度与质量的最佳平衡'
            },
            'quality': {
                'enable_thinking': True,
                'thinking_budget': 8000,
                'temperature': 0.5,
                'tip': '💡 质量：开启思考链深度推理，20-60秒/次'
            }
        }
        
        # 确定当前选择的模式
        if self.mode_fast.GetValue():
            preset = mode_presets['fast']
        elif self.mode_quality.GetValue():
            preset = mode_presets['quality']
        else:
            preset = mode_presets['balanced']
        
        # 更新UI控件
        self.thinking_enable_cb.SetValue(preset['enable_thinking'])
        self.thinking_budget_spin.SetValue(preset['thinking_budget'])
        self.temperature_spin.SetValue(preset['temperature'])
        self.mode_tip_label.SetLabel(preset['tip'])
        
        # 保存到配置
        config.set(f'model_routing.providers.{provider}.enable_thinking', preset['enable_thinking'])
        config.set(f'model_routing.providers.{provider}.thinking_budget', preset['thinking_budget'])
        config.set(f'model_routing.providers.{provider}.temperature', preset['temperature'])
        config.save()

    def on_save_config(self, event):
        provider = self.provider_choice.GetStringSelection()
        
        # Save Provider Config
        base_url = self.base_url_input.GetValue().strip()
        api_key = self.api_key_input.GetValue().strip()
        model = self.model_name_input.GetValue().strip()
        
        config.set('model_routing.default_provider', provider)
        config.set(f'model_routing.providers.{provider}.base_url', base_url)
        config.set(f'model_routing.providers.{provider}.api_key', api_key)
        config.set(f'model_routing.providers.{provider}.models', [model])
        config.set(f'model_routing.providers.{provider}.enabled', True)
        
        # Save Thinking Chain Config
        config.set(f'model_routing.providers.{provider}.enable_thinking', self.thinking_enable_cb.GetValue())
        config.set(f'model_routing.providers.{provider}.thinking_budget', self.thinking_budget_spin.GetValue())
        
        # Save Advanced Parameters
        config.set(f'model_routing.providers.{provider}.temperature', self.temperature_spin.GetValue())
        config.set(f'model_routing.providers.{provider}.top_p', self.top_p_spin.GetValue())
        config.set(f'model_routing.providers.{provider}.max_tokens', self.max_tokens_spin.GetValue())
        
        # Save Expert Config
        config.set('expert_review.enabled', self.expert_enable_cb.GetValue())
        config.set('expert_review.max_rounds', self.rounds_spin.GetValue())
        config.set('expert_review.target_score', self.pass_score_spin.GetValue())
        
        # [*] 保存引用配置
        config.set('citation.max_total', self.max_citations_spin.GetValue())
        
        config.save()
        wx.MessageBox("所有配置已保存！", "成功", wx.OK | wx.ICON_INFORMATION)
    
    def on_test_api(self, event):
        """测试API连接"""
        import requests
        import time
        
        base_url = self.base_url_input.GetValue().strip()
        api_key = self.api_key_input.GetValue().strip()
        model = self.model_name_input.GetValue().strip()
        
        if not base_url or not api_key or not model:
            wx.MessageBox("请先填写 Base URL、API Key 和 Model Name", "提示", wx.OK | wx.ICON_WARNING)
            return
        
        # 构建端点URL
        if not base_url.endswith('/chat/completions'):
            if base_url.endswith('/v1') or base_url.endswith('/v4'):
                endpoint = f"{base_url}/chat/completions"
            else:
                endpoint = f"{base_url}/v1/chat/completions"
        else:
            endpoint = base_url
        
        self.test_api_btn.SetLabel("测试中...")
        self.test_api_btn.Disable()
        wx.Yield()  # 刷新UI
        
        try:
            start_time = time.time()
            response = requests.post(
                endpoint,
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': model,
                    'messages': [{'role': 'user', 'content': 'Hi, respond with OK'}],
                    'max_tokens': 10
                },
                timeout=30
            )
            elapsed = time.time() - start_time
            
            if response.ok:
                data = response.json()
                content = data.get('choices', [{}])[0].get('message', {}).get('content', 'OK')
                wx.MessageBox(
                    f"✅ 连接成功！\n\n"
                    f"响应时间: {elapsed:.2f}秒\n"
                    f"模型响应: {content[:50]}\n"
                    f"端点: {endpoint}",
                    "API测试成功", wx.OK | wx.ICON_INFORMATION
                )
            else:
                error_msg = response.text[:300] if response.text else f"HTTP {response.status_code}"
                wx.MessageBox(
                    f"❌ 连接失败！\n\n"
                    f"状态码: {response.status_code}\n"
                    f"错误信息: {error_msg}",
                    "API测试失败", wx.OK | wx.ICON_ERROR
                )
                
        except requests.exceptions.Timeout:
            wx.MessageBox("❌ 连接超时！请检查网络或API地址。", "API测试失败", wx.OK | wx.ICON_ERROR)
        except requests.exceptions.ConnectionError as e:
            wx.MessageBox(f"❌ 无法连接！\n\n{str(e)[:200]}", "API测试失败", wx.OK | wx.ICON_ERROR)
        except Exception as e:
            wx.MessageBox(f"❌ 测试出错！\n\n{str(e)[:200]}", "API测试失败", wx.OK | wx.ICON_ERROR)
        finally:
            self.test_api_btn.SetLabel("🔗 测试连接")
            self.test_api_btn.Enable()

    def on_save_search_config(self, event):
        enabled = self.search_enable_cb.GetValue()
        mode_idx = self.search_mode_rb.GetSelection()
        mode = 'deep' if mode_idx == 1 else 'standard'
        limit = self.search_limit_spin.GetValue()
        
        config.set('literature.web_search.enabled', enabled)
        config.set('literature.web_search.mode', mode)
        config.set('literature.web_search.results_per_query', limit)
        
        config.save()
        wx.MessageBox("搜索配置已保存！", "成功", wx.OK | wx.ICON_INFORMATION)

    def on_select_lit(self, event):
        wildcard = "Text files (*.txt)|*.txt|All files (*.*)|*.*"
        dlg = wx.FileDialog(self, "选择文献池文件", wildcard=wildcard, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            self.lit_path_ctrl.SetValue(dlg.GetPath())
        dlg.Destroy()

    def on_start(self, event):
        title = self.title_input.GetValue().strip()
        if not title:
            wx.MessageBox("请输入论文题目", "提示", wx.OK | wx.ICON_WARNING)
            return

        self.start_btn.Disable()
        self.log_ctrl.Clear()
        self.log_ctrl.AppendText("🚀 正在生成大纲，请稍候...\n")
        
        # 初始化进度统计
        import time
        self.generation_start_time = time.time()
        self.generation_api_calls = 0
        self.generation_word_count = 0
        
        # 重置进度UI
        self.progress_bar.SetValue(0)
        self.progress_percent_label.SetLabel("0%")
        self.progress_stage_label.SetLabel("当前阶段: 生成大纲")
        self.stats_words_label.SetLabel("已生成: 0 字")
        self.stats_api_label.SetLabel("API调用: 0 次")
        self.stats_time_label.SetLabel("耗时: 0 秒")
        
        # 保存输入数据，供后续使用
        self.pending_title = title
        self.pending_idea = self.idea_input.GetValue().strip()
        self.pending_lit_path = self.lit_path_ctrl.GetValue().strip()
        
        # 启动大纲生成线程
        outline_worker = OutlineWorkerThread(
            self, 
            self.pending_title, 
            self.pending_idea, 
            self.pending_lit_path
        )
        outline_worker.start()
    
    def on_outline_ready(self, event):
        """大纲生成完成后的处理"""
        self.log_ctrl.AppendText("🎯 收到大纲事件，准备显示编辑对话框...\n")
        
        if not event.success:
            self.start_btn.Enable()
            error = getattr(event, 'error', '未知错误')
            self.log_ctrl.AppendText(f"❌ 大纲生成失败: {error}\n")
            wx.MessageBox(f"大纲生成失败: {error}", "错误", wx.OK | wx.ICON_ERROR)
            return
        
        outline_data = event.outline
        
        # 弹出大纲编辑对话框
        dlg = OutlineEditorDialog(self, outline_data)
        result = dlg.ShowModal()
        
        if result == wx.ID_OK:
            edited_outline = dlg.result
            dlg.Destroy()
            
            self.log_ctrl.AppendText("✅ 大纲已确认，开始生成论文...\n")
            
            # Check Search Mode warning
            if config.get('literature.web_search.enabled') and config.get('literature.web_search.mode') == 'deep':
                self.log_ctrl.AppendText("🔍 已启用深度搜索，首次运行可能需要下载浏览器...\n")

            # 启动论文生成线程
            worker = WorkerThread(
                self, 
                self.pending_title, 
                self.pending_idea, 
                self.pending_lit_path, 
                edited_outline
            )
            worker.start()
        else:
            dlg.Destroy()
            self.start_btn.Enable()
            self.log_ctrl.AppendText("❌ 已取消生成\n")

    def on_progress_update(self, event):
        """进度更新事件处理器"""
        # 更新进度条
        progress = getattr(event, 'progress', 0)
        self.progress_bar.SetValue(min(100, max(0, int(progress))))
        self.progress_percent_label.SetLabel(f"{int(progress)}%")
        
        # 更新阶段标签
        stage = getattr(event, 'stage', '')
        if stage:
            self.progress_stage_label.SetLabel(f"当前阶段: {stage}")
        
        # 更新统计信息
        word_count = getattr(event, 'word_count', None)
        if word_count is not None:
            self.generation_word_count = word_count
            self.stats_words_label.SetLabel(f"已生成: {word_count:,} 字")
        
        api_calls = getattr(event, 'api_calls', None)
        if api_calls is not None:
            self.generation_api_calls = api_calls
            self.stats_api_label.SetLabel(f"API调用: {api_calls} 次")
        
        # 更新耗时
        if self.generation_start_time:
            import time
            elapsed = int(time.time() - self.generation_start_time)
            minutes, seconds = divmod(elapsed, 60)
            if minutes > 0:
                self.stats_time_label.SetLabel(f"耗时: {minutes}分{seconds}秒")
            else:
                self.stats_time_label.SetLabel(f"耗时: {seconds} 秒")

    def on_log_update(self, event):
        self.log_ctrl.AppendText(event.message)
        self.log_ctrl.ShowPosition(self.log_ctrl.GetLastPosition())

    def on_task_done(self, event):
        self.start_btn.Enable()
        result = event.result
        if result['success']:
            data = result.get('data', {})
            if isinstance(data, dict):
                # 收集所有生成的文件
                files = []
                for key, path in data.items():
                    if isinstance(path, str) and os.path.exists(path):
                        files.append({'name': key.upper(), 'path': path})

                if files:
                    # 添加到历史记录
                    title = self.title_input.GetValue().strip()
                    add_to_history(title, files)
                    self.refresh_history_tree()
                    
                    # 显示成功消息
                    file_list = "\n".join([f"- {f['name']}: {os.path.basename(f['path'])}" for f in files])
                    wx.MessageBox(f"论文生成完成！\n\n生成的文件：\n{file_list}\n\n可在历史记录中查看和打开文件。", 
                                  "成功", wx.OK | wx.ICON_INFORMATION)
                else:
                    wx.MessageBox("论文生成完成！\n但未找到生成的文件。", "警告", wx.OK | wx.ICON_WARNING)
            else:
                wx.MessageBox("论文生成完成！\n请查看输出目录。", "成功", wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox(f"任务失败: {result['error']}", "错误", wx.OK | wx.ICON_ERROR)


if __name__ == "__main__":
    app = wx.App()
    frame = MainFrame()
    app.MainLoop()
