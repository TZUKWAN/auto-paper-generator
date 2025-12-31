"""模板引擎 - 解析模板并生成论文"""
import logging
import re
import yaml
import os
import asyncio
from core.model_router import ModelRouter
from core.citation_manager import CitationManager
from core.web_search import WebSearchIntegration

logger = logging.getLogger(__name__)

class TemplateEngine:
    """论文模板引擎"""
    
    def __init__(self, template_path, model_router, citation_manager, project_context, config=None):
        """
        初始化模板引擎
        
        Args:
            template_path: 模板YAML文件路径
            model_router: 大模型路由器
            citation_manager: 引用管理器
            project_context: 项目上下文（题目、关键词、大纲等）
            config: 配置对象（用于网络检索）
        """
        self.template_path = template_path
        self.router = model_router
        self.citation_mgr = citation_manager
        self.project_context = project_context
        
        # 网络检索集成
        self.web_search = WebSearchIntegration(config) if config else None
        
        # 加载模板
        self.template = self._load_template()
        logger.info(f"模板引擎初始化: {self.template['template_name']}")
    
    def _load_template(self):
        """加载YAML模板"""
        import sys
        
        path_to_load = self.template_path
        
        # Check if file exists at original path
        if not os.path.exists(path_to_load) and getattr(sys, 'frozen', False):
             # Try _internal path
             if hasattr(sys, '_MEIPASS'):
                 internal_path = os.path.join(sys._MEIPASS, path_to_load)
                 if os.path.exists(internal_path):
                     path_to_load = internal_path
        
        with open(path_to_load, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _format_context_string(self):
        """将项目上下文（可能是字典）格式化为字符串"""
        if isinstance(self.project_context, dict):
            return f"""
项目题目：{self.project_context.get('title', '')}
核心思路/关键词：{self.project_context.get('extra_idea', '') or self.project_context.get('keywords', '')}

请基于以上信息生成学术论文内容。
"""
        return str(self.project_context)

    def generate_paper(self, progress_callback=None):
        """
        生成论文
        
        按照用户需求，每个部分生成单独的MD文档：
        - 00_摘要关键词.md
        - 01_引言.md
        - 02_二级标题1.md ~ 10_二级标题9.md (共9个，3个主体章节x3个二级标题)
        - 11_结论.md
        - 12_参考文献.md
        
        Args:
            progress_callback: 进度回调函数，签名: (progress, stage, word_count, api_calls)
        
        Returns:
            论文内容字符串
        """
        logger.info("开始生成论文...")
        
        # 辅助函数：发送进度
        def report_progress(pct, stage, word_count=None):
            if progress_callback:
                try:
                    progress_callback(pct, stage, word_count, None)
                except Exception:
                    pass
        
        # 获取保存目录
        sections_folder = self.project_context.get('sections_folder', None)
        if not sections_folder:
            sections_folder = os.path.join(
                self.project_context.get('output_folder', 'data/temp'), 
                'sections', 'v1'
            )
        os.makedirs(sections_folder, exist_ok=True)
        logger.info(f"章节保存目录: {sections_folder}")
        
        # 获取用户确认的大纲数据
        outline_data = self.project_context.get('outline_data', None)
        if not outline_data:
            logger.warning("未找到用户大纲数据，使用默认结构")
            outline_data = {
                'introduction': {'title': '一、引言', 'idea': ''},
                'chapters': [
                    {'title': '二、研究维度1', 'subsections': [{'title': '子维度1', 'idea': ''} for _ in range(3)]},
                    {'title': '三、研究维度2', 'subsections': [{'title': '子维度2', 'idea': ''} for _ in range(3)]},
                    {'title': '四、研究维度3', 'subsections': [{'title': '子维度3', 'idea': ''} for _ in range(3)]}
                ],
                'conclusion': {'title': '结论', 'idea': ''}
            }
        
        sections_content = []
        body_sections = []
        saved_md_files = []
        file_index = 1  # 0留给摘要
        
        # ===== 1. 生成引言 =====
        intro = outline_data.get('introduction', {})
        intro_title = intro.get('title', '一、引言')
        intro_idea = intro.get('idea', '')
        
        logger.info(f"生成引言: {intro_title}")
        report_progress(30, f"生成引言: {intro_title[:20]}")
        # [*] 设置当前章节为引言
        self.citation_mgr.set_current_section('introduction')
        intro_text = self._generate_introduction(intro_title, intro_idea)
        
        # 保存引言MD
        intro_path = os.path.join(sections_folder, f"{file_index:02d}_引言.md")
        with open(intro_path, 'w', encoding='utf-8') as f:
            f.write(intro_text)
        saved_md_files.append({'index': file_index, 'type': 'introduction', 'title': intro_title, 'path': intro_path})
        file_index += 1
        
        sections_content.append(intro_text)
        body_sections.append(intro_text)
        
        # ===== 2. 生成三个主体章节，每个3个二级标题 =====
        chapters = outline_data.get('chapters', [])
        for ch_idx, chapter in enumerate(chapters):
            chapter_title = chapter.get('title', f'{["二", "三", "四"][ch_idx]}、研究维度{ch_idx+1}')
            subsections = chapter.get('subsections', [])
            
            logger.info(f"生成主体章节 {ch_idx+1}: {chapter_title}")
            
            chapter_header = f"## {chapter_title}"
            chapter_parts = [chapter_header]
            
            for sub_idx, sub in enumerate(subsections[:3]):  # 限制为3个二级标题
                sub_title = sub.get('title', f'子维度{sub_idx+1}')
                sub_idea = sub.get('idea', '')
                
                chinese_nums = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
                sub_num = chinese_nums[sub_idx] if sub_idx < len(chinese_nums) else str(sub_idx + 1)
                sub_header = f"### （{sub_num}）{sub_title}"
                
                logger.info(f"  生成二级标题 {sub_idx+1}: {sub_title}")
                
                # 计算当前进度: 引言(30%) + 章节(30%-60%) = 30% + (ch_idx*3 + sub_idx + 1) / 9 * 30%
                section_progress = 30 + int((ch_idx * 3 + sub_idx + 1) / 9 * 30)
                report_progress(section_progress, f"章节{ch_idx+1}-{sub_idx+1}: {sub_title[:15]}")
                
                # 生成二级标题内容（带异常保护）
                try:
                    # [*] 设置当前章节和二级标题位置
                    self.citation_mgr.set_current_section('chapter', ch_idx, sub_idx)
                    sub_text = self._generate_subsection(chapter_title, sub_title, sub_idea, sub_idx)
                    
                    # 验证内容非空
                    if not sub_text or len(sub_text.strip()) < 50:
                        logger.error(f"二级标题 '{sub_title}' 生成内容过短或为空，使用回退内容")
                        sub_text = f'本节围绕"{sub_title}"展开论述。{sub_idea if sub_idea else ""}'
                except Exception as e:
                    logger.error(f"生成二级标题 '{sub_title}' 时发生异常: {e}")
                    sub_text = f'[内容生成异常: {str(e)[:100]}] 本节主题：{sub_title}'
                
                # 保存每个二级标题为单独的MD文件
                safe_title = re.sub(r'[<>:"/\\|?*]', '', sub_title).strip()[:30]
                md_filename = f"{file_index:02d}_{safe_title}.md"
                md_path = os.path.join(sections_folder, md_filename)
                
                subsection_content = f"{sub_header}\n\n{sub_text}"
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(subsection_content)
                
                saved_md_files.append({
                    'index': file_index,
                    'type': 'subsection',
                    'title': sub_title,
                    'parent_title': chapter_title,
                    'header': sub_header,
                    'path': md_path
                })
                logger.info(f"    保存: {md_filename}")
                file_index += 1
                
                chapter_parts.append(sub_header)
                chapter_parts.append(sub_text)
            
            chapter_text = "\n\n".join(chapter_parts)
            sections_content.append(chapter_text)
            body_sections.append(chapter_text)
        
        # ===== 3. 生成结论 =====
        conclusion = outline_data.get('conclusion', {})
        concl_title = conclusion.get('title', '结论')
        concl_idea = conclusion.get('idea', '')
        
        logger.info(f"生成结论: {concl_title}")
        report_progress(62, f"生成结论: {concl_title[:15]}")
        # [*] 设置当前章节为结论（配额为0，不添加新引用）
        self.citation_mgr.set_current_section('conclusion')
        concl_text = self._generate_conclusion(concl_title, concl_idea)
        
        # 保存结论MD
        concl_path = os.path.join(sections_folder, f"{file_index:02d}_结论.md")
        with open(concl_path, 'w', encoding='utf-8') as f:
            f.write(concl_text)
        saved_md_files.append({'index': file_index, 'type': 'conclusion', 'title': concl_title, 'path': concl_path})
        file_index += 1
        
        sections_content.append(concl_text)
        body_sections.append(concl_text)
        
        # ===== 4. 同步引用并生成参考文献 =====
        # [*] 新增：在生成参考文献前，同步正文中的引用与citation_tracker
        full_body_text = "\n\n".join(body_sections)
        sync_report = self.citation_mgr.sync_with_text(full_body_text)
        logger.info(f"引用同步报告: 正文引用{len(sync_report['text_citations'])}个, "
                   f"匹配{len(sync_report['matched'])}个, 缺失{len(sync_report.get('missing', []))}个")
        
        references = self.citation_mgr.generate_reference_list()
        # [*] 确保参考文献始终保存，即使为空也创建占位
        ref_text = f"## 参考文献\n\n{references}" if references else "## 参考文献\n\n（暂无参考文献）"
        sections_content.append(ref_text)
        
        ref_path = os.path.join(sections_folder, f"{file_index:02d}_参考文献.md")
        with open(ref_path, 'w', encoding='utf-8') as f:
            f.write(ref_text)
        saved_md_files.append({'index': file_index, 'type': 'references', 'title': '参考文献', 'path': ref_path})
        logger.info(f"保存参考文献: {ref_path} ({len(references) if references else 0}字)")
        
        # ===== 5. 生成摘要 (基于全文) =====
        full_body_text = "\n\n".join(body_sections)
        logger.info("生成最终摘要（基于全文，无引用）...")
        report_progress(65, "生成摘要")
        abstract_text = self._generate_final_abstract(None, full_body_text)
        sections_content.insert(0, abstract_text)
        
        # 保存摘要MD（编号为00）
        abstract_path = os.path.join(sections_folder, "00_摘要关键词.md")
        with open(abstract_path, 'w', encoding='utf-8') as f:
            f.write(abstract_text)
        saved_md_files.insert(0, {'index': 0, 'type': 'abstract', 'title': '摘要关键词', 'path': abstract_path})
        logger.info("保存摘要: 00_摘要关键词.md")
        
        # 保存文件索引
        import json
        index_path = os.path.join(sections_folder, "_index.json")
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(saved_md_files, f, ensure_ascii=False, indent=2)
        
        # 组合完整论文
        paper = "\n\n".join(sections_content)
        
        logger.info(f"论文生成完成，共保存 {len(saved_md_files)} 个MD文件")
        return paper
    
    def _generate_introduction(self, title, idea):
        """生成引言 - 增强版"""
        prompt = f"""请为论文撰写引言部分。

论文题目：{self.project_context.get('title', '')}
引言标题：{title}
写作思路：{idea if idea else '未指定'}

写作要求：
1. 引言为纯段落形式，禁止使用任何小标题
2. 包含研究背景、研究意义、研究问题、研究方法等内容
3. 逻辑递进，层层深入
4. 字数：800-1200字
5. 学术化表达，语言平实
6. 禁止使用"首先""其次""再次""最后""此外""另外"等机械过渡词，改用更自然的逻辑连接

【重要】请直接输出引言正文，不要有任何开场白或额外说明。
"""
        result = self.router.generate(prompt, context="你是学术论文写作专家", max_tokens=8000)
        
        # 验证结果
        cleaned_result = self._clean_ai_artifacts(result)
        if not cleaned_result or len(cleaned_result.strip()) < 100:
            logger.warning(f"引言生成结果过短或为空(raw_len={len(result) if result else 0}, cleaned_len={len(cleaned_result) if cleaned_result else 0})，尝试重试...")
            if result:
                logger.debug(f"Raw Result Preview: {result[:200]}...")
            retry_prompt = prompt + "\n\n【警告】上次生成的内容为空，请务必输出详细的引言内容！"
            result = self.router.generate(retry_prompt, context="你是学术论文写作专家", max_tokens=8000)
            cleaned_result = self._clean_ai_artifacts(result)
            
        return f"## {title}\n\n{cleaned_result}"
    
    def _generate_subsection(self, chapter_title, sub_title, idea, sub_idx):
        """生成二级标题内容（带引用）"""
        prompt = f"""请撰写二级标题内容。

所属一级标题：{chapter_title}
二级标题：{sub_title}
核心思路：{idea if idea else '未指定'}

写作要求：
- 这是本章的第 {sub_idx+1} 个小节
- 必须紧扣二级标题展开论述
- 逻辑要层层递进
- 字数要求：600-800字
- 禁止使用小标题，直接写成段落形式
- 学术化表达，语言平实
- 禁止使用"首先""其次""再次""最后""此外""另外"等机械过渡词

【重要】请直接输出正文内容，不要有任何开场白或额外说明。
"""
        # 调用带引用的生成逻辑
        para_config = {
            'prompt': prompt,
            'target_sentences': 8,
            'sub_title': sub_title
        }
        result = self._generate_paragraph(para_config, f"本节核心内容：{idea}")
        return result
    
    def _generate_conclusion(self, title, idea):
        """生成结论 - 增强版"""
        prompt = f"""请为论文撰写结论部分。

论文题目：{self.project_context.get('title', '')}
结论标题：{title}
写作思路：{idea if idea else '未指定'}

写作要求：
1. 结论为纯段落形式，禁止使用任何小标题
2. 总结研究发现、研究贡献、研究局限、未来展望
3. 逻辑清晰，总结有力
4. 字数：500-800字
5. 学术化表达
6. 禁止使用"首先""其次""再次""最后""此外""另外"等机械过渡词

【重要】请直接输出结论正文，不要有任何开场白或额外说明。
"""
        result = self.router.generate(prompt, context="你是学术论文写作专家", max_tokens=8000)
        
        # 验证结果
        cleaned_result = self._clean_ai_artifacts(result)
        if not cleaned_result or len(cleaned_result.strip()) < 100:
            logger.warning("结论生成结果过短或为空，尝试重试...")
            retry_prompt = prompt + "\n\n【警告】上次生成的内容为空，请务必输出详细的结论内容！"
            result = self.router.generate(retry_prompt, context="你是学术论文写作专家", max_tokens=8000)
            cleaned_result = self._clean_ai_artifacts(result)
            
        return f"## {title}\n\n{cleaned_result}"

    def _generate_final_abstract(self, section_config, full_body):
        """生成最终摘要（基于全文，严禁引用）"""
        prompt = f"""
请基于以下论文正文，撰写一份高质量的学术摘要。

论文正文：
{full_body[:8000]}... (略)

写作要求：
1. **内容全面**：概括研究背景、目的、方法、主要观点和结论。
2. **语言精炼**：学术化表达，高度概括。
3. **关键词**：文末附3-5个关键词。
4. **绝对禁止引用**：摘要中严禁出现任何文献引用编号（如[1][2]），必须是纯文本。
5. **格式要求**：标题为“摘要”，正文为一段。

【重要】请直接输出摘要内容和关键词，不要有任何开场白、解释或额外回应。
"""
        result = self.router.generate(prompt, context="你是专业的学术编辑，负责撰写摘要", max_tokens=4000)
        # [*] 后处理：强制清理所有引用格式
        result = re.sub(r'\[citation:\d+\]', '', result)
        result = re.sub(r'\[\d+\]', '', result)
        result = re.sub(r'（注[：:].*?）', '', result)
        return result
    
    def _expand_dynamic_sections(self, sections):
        """
        展开动态章节
        
        处理模板中标记为 dynamic=true 的章节
        """
        expanded = []
        
        i = 0
        while i < len(sections):
            section = sections[i]
            
            if section.get('dynamic', False):
                # 这是一个动态章节，需要AI设计框架
                logger.info(f"处理动态章节: {section['title']}")
                
                # 获取框架
                framework = self._get_dynamic_framework(section)
                
                # 找到模板章节
                template_section = sections[i + 1]
                if not template_section.get('is_template', False):
                    logger.error("动态章节后缺少模板章节")
                    expanded.append(section)
                    i += 1
                    continue
                
                # 为每个框架项生成详细内容
                for idx, item in enumerate(framework):
                    # item结构: {'title': '...', 'summary': '...', 'subsections': [...]}
                    expanded_section = template_section.copy()
                    
                    # 设置一级标题
                    l1_title = item['title']
                    # [*] 使用真正的章节标题，不要拼接模板标题
                    expanded_section['title'] = l1_title
                    expanded_section['framework_summary'] = item['summary']
                    
                    # [*] 关键修改：将二级标题转换为"段落"配置，实现分块生成
                    if item['subsections']:
                        paragraphs = []
                        chinese_nums = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
                        for sub_idx, sub_title in enumerate(item['subsections']):
                            sub_num = chinese_nums[sub_idx] if sub_idx < len(chinese_nums) else str(sub_idx + 1)
                            paragraphs.append({
                                'prompt': f"""
请撰写二级标题内容：{sub_title}

所属一级标题：{l1_title}
核心论点：{item['summary']}

写作要求：
- 这是本章的第 {sub_idx+1} 个小节
- 必须紧扣二级标题 "{sub_title}" 展开
- 逻辑要承接上一节，层层递进
- 字数要求：600-800字
- 禁止使用小标题，直接写成段落形式
- 禁止输出"句子N:"、"查询N:"等格式
- 直接输出正文内容，不要任何前言或说明
""",
                                'id': f"{expanded_section.get('id', 'section')}_sub_{idx}_{sub_idx}",
                                'target_sentences': 8,
                                'sub_title': sub_title,  # [*] 保存二级标题
                                'sub_num': sub_num       # [*] 保存序号
                            })
                        expanded_section['paragraphs'] = paragraphs
                        logger.info(f"  已为 '{l1_title}' 生成 {len(paragraphs)} 个二级标题任务")
                    else:
                        #以此类推
                        pass

                    expanded.append(expanded_section)
                
                i += 2  # 跳过模板章节
            else:
                expanded.append(section)
                i += 1
        
        return expanded

    def _get_dynamic_framework(self, section):
        """
        获取动态章节框架
        
        Args:
            section: 章节配置
            
        Returns:
            框架列表 [(标题, 概要), ...]
        """
        prompt = section['prompt']
        node_id = section.get('id')
        
        # 调用AI生成框架
        response = self.router.generate(
            prompt,
            self._format_context_string(),
            node_id=node_id
        )
        
        # 解析响应（假设格式：维度1: xxx\n概要: xxx\n\n维度2: ...）
        framework = self._parse_framework_response(response, section.get('expand_count', 4))
        
        logger.info(f"框架生成完成: {len(framework)} 个子章节")
        return framework

    def _parse_framework_response(self, response, count):
        """解析框架响应（增强版：提取二级标题）"""
        frameworks = []
        
        # 预清洗：统一冒号
        clean_response = response.replace('：', ':')
        
        # 按 "主体N标题" 或 "维度N标题" 分割
        # 匹配模式: (主体\d+标题|维度\d+标题):
        parts = re.split(r'(?:主体|维度|论点)\d+标题:', clean_response)
        
        for part in parts[1:count+1]:
            lines = [l.strip() for l in part.strip().split('\n') if l.strip()]
            if not lines:
                continue
                
            l1_title = lines[0] # 第一行是一级标题内容
            
            # 提取核心内容和二级标题
            summary = ""
            subsections = []
            
            current_tag = None
            
            # 逐行解析
            # 格式预期:
            # [标题内容]
            # 核心内容: xxx
            # 二级标题1: xxx
            # 二级标题2: xxx
            
            summary_lines = []
            
            for line in lines[1:]:
                if line.startswith('核心内容:'):
                    summary_lines.append(line.replace('核心内容:', '').strip())
                elif re.match(r'二级标题\d+:', line):
                    sub_title = re.sub(r'二级标题\d+:', '', line).strip()
                    # [*] 清理AI可能生成的序号前缀（一）、（二）等
                    sub_title = re.sub(r'^[（\(][一二三四五六七八九十\d]+[）\)]\s*', '', sub_title).strip()
                    sub_title = re.sub(r'^[一二三四五六七八九十]+[\s、\.．。:：]\s*', '', sub_title).strip()
                    if sub_title:
                        subsections.append(sub_title)
                else:
                    # 可能是summary的延续
                    if not subsections: # 如果还没开始解析二级标题，就算作summary
                        summary_lines.append(line)
            
            frameworks.append({
                'title': l1_title,
                'summary': " ".join(summary_lines),
                'subsections': subsections[:3] # 限制为前3个
            })
            
        # 补充默认
        while len(frameworks) < count:
            frameworks.append({
                'title': f"研究维度{len(frameworks)+1}",
                'summary': "暂无",
                'subsections': [f"子维度{i}" for i in range(1,4)]
            })
        
        return frameworks[:count]
    
    def _generate_section(self, section):
        """
        生成单个章节
        
        Args:
            section: 章节配置
            
        Returns:
        """
        title = section['title']
        content_parts = [f"## {title}"]
        
        # 如果有框架概要，加入上下文
        framework_context = ""
        if 'framework_summary' in section:
            framework_context = f"\n本节核心内容：{section['framework_summary']}\n"
        
        # 如果有段落配置
        if 'paragraphs' in section:
            for para_config in section['paragraphs']:
                para_text = self._generate_paragraph(para_config, framework_context)
                
                # [*] 如果有二级标题，添加 ### 格式
                if 'sub_title' in para_config and 'sub_num' in para_config:
                    sub_header = f"### （{para_config['sub_num']}）{para_config['sub_title']}"
                    content_parts.append(sub_header)
                
                content_parts.append(para_text)
        else:
            # 直接生成整个章节
            para_text = self._generate_paragraph(section, framework_context)
            content_parts.append(para_text)
        
        return "\n\n".join(content_parts)
    
    def _generate_paragraph(self, para_config, additional_context=""):
        """
        生成段落（三阶段流程：骨架→引用→润色）

        Args:
            para_config: 段落配置
            additional_context: 额外上下文

        Returns:
            段落文本
        """
        prompt = para_config['prompt']
        node_id = para_config.get('id')
        target_sentences = para_config.get('target_sentences', 5)

        # 阶段0: 网络检索（如果启用）
        search_context = ""
        if self.web_search and self.web_search.enabled:
            # 从提示词中提取主题关键词
            topic = prompt[:100]  # 使用提示词前100字符作为搜索查询
            try:
                search_results = asyncio.run(self.web_search.search(topic))

                if search_results:
                    search_context = self.web_search.format_results_as_context(search_results) + "\n\n"
                    logger.info(f"已添加网络检索上下文")
            except Exception as e:
                logger.warning(f"网络检索失败: {e}")
        
        # 阶段1: 生成句子骨架与检索查询
        skeleton_prompt = f"""{additional_context}{search_context}

{prompt}

要求：
1. 生成{target_sentences}个句子的骨架（不含引用）
2. 为每个句子生成语义检索查询词（用于文献检索）

【重要】请直接输出内容，不要有任何开场白、解释或额外回应。

输出格式：
句子1: [骨架句子]
查询1: [检索关键词]

句子2: [骨架句子]
查询2: [检索关键词]
...
"""
        
        skeleton_response = self.router.generate(
            skeleton_prompt,
            self._format_context_string(),
            node_id=node_id
        )
        logger.debug(f"骨架生成原始响应:\n{skeleton_response}")
        
        # 验证骨架响应不为空
        if not skeleton_response or len(skeleton_response.strip()) < 50:
            logger.warning(f"骨架生成响应过短或为空，使用直接生成模式")
            # 直接生成模式：跳过骨架+引用流程
            direct_prompt = f"""{additional_context}

{prompt}

【重要】请直接输出600-800字的学术论文段落内容，不要有任何开场白或额外说明。
【禁止】不要添加任何引用编号如[1][2]等，正文不需要引用。
"""
            direct_result = self.router.generate(
                direct_prompt,
                self._format_context_string(),
                node_id=node_id,
                max_tokens=16000
            )
            # [*] 清理AI可能自己编造的假引用编号
            cleaned = self._clean_ai_artifacts(direct_result)
            cleaned = self._remove_fake_citations(cleaned)
            return cleaned
        
        # 解析骨架和查询
        sentences_and_queries = self._parse_skeleton_response(skeleton_response)
        
        # 验证解析结果
        if not sentences_and_queries:
            logger.warning(f"骨架解析失败，使用直接输出模式")
            # 直接使用AI响应，清理后返回（去除假引用）
            cleaned = self._clean_ai_artifacts(skeleton_response)
            return self._remove_fake_citations(cleaned)
        
        # 阶段2: 本地检索挂引用
        cited_sentences = []
        for sentence, query in sentences_and_queries:
            cited_sentence, _ = self.citation_mgr.generate_sentence_with_citations(
                sentence, query
            )
            cited_sentences.append(cited_sentence)
        
        # 阶段3: 轻度润色（可选）
        paragraph_draft = '\n'.join(cited_sentences)
        
        # 最终验证：确保输出不为空
        if not paragraph_draft or len(paragraph_draft.strip()) < 50:
            logger.warning(f"段落生成结果过短，使用骨架响应作为回退")
            cleaned = self._clean_ai_artifacts(skeleton_response)
            return self._remove_fake_citations(cleaned)
        
        return paragraph_draft

    def expand_full_paper_content(self, text):
        """
        全文档智能扩写（后处理模式）
        - 识别并跳过标题
        - 对正文段落进行学术扩写
        """
        paragraphs = text.split('\n\n')
        expanded_paragraphs = []
        
        total = len(paragraphs)
        for idx, para in enumerate(paragraphs):
            para = para.strip()
            
            # 保护逻辑：跳过标题、短文本或代码块标记
            if not para:
                continue
            if para.startswith('#'):  # 标题
                expanded_paragraphs.append(para)
                continue
            if para.startswith('```') or para.startswith('---'):  # 代码或分割线
                expanded_paragraphs.append(para)
                continue
            if len(para) < 50:  # 短句不扩写
                expanded_paragraphs.append(para)
                continue
                
            logger.info(f"正在执行终极扩写 {idx+1}/{total} (原长: {len(para)})")
            
            prompt = f"""【这里是需要优化的段落】
{para}

【请为我优化梳理这一段文本，使之逻辑顺畅。这个问题看似简单实际上非常难，请你谨慎的思考，深入的研究和搜索。让我们一步一步来，从多个角度考虑这个问题。】

学术化表达，逻辑严谨，层层递进，语言要平实的学术语言，不要夸张，不要自造新词，少用引号，不要创造新概念，多用学术表达，要易懂，但是用词要有专业性，整体要有较高的学术质感。禁止使用类似"首先""其次""再次""最后"等机械感很强的词汇，也禁止使用"重构""重建""填补空白"等夸张吹嘘表达，同时更禁止随意使用引号、冒号、破折号等一看就很AI的标点符号，要自然表述，禁止任何的小标题和分点，形成段落化长文本，多分几个自然段，不要出现"如何""何以""为何"等提问字样。字数适中。

 **保留引用**：绝对不能删除原文中的文献引用编号（如[1]、[2-3]），它们必须保留在扩写后的对应位置。

请直接输出扩写后的段落，不要包含任何前言后语。
"""
            try:
                expanded_para = self.router.generate(prompt, context="严格扩写专家", max_tokens=16000)
                # 简单清洗
                if expanded_para:
                    clean_para = expanded_para.replace('首先', '').replace('其次', '').replace('**', '')
                    # [*] 清理AI可能编造的虚假引用
                    clean_para = self._remove_fake_citations(clean_para)
                    expanded_paragraphs.append(clean_para)
                else:
                    expanded_paragraphs.append(para)
            except Exception as e:
                logger.error(f"段落扩写失败: {e}")
                expanded_paragraphs.append(para)
                
        return "\n\n".join(expanded_paragraphs)
    
    def _parse_skeleton_response(self, response):
        """解析骨架和查询响应 - 增强版"""
        import re
        
        sentences_and_queries = []
        
        # 匹配 "句子N:" 和 "查询N:" 或其他变体
        lines = response.split('\n')
        
        sentence = ""
        query = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 支持多种格式: "句子1:", "句子 1:", "1. ", "第1句:" 等
            if re.match(r'(句子|Sentence|第)\s*\d+[\s:：]', line, re.IGNORECASE):
                sentence = re.sub(r'(句子|Sentence|第)\s*\d+[\s:：]\s*', '', line, flags=re.IGNORECASE).strip()
            elif re.match(r'(查询|Query|关键词)\s*\d+[\s:：]', line, re.IGNORECASE):
                query = re.sub(r'(查询|Query|关键词)\s*\d+[\s:：]\s*', '', line, flags=re.IGNORECASE).strip()
                
                if sentence and query:
                    sentences_and_queries.append((sentence, query))
                    sentence = ""
                    query = ""
            # 备用格式：如果是数字开头的句子
            elif re.match(r'^\d+[\.、．]', line):
                content = re.sub(r'^\d+[\.、．]\s*', '', line).strip()
                if content and len(content) > 10:
                    # 既作为句子又作为查询
                    if sentence:
                        sentences_and_queries.append((sentence, sentence))
                    sentence = content
        
        # 如果最后有未配对的句子
        if sentence:
            sentences_and_queries.append((sentence, sentence))
        
        # 如果解析失败，尝试简单分句（增强版）
        if not sentences_and_queries:
            # 尝试按中文句号分句
            sentences = [s.strip() for s in response.split('。') if s.strip() and len(s.strip()) > 10]
            for s in sentences[:8]:  # 最多8句
                # 清理开头的编号
                clean_s = re.sub(r'^[\d\(\)（）一二三四五六七八九十]+[\.、．\s]*', '', s).strip()
                if clean_s:
                    sentences_and_queries.append((clean_s + '。', clean_s))
        
        logger.debug(f"骨架解析: 提取到 {len(sentences_and_queries)} 个句子对")
        return sentences_and_queries

    def _parse_paper_into_sections(self, paper_text):
        """
        解析论文为结构化章节
        
        Returns:
            {
                'abstract': {'title': '...', 'content': '...'},
                'sections': [{'title': '...', 'content': '...', 'subsections': [...]}],
                'references': {'title': '...', 'content': '...'}
            }
        """
        result = {
            'abstracts': [],
            'sections': [],
            'references': None
        }
        
        lines = paper_text.split('\n')
        current_section = None
        current_subsection = None
        buffer = []
        
        for line in lines:
            # 增强标题识别：支持多种格式
            # 一级标题模式
            level1_patterns = [
                (r'^##\s+(.+)', lambda m: m.group(1)),           # ## 标题
                (r'^#\s+([^#].+)', lambda m: m.group(1)),        # # 标题 (非 ##)
                (r'^[一二三四五六七八九十]+[、．.\s]\s*(.+)', lambda m: m.group(1)),  # 一、标题 或 一．标题 或 一 标题
            ]
            # 二级标题模式
            level2_patterns = [
                (r'^###\s+(.+)', lambda m: m.group(1)),          # ### 标题
                (r'^（[一二三四五六七八九十]+）\s*(.+)', lambda m: m.group(1)),    # （一）标题
                (r'^\d+[\.、]\s*(.+)', lambda m: m.group(1)),   # 1. 或 1、标题
            ]
            
            # 检查一级标题
            is_level1 = False
            for pattern, extractor in level1_patterns:
                match = re.match(pattern, line)
                if match:
                    # 保存之前的内容
                    if current_subsection:
                        current_subsection['content'] = '\n'.join(buffer).strip()
                    elif current_section:
                        if not current_section.get('subsections'):
                            current_section['content'] = '\n'.join(buffer).strip()
                    buffer = []
                    current_subsection = None
                    
                    title = extractor(match).strip()
                    
                    # 识别特殊章节 (增强兼容性)
                    if '摘要' in title or '关键词' in title or 'Abstract' in title or 'Keywords' in title:
                        current_section = {'title': title, 'content': '', 'type': 'abstract'}
                        result['abstracts'].append(current_section)
                    elif '参考文献' in title or 'References' in title or 'Reference' in title:
                        current_section = {'title': title, 'content': '', 'type': 'references'}
                        result['references'] = current_section
                    else:
                        current_section = {'title': title, 'content': '', 'subsections': [], 'type': 'body'}
                        result['sections'].append(current_section)
                    
                    is_level1 = True
                    break
            
            if is_level1:
                continue
                    
            # 检查二级标题
            is_level2 = False
            if current_section and current_section.get('type') == 'body':
                for pattern, extractor in level2_patterns:
                    match = re.match(pattern, line)
                    if match:
                        subtitle_candidate = extractor(match).strip()
                        
                        # 过滤骨架格式
                        skeleton_patterns = ['句子', '查询', '骨架', 'Sentence', 'Query']
                        is_skeleton = any(p in subtitle_candidate for p in skeleton_patterns)
                        
                        if not is_skeleton:
                            if current_subsection:
                                current_subsection['content'] = '\n'.join(buffer).strip()
                                buffer = []
                            
                            current_subsection = {'title': subtitle_candidate, 'content': ''}
                            current_section['subsections'].append(current_subsection)
                            is_level2 = True
                            break
            
            if is_level2:
                continue
            
            # 普通内容
            buffer.append(line)
        
        # 处理最后的缓冲区
        if buffer:
            if current_subsection:
                current_subsection['content'] = '\n'.join(buffer).strip()
            elif current_section:
                if current_section.get('subsections'):
                    # 追加到最后一个子章节
                    if current_section['subsections']:
                        current_section['subsections'][-1]['content'] += '\n' + '\n'.join(buffer).strip()
                else:
                    current_section['content'] = '\n'.join(buffer).strip()
        
        # 兜底主要逻辑：如果没解析出参考文献内容，但全文包含"参考文献"
        if (not result['references'] or not result['references']['content'].strip()) and '参考文献' in paper_text:
            logger.warning("触发参考文献兜底提取")
            # 查找 Reference 标题（## 参考文献 或 # 参考文献）
            # 优化正则：允许没有换行符（EOF情况）
            pattern = r'(?:^|\n)(#{1,2}\s*参考文献[^\n]*)(\n[\s\S]*|$)'
            match = re.search(pattern, paper_text)
            if match:
                title = match.group(1).strip().replace('#', '').strip()
                content = match.group(2).strip()
                
                # 如果后续还有一级标题（## 或 #），则截断
                # 排除 ### (二级标题)
                next_header = re.search(r'\n#{1,2}\s+[^#]', content)
                if next_header:
                    content = content[:next_header.start()].strip()
                
                if content and len(content) > 10:
                    result['references'] = {'title': title, 'content': content, 'type': 'references'}
                    logger.info(f"兜底提取成功: {len(content)}字")

        # Debug: Log parsed structure summary
        logger.debug(f"解析结果: Section count={len(result['sections'])}")
        if result['references']:
            logger.debug(f"参考文献解析: Title='{result['references']['title']}', Content Length={len(result['references']['content'])}")
            if not result['references']['content']:
                logger.warning("参考文献内容为空！")
        else:
            logger.warning("未解析到参考文献章节")
            
        return result

    def optimize_paper_sections(self, paper_text):
        """
        V2: 结构保留优化 - 只优化正文内容，保留所有标题
        
        策略：提取所有标题，只优化正文段落，用原始标题重新组装
        保持不变：标题、摘要、参考文献
        """
        logger.info("="*60)
        logger.info("开始V2结构保留优化")
        logger.info("="*60)
        
        original_length = len(paper_text)
        logger.info(f"原始论文长度: {original_length}字")
        
        # 解析论文结构
        parsed = self._parse_paper_into_sections(paper_text)
        
        # 统计解析结果
        section_count = len(parsed['sections'])
        subsection_count = sum(len(s.get('subsections', [])) for s in parsed['sections'])
        logger.info(f"解析结果: {section_count}个一级章节, {subsection_count}个二级章节")
        
        if section_count == 0:
            logger.warning("未找到章节结构，跳过优化")
            return paper_text
        
        optimized_parts = []
        
        # 1. 论文标题（如果有）
        title_match = re.search(r'^(#\s+[^#\n]+)', paper_text, re.MULTILINE)
        if title_match:
            optimized_parts.append(title_match.group(1).strip())
            logger.info(f"保留标题: {title_match.group(1)[:30]}...")
        
        # 2. 摘要保持不变 (遍历所有摘要类章节)
        if parsed.get('abstracts'):
            for abs_sec in parsed['abstracts']:
                optimized_parts.append(f"## {abs_sec['title']}\n\n{abs_sec['content']}")
            logger.info(f"摘要/关键词 ({len(parsed['abstracts'])}个) - 保持不变")
        
        # 3. 优化每个主体章节（保留标题，只优化内容）
        # [*] 关键修改：从"引言"章节开始优化，之前的内容保持不变
        found_introduction = False
        for section in parsed['sections']:
            section_title = section['title']
            
            # 检测是否到达引言章节
            if not found_introduction:
                if '引言' in section_title or 'Introduction' in section_title or section_title.startswith('一'):
                    found_introduction = True
                    logger.info(f"从此章节开始优化: {section_title}")
                else:
                    # 引言之前的章节保持不变（可能是被误识别的摘要等）
                    logger.info(f"跳过优化（引言之前）: {section_title}")
                    content = section.get('content', '')
                    if content:
                        optimized_parts.append(f"## {section_title}\n\n{content}")
                    else:
                        optimized_parts.append(f"## {section_title}")
                    continue
            
            logger.info(f"处理章节: {section_title}")
            
            section_parts = [f"## {section_title}"]  # 保留原始标题
            
            if section.get('subsections'):
                # 有二级标题，逐个处理
                for sub in section['subsections']:
                    sub_title = sub['title']
                    sub_content = sub.get('content', '')
                    
                    # 保留原始二级标题
                    if sub_content and len(sub_content) > 100:
                        logger.info(f"  优化: ### {sub_title[:20]}... ({len(sub_content)}字)")
                        # 只发送内容给AI，不包含标题
                        optimized_content = self._optimize_content_only(sub_content, sub_title)
                        section_parts.append(f"### {sub_title}\n\n{optimized_content}")
                    else:
                        section_parts.append(f"### {sub_title}\n\n{sub_content}")
            else:
                # 无二级标题（引言、结论等）
                content = section.get('content', '')
                if content and len(content) > 100:
                    logger.info(f"  优化内容: ({len(content)}字)")
                    optimized_content = self._optimize_content_only(content, section_title)
                    section_parts.append(optimized_content)
                else:
                    section_parts.append(content)
            
            optimized_parts.append('\n\n'.join(section_parts))
        
        # 4. 参考文献处理（验证同步 + 保留原有）
        # [*] 新增：验证正文引用与参考文献的一致性
        body_text = '\n\n'.join(optimized_parts)
        sync_report = self._validate_and_log_citations(body_text, parsed.get('references'))
        
        if parsed['references']:
            ref_content = parsed['references']['content']
            # 如果有缺失的引用，尝试从citation_mgr补充
            if sync_report.get('missing_in_refs'):
                logger.warning(f"正文中有引用未在参考文献中找到: {sync_report['missing_in_refs']}")
                # 尝试从citation_mgr获取补充
                supplemental_refs = self._get_supplemental_references(sync_report['missing_in_refs'])
                if supplemental_refs:
                    ref_content = ref_content + '\n\n' + supplemental_refs
                    logger.info(f"已补充 {len(sync_report['missing_in_refs'])} 条参考文献")
            
            optimized_parts.append(f"## {parsed['references']['title']}\n\n{ref_content}")
            logger.info("参考文献 - 验证同步完成")
        
        result = '\n\n'.join(optimized_parts)
        
        # [*] 新增：验证并修复引用分布（修复超限编号和过度复用问题）
        if hasattr(self, 'citation_mgr') and self.citation_mgr:
            result = self.citation_mgr.validate_and_fix_distribution(result)
        
        logger.info(f"V2优化完成: {original_length}字 -> {len(result)}字")
        
        return result
    
    def _optimize_content_only(self, content, context_title):
        """只优化正文内容（不包含标题），带重试机制"""
        
        original_length = len(content)
        
        for attempt in range(1, 4):  # 最多3次尝试
            extra_warning = ""
            if attempt > 1:
                extra_warning = f"""
【警告 - 第{attempt}次尝试】
上次输出长度严重不足！原文{original_length}字，你只输出了约{int(original_length*0.3)}字。
你必须输出至少{int(original_length*0.9)}字的完整润色内容！
"""
            
            prompt = f"""【任务】对以下中文学术段落进行润色优化。

【重要】原文共{original_length}字，你的输出必须达到{int(original_length*0.9)}-{int(original_length*1.2)}字！
{extra_warning}
【段落所属章节】{context_title}

【待优化段落（共{original_length}字）】
{content}

【严格要求 - 必须全部遵守】
1. [重要] 输出长度必须≥{int(original_length*0.9)}字！禁止删减、精简、缩写内容！
2. 全程使用中文，禁止出现英文单词
3. 禁止使用"【后续内容保持不变】"、"...省略"等任何省略语
4. 禁止使用"首先、其次、最后、综上所述"等机械连接词
5. 必须保留所有引用编号[1][2]等
6. 不要输出任何标题，只输出正文段落
7. 逐句润色，保持原文的所有信息点和论据

【再次强调】你必须输出完整的{original_length}字左右的润色内容，不能删减！

【输出】直接输出润色后的完整段落内容（{int(original_length*0.9)}-{int(original_length*1.2)}字）："""
            
            try:
                result = self.router.generate(prompt, context="中文润色专家", max_tokens=16384)
                result = self._clean_ai_artifacts(result)
                
                # 移除可能的标题（AI可能会添加）
                result = re.sub(r'^#+\s+.*\n', '', result).strip()
                
                # 验证
                result_length = len(result)
                ratio = result_length / original_length
                
                # 检查英文
                has_english = bool(re.search(r'[A-Za-z]{3,}(?:\s+[A-Za-z]{3,}){9,}', result))
                # 检查占位符
                has_lazy = any(p in result for p in ['【后续内容保持不变】', '...省略', '此处省略'])
                # [*] 移除引用验证 - 优化阶段的引用都是初稿阶段生成的合法引用
                
                if 0.7 <= ratio <= 100.0 and not has_english and not has_lazy and result:
                    logger.info(f"    [OK] 优化成功 ({original_length}字 -> {result_length}字)")
                    # [*] 清理AI可能编造的虚假引用
                    result = self._remove_fake_citations(result)
                    return result
                else:
                    logger.warning(f"    [FAIL] 尝试{attempt}失败 (比例={ratio:.1f}, 英文={has_english}, 占位符={has_lazy})")
                    
            except Exception as e:
                logger.error(f"    优化失败: {e}")
        
        # 所有尝试失败，返回原文
        logger.warning(f"    所有尝试失败，保留原文")
        return content
    
    def _optimize_whole_body(self, body_text, attempt=1):
        """整篇优化论文主体"""
        
        # 根据重试次数调整提示词强度
        extra_warning = ""
        if attempt > 1:
            extra_warning = f"""
【第{attempt}次尝试 - 上次失败原因】
上次输出不合格。请特别注意：
- 绝对不能使用英文
- 绝对不能使用"【后续内容保持不变】"等省略语
- 必须输出完整内容
"""
        
        prompt = f"""【任务】对以下中文学术论文进行润色优化。
{extra_warning}
【原文】
{body_text}

【严格要求】
1. 全程使用中文，不得出现任何英文单词或句子
2. 禁止使用"【后续内容保持不变】""...省略..."等任何形式的省略
3. 禁止使用"首先、其次、最后、综上所述"等机械连接词
4. 禁止使用"重构、重建、填补空白"等夸张表达
5. 必须保留所有章节标题（##、###格式）
6. 必须保留所有引用编号[1][2]等
7. 输出长度必须与原文相当

【输出】
直接输出优化后的完整中文论文内容，无需任何解释。"""

        try:
            result = self.router.generate(
                prompt, 
                context="中文学术论文润色专家，严格遵守所有要求",
                max_tokens=60000
            )
            result = self._clean_ai_artifacts(result)
            
            if result and len(result) > 500:
                # [*] 清理AI可能编造的虚假引用
                result = self._remove_fake_citations(result)
                return result
            return None
            
        except Exception as e:
            logger.error(f"优化失败: {e}")
            return None

    def _optimize_section_content(self, content, section_title):
        """用用户指定的提示词优化单个章节内容 - 增强版"""
        
        # 计算原始内容长度（作为验证基准）
        original_length = len(content)
        
        prompt = f"""【任务目标】
请对以下学术论文段落进行润色和优化。

【待优化内容】
{content}

【优化要求】
1. **语言要求**：
   - 必须使用全中文输出，严禁出现任何英文内容
   - 使用地道的中文学术表达，逻辑严谨，层层递进
   - 语言平实自然，避免夸张和自造新词

2. **严禁以下行为（违反将导致输出无效）**：
   - 严禁使用"首先"、"其次"、"最后"等机械连接词
   - 严禁使用"重构"、"重建"、"填补空白"等夸张词汇
   - **严禁出现"【后续内容保持不变】""...省略...""此处省略"或任何形式的省略语**
   - **严禁将任何内容翻译成英文**
   - 严禁删除原文的章节标题（如##、###开头的行）
   - 严禁大幅缩减内容长度

3. **内容完整性（最重要）**：
   - 必须输出**完整**的优化后内容
   - 必须保留原文的**所有**核心论点和细节
   - 输出长度应与原文相当（至少达到原文的90%）
   - 不得截断、省略、概括或合并原文内容

4. **格式要求**：
   - 删除"句子N:"、"查询N:"等骨架标记
   - 删除AI开场白（如"好的""以下是"）和元注释
   - **必须保留**原文中的引用编号（如[1][2]）
   - 保留原有的Markdown标题标记（如###）

【输出格式】
直接输出优化后的中文正文内容，不要包含任何前言后语、解释或总结。
"""
        
        try:
            result = self.router.generate(prompt, context="中文学术优化专家，严格遵守完整性要求", max_tokens=32768)
            
            # 额外清理
            result = self._clean_ai_artifacts(result)
            
            # 检测是否包含英文段落（超过20个连续英文单词视为英文内容）
            import re
            english_pattern = r'[A-Za-z]{3,}(?:\s+[A-Za-z]{3,}){19,}'
            if re.search(english_pattern, result):
                logger.warning(f"优化结果包含大量英文内容，保留原文")
                return content
            
            # 检测是否包含省略标记
            lazy_patterns = ['【后续内容保持不变】', '【其他内容', '...省略', '（略）', '此处省略', '[省略]']
            for lazy_pattern in lazy_patterns:
                if lazy_pattern in result:
                    logger.warning(f"优化结果包含省略标记'{lazy_pattern}'，保留原文")
                    return content
            
            # [*] 移除引用验证 - 优化阶段的引用是初稿生成的合法引用

            # 验证内容完整性：优化后不应该明显变短
            if len(result) < original_length * 0.7:
                logger.warning(f"优化后内容过短（原{original_length}字 -> 现{len(result)}字），保留原文")
                return content
            
            # 验证结果不为空
            if not result or len(result.strip()) < 100:
                logger.warning(f"优化结果为空或过短，保留原文")
                return content
            
            logger.info(f"  章节优化完成: {original_length}字 -> {len(result)}字")
            return result
            
        except Exception as e:
            logger.error(f"章节优化失败: {e}")
            return content

    def _clean_ai_artifacts(self, text):
        """清理AI生成痕迹（保留正常引用[1][2]等）"""
        if not text:
            return text
        
        original_text = text
        
        # [*] 0. 清理可能导致编码问题的特殊Unicode字符
        # 这些字符在GBK编码的Windows控制台中无法正确显示
        unicode_cleanup = {
            '\u2713': '',  # ✓ 检查标记
            '\u2714': '',  # ✔ 粗检查标记
            '\u2717': '',  # ✗ X标记
            '\u2718': '',  # ✘ 粗X标记
            '\u26a0': '',  # ⚠ 警告符号
            '\u2022': '-',  # • 项目符号 -> 短横线
            '\u2023': '>',  # ‣ 三角项目符号
            '\u2b50': '',  # ⭐ 星星
            '\u2764': '',  # ❤ 心形
            '\u2709': '',  # ✉ 信封
            '\u2605': '',  # ★ 实心星
            '\u2606': '',  # ☆ 空心星
            '\u279c': '->',  # ➜ 箭头
            '\U0001F4A1': '',  # 💡 灯泡emoji
            '\U0001F4DD': '',  # 📝 备忘录emoji
            '\U0001F389': '',  # 🎉 庆祝emoji
        }
        for char, replacement in unicode_cleanup.items():
            text = text.replace(char, replacement)
        # 移除emoji范围内的字符 (U+1F300 - U+1F9FF)
        text = re.sub(r'[\U0001F300-\U0001F9FF]', '', text)
        # 移除其他杂项符号 (U+2600 - U+26FF中除了已处理的)
        text = re.sub(r'[\u2600-\u26FF](?<!\u26a0)', '', text)
        
        # [*] 0.5 提取Markdown代码块内容（如果AI把正文放在代码块里）
        # 匹配 ```markdown ... ``` 或 ```text ... ``` 或 ``` ... ```
        code_block = re.search(r'```(?:markdown|text)?\s*([\s\S]*?)\s*```', text, re.DOTALL)
        if code_block:
            text = code_block.group(1).strip()
        
        # [*] 1. 删除骨架句子格式 (更精确的匹配，避免误删)
        text = re.sub(r'^[\*]*句子\s*\d+\s*[:：].*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[\*]*查询\s*\d+\s*[:：].*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'\[骨架句子\]', '', text)
        
        # [*] 2. 删除[citation:N]格式（但保留[1][2]等正常引用）
        text = re.sub(r'\[citation:\d+\]', '', text)
        
        # [*] 3. 删除AI开场白
        patterns = [
            r'^好的[，,]?请看.*?[:：]\s*',
            r'^以下是.*?[:：]\s*',
            r'^根据您的要求.*?[:：]\s*',
            r'^下面是.*?[:：]\s*',
            r'^好的，我.*?[:：]\s*',
            r'^请看下方.*?[:：]?\s*',
        ]
        for p in patterns:
            text = re.sub(p, '', text, flags=re.MULTILINE)
        
        # [*] 4. 删除元注释（注：...）
        text = re.sub(r'（注[：:].*?）', '', text)
        text = re.sub(r'\(注[：:].*?\)', '', text)
        
        # [*] 5. 删除"参考资料："格式块
        text = re.sub(r'参考资料[：:]\s*\n(\[\d+\][^\n]+\n)*', '', text)
        
        # [*] 6. 删除错误的标题格式
        text = re.sub(r'主体内容大纲[:：]\s*', '', text)
        
        # [*] 7. 删除Markdown加粗符号（但保留标题符号）
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        
        # [*] 8. 删除示例/模板痕迹
        text = re.sub(r'\[此处[^\]]*\]', '', text)
        text = re.sub(r'【[此处填写][^\]]*】', '', text)
        
        # [*] 9. 清理多余空行和空白
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'^\s+$', '', text, flags=re.MULTILINE)
        
        # [*] 10. 移除开头的标题回显（AI可能在正文开头重复标题）
        lines = text.strip().split('\n')
        if len(lines) >= 2:
            first_line = lines[0].strip()
            second_line = lines[1].strip()
            # 检查第一行是否是标题格式
            if first_line.startswith('#') or re.match(r'^[一二三四五六七八九十]+[、．.]', first_line):
                # 比较清理后的标题
                clean_first = re.sub(r'^#+\s*', '', first_line).strip()
                clean_second = re.sub(r'^#+\s*', '', second_line).strip()
                # 如果前两行几乎相同（可能有标点差异），删除第二行
                if clean_first and clean_second and (clean_first == clean_second or clean_first in clean_second or clean_second in clean_first):
                    lines = [lines[0]] + lines[2:]
                    text = '\n'.join(lines)
                    logger.debug(f"移除了重复的标题行: {clean_second[:30]}...")
        
        if not text.strip() and len(original_text) > 50:
            logger.warning("清理后内容为空但原始内容较长，可能清理过度，回退到原始内容")
            return original_text
        
        # [*] 修复：正常路径必须返回清理后的文本
        return text.strip()
    
    def _remove_fake_citations(self, text):
        """
        移除AI在直接生成模式下编造的假引用编号
        只保留citation_tracker中记录的合法引用
        """
        import re
        
        if not text or not hasattr(self, 'citation_mgr'):
            return text
        
        # 获取合法的引用编号
        valid_nums = set(self.citation_mgr.citation_tracker.values())
        
        def replace_citation(match):
            num = int(match.group(1))
            if num in valid_nums:
                return match.group(0)  # 保留合法引用
            else:
                logger.debug(f"移除假引用: [{num}]")
                return ""  # 移除非法引用
        
        # 替换所有[N]格式引用
        cleaned = re.sub(r'\[(\d+)\]', replace_citation, text)
        
        # 清理可能留下的双空格
        cleaned = re.sub(r'  +', ' ', cleaned)
        cleaned = re.sub(r' 。', '。', cleaned)
        
        return cleaned
            
    def _validate_citation_consistency(self, original_text, generated_text):
        """
        验证生成的文本中的引用是否合法
        
        改进逻辑：检查引用编号是否在 citation_tracker 中有记录
        而不是检查是否在原段落中（因为原段落只是全文的一部分）
        """
        import re
        
        if not generated_text:
            return True, []
        
        # 提取生成文本中的引用编号
        generated_nums = set()
        for match in re.finditer(r'\[(\d+)\]', generated_text):
            generated_nums.add(int(match.group(1)))
        
        if not generated_nums:
            return True, []
        
        # 获取 citation_tracker 中记录的所有编号
        if hasattr(self, 'citation_mgr') and self.citation_mgr:
            tracker_nums = set(self.citation_mgr.citation_tracker.values())
        else:
            # 如果没有 citation_mgr，回退到原文检查
            original_nums = set()
            for match in re.finditer(r'\[(\d+)\]', original_text):
                original_nums.add(int(match.group(1)))
            tracker_nums = original_nums
        
        # 检查是否有超出 tracker 记录的编号
        unknown_nums = generated_nums - tracker_nums
        
        if unknown_nums:
            return False, [f'[{n}]' for n in sorted(unknown_nums)]
        return True, []
    
    def _validate_and_log_citations(self, body_text, references_section):
        """
        验证正文中的引用与参考文献列表的一致性
        
        Args:
            body_text: 论文正文（不含参考文献）
            references_section: 解析出的参考文献章节 {'title': ..., 'content': ...}
            
        Returns:
            验证报告 {'text_nums': set, 'ref_nums': set, 'missing_in_refs': set, 'unused_in_text': set}
        """
        import re
        
        report = {
            'text_nums': set(),
            'ref_nums': set(),
            'missing_in_refs': set(),
            'unused_in_text': set()
        }
        
        # 1. 提取正文中的引用编号
        text_citation_nums = set()
        for match in re.finditer(r'\[(\d+)\]', body_text):
            text_citation_nums.add(int(match.group(1)))
        report['text_nums'] = text_citation_nums
        
        # 2. 提取参考文献中的编号
        ref_nums = set()
        if references_section and references_section.get('content'):
            ref_content = references_section['content']
            for match in re.finditer(r'^\s*\[(\d+)\]', ref_content, re.MULTILINE):
                ref_nums.add(int(match.group(1)))
        report['ref_nums'] = ref_nums
        
        # 3. 计算差异
        report['missing_in_refs'] = text_citation_nums - ref_nums  # 正文有，参考文献没有
        report['unused_in_text'] = ref_nums - text_citation_nums    # 参考文献有，正文没有
        
        # 4. 日志记录
        if report['missing_in_refs']:
            logger.warning(f"引用一致性检查: 正文中{len(report['missing_in_refs'])}个引用未在参考文献中: {sorted(report['missing_in_refs'])}")
        if report['unused_in_text']:
            logger.info(f"引用一致性检查: 参考文献中{len(report['unused_in_text'])}个条目未在正文使用: {sorted(report['unused_in_text'])}")
        
        if not report['missing_in_refs'] and not report['unused_in_text']:
            logger.info(f"引用一致性检查: 完全匹配 ({len(text_citation_nums)}个引用)")
        
        return report
    
    def _get_supplemental_references(self, missing_nums):
        """
        从citation_mgr获取缺失引用编号的参考文献条目
        
        Args:
            missing_nums: 缺失的引用编号集合
            
        Returns:
            补充的参考文献文本（多行）
        """
        import re
        
        if not missing_nums or not hasattr(self, 'citation_mgr'):
            return ""
        
        supplemental = []
        tracker = self.citation_mgr.citation_tracker
        pool = self.citation_mgr.pool
        
        # 反向查找：从citation_num找lit_id
        num_to_lit = {v: k for k, v in tracker.items()}
        
        for num in sorted(missing_nums):
            if num in num_to_lit:
                lit_id = num_to_lit[num]
                # 在pool中查找文献
                lit = next((l for l in pool if l['id'] == lit_id), None)
                if lit:
                    full_cit = lit.get('full_citation', '')
                    clean_cit = re.sub(r'^\[\d+\]\s*', '', full_cit)
                    supplemental.append(f"[{num}] {clean_cit}")
                    logger.info(f"  补充参考文献[{num}]: {clean_cit[:50]}...")
        
        return '\n\n'.join(supplemental)

    def expand_paper_sections(self, paper_text):
        """
        V3: 结构保留扩写 - 只扩写正文内容，保留所有标题
        
        策略：提取所有标题，只扩写正文段落，用原始标题重新组装
        保持不变：标题、摘要、参考文献
        """
        logger.info("="*60)
        logger.info("开始V3结构保留扩写")
        logger.info("="*60)
        
        original_length = len(paper_text)
        logger.info(f"原始论文长度: {original_length}字")
        
        # 解析论文结构
        parsed = self._parse_paper_into_sections(paper_text)
        
        # 统计解析结果
        section_count = len(parsed['sections'])
        subsection_count = sum(len(s.get('subsections', [])) for s in parsed['sections'])
        logger.info(f"解析结果: {section_count}个一级章节, {subsection_count}个二级章节")
        
        if section_count == 0:
            logger.warning("未找到章节结构，跳过扩写")
            return paper_text
        
        expanded_parts = []
        
        # 1. 论文标题（如果有）
        title_match = re.search(r'^(#\s+[^#\n]+)', paper_text, re.MULTILINE)
        if title_match:
            expanded_parts.append(title_match.group(1).strip())
            logger.info(f"保留标题: {title_match.group(1)[:30]}...")
        
        # 2. 摘要保持不变 (遍历所有)
        if parsed.get('abstracts'):
            for abs_sec in parsed['abstracts']:
                expanded_parts.append(f"## {abs_sec['title']}\n\n{abs_sec['content']}")
            logger.info(f"摘要/关键词 ({len(parsed['abstracts'])}个) - 保持不变")
        
        # 3. 扩写每个主体章节（保留标题，只扩写内容）
        # [*] 关键修改：从"引言"章节开始扩写，之前的内容保持不变
        found_introduction = False
        for section in parsed['sections']:
            section_title = section['title']
            
            # 检测是否到达引言章节
            if not found_introduction:
                if '引言' in section_title or 'Introduction' in section_title or section_title.startswith('一'):
                    found_introduction = True
                    logger.info(f"从此章节开始扩写: {section_title}")
                else:
                    # 引言之前的章节保持不变（可能是被误识别的摘要等）
                    logger.info(f"跳过扩写（引言之前）: {section_title}")
                    content = section.get('content', '')
                    if content:
                        expanded_parts.append(f"## {section_title}\n\n{content}")
                    else:
                        expanded_parts.append(f"## {section_title}")
                    continue
            
            logger.info(f"处理章节: {section_title}")
            
            section_parts = [f"## {section_title}"]  # 保留原始标题
            
            if section.get('subsections'):
                # 有二级标题，逐个处理
                for sub in section['subsections']:
                    sub_title = sub['title']
                    sub_content = sub.get('content', '')
                    
                    # 保留原始二级标题
                    if sub_content and len(sub_content) > 100:
                        logger.info(f"  扩写: ### {sub_title[:20]}... ({len(sub_content)}字)")
                        # 只发送内容给AI，不包含标题
                        expanded_content = self._expand_content_only(sub_content, sub_title)
                        section_parts.append(f"### {sub_title}\n\n{expanded_content}")
                    else:
                        section_parts.append(f"### {sub_title}\n\n{sub_content}")
            else:
                # 无二级标题（引言、结论等）
                content = section.get('content', '')
                if content and len(content) > 100:
                    logger.info(f"  扩写内容: ({len(content)}字)")
                    expanded_content = self._expand_content_only(content, section_title)
                    section_parts.append(expanded_content)
                else:
                    section_parts.append(content)
            
            expanded_parts.append('\n\n'.join(section_parts))
        
        # 4. 参考文献处理（验证同步 + 保留原有）
        # [*] 新增：验证正文引用与参考文献的一致性
        body_text = '\n\n'.join(expanded_parts)
        sync_report = self._validate_and_log_citations(body_text, parsed.get('references'))
        
        if parsed['references']:
            ref_content = parsed['references']['content']
            # 如果有缺失的引用，尝试从citation_mgr补充
            if sync_report.get('missing_in_refs'):
                logger.warning(f"正文中有引用未在参考文献中找到: {sync_report['missing_in_refs']}")
                supplemental_refs = self._get_supplemental_references(sync_report['missing_in_refs'])
                if supplemental_refs:
                    ref_content = ref_content + '\n\n' + supplemental_refs
                    logger.info(f"已补充 {len(sync_report['missing_in_refs'])} 条参考文献")
            
            expanded_parts.append(f"## {parsed['references']['title']}\n\n{ref_content}")
            logger.info("参考文献 - 验证同步完成")
        
        result = '\n\n'.join(expanded_parts)
        
        # [*] 新增：验证并修复引用分布（修复超限编号和过度复用问题）
        if hasattr(self, 'citation_mgr') and self.citation_mgr:
            result = self.citation_mgr.validate_and_fix_distribution(result)
        
        logger.info(f"V3扩写完成: {original_length}字 -> {len(result)}字")
        
        return result
    
    def _expand_content_only(self, content, context_title):
        """只扩写正文内容（不包含标题），带重试机制"""
        
        original_length = len(content)
        
        for attempt in range(1, 4):  # 最多3次尝试
            target_min = int(original_length * 1.3)
            target_max = int(original_length * 1.5)
            
            extra_warning = ""
            if attempt > 1:
                extra_warning = f"""
【警告 - 第{attempt}次尝试】
上次输出长度不足！原文{original_length}字，扩写后必须达到{target_min}-{target_max}字。
你上次输出太短，请这次务必达到目标长度！
"""
            
            prompt = f"""【任务】对以下中文学术段落进行深度扩写，使内容更加详实充分。

【重要】原文{original_length}字，扩写后必须达到{target_min}-{target_max}字！
{extra_warning}
【段落所属章节】{context_title}

【待扩写段落（共{original_length}字，需扩写至{target_min}-{target_max}字）】
{content}

【扩写要求 - 必须全部遵守】
1. [重要] 扩写后长度必须≥{target_min}字！必须比原文长30%-50%！
2. 通过增加理论依据、逻辑推演、细节阐述、案例说明来充实内容
3. 全程使用中文，禁止出现英文单词
4. 禁止使用"【后续内容保持不变】"、"...省略"等任何省略语
5. 禁止使用"首先、其次、最后、综上所述"等机械连接词
6. 必须保留所有引用编号[1][2]等
7. 不要输出任何标题，只输出正文段落

【再次强调】你必须输出{target_min}-{target_max}字的扩写内容，不能比原文短！

【输出】直接输出扩写后的完整段落内容（{target_min}-{target_max}字）："""
            
            try:
                result = self.router.generate(prompt, context="中文扩写专家", max_tokens=24576)
                result = self._clean_ai_artifacts(result)
                
                # 移除可能的标题
                result = re.sub(r'^#+\s+.*\n', '', result).strip()
                
                # 验证
                result_length = len(result)
                ratio = result_length / original_length
                # 检查英文
                has_english = bool(re.search(r'[A-Za-z]{3,}(?:\s+[A-Za-z]{3,}){9,}', result))
                # 检查占位符
                has_lazy = any(p in result for p in ['【后续内容保持不变】', '...省略', '此处省略'])
                
                # [*] 移除引用验证 - 扩写阶段的引用是初稿生成的合法引用

                # 扩写后应该变长（至少100%）
                if ratio >= 1.0 and not has_english and not has_lazy and result:
                    logger.info(f"    [OK] 扩写成功 ({original_length}字 -> {result_length}字, +{(ratio-1)*100:.0f}%)")
                    return result
                else:
                    logger.warning(f"    [FAIL] 尝试{attempt}失败 (比例={ratio:.1f}, 英文={has_english}, 占位符={has_lazy})")
                    
            except Exception as e:
                logger.error(f"    扩写失败: {e}")
        
        # 所有尝试失败，返回原文
        logger.warning(f"    所有尝试失败，保留原文")
        return content
    
    def _expand_whole_body(self, body_text, attempt=1):
        """整篇扩写论文主体"""
        
        extra_warning = ""
        if attempt > 1:
            extra_warning = f"""
【第{attempt}次尝试 - 上次失败原因】
上次输出不合格。请特别注意：
- 绝对不能使用英文
- 绝对不能使用省略语
- 扩写后必须比原文更长
"""
        
        prompt = f"""【任务】对以下中文学术论文进行深度扩写，使内容更加详实充分。
{extra_warning}
【原文】
{body_text}

【扩写要求】
1. 将内容扩展至原来的1.3-1.5倍
2. 通过增加理论依据、逻辑推演、细节阐述来充实内容
3. 全程使用中文，不得出现任何英文
4. 禁止使用"【后续内容保持不变】"等省略语
5. 禁止使用"首先、其次、最后"等机械连接词
6. 必须保留所有章节标题（##、###格式）
7. 必须保留所有引用编号[1][2]等
8. 扩写后的内容必须比原文更长

【输出】
直接输出扩写后的完整中文论文内容，无需任何解释。"""

        try:
            result = self.router.generate(
                prompt, 
                context="中文学术论文扩写专家，严格遵守所有要求",
                max_tokens=80000
            )
            result = self._clean_ai_artifacts(result)
            
            if result and len(result) > len(body_text):
                return result
            return None
            
        except Exception as e:
            logger.error(f"扩写失败: {e}")
            return None

    def _expand_section_content(self, content, section_title):
        """扩写单个章节内容 - 增强版"""
        
        original_length = len(content)
        
        prompt = f"""【任务目标】
请对以下学术论文段落进行深度扩写，使其内容更加详实、论证更加充分。

【待扩写内容】
{content}

【扩写要求】
1. **扩写目标**：
   - 在保持核心观点不变的前提下，将篇幅扩展至原来的1.3-1.5倍
   - 通过增加理论依据、逻辑推演、细节阐述来充实内容
   - 保持论述的连贯性和逻辑性

2. **语言要求**：
   - **必须使用全中文输出，严禁出现任何英文内容**
   - 使用地道的中文学术表达，逻辑严谨，层层递进
   - 多使用长句和复合句增强学术感

3. **严禁以下行为（违反将导致输出无效）**：
   - 严禁使用"首先"、"其次"、"最后"等机械连接词
   - **严禁出现"【后续内容保持不变】""...省略...""此处省略"或任何形式的省略语**
   - **严禁将任何内容翻译成英文**
   - 严禁删除原文的任何核心论点
   - 严禁输出比原文更短的内容

4. **内容完整性**：
   - 必须覆盖原文**所有**论点，不得遗漏
   - 扩写后的内容必须**长于**原文
   - 不可截断或概括原文内容

5. **格式要求**：
   - **必须保留**引用编号（如[1][2]）
   - 删除任何骨架标记或AI元注释

【输出格式】
直接输出扩写后的中文正文内容，不要包含任何前言后语、解释或总结。
"""
        
        try:
            result = self.router.generate(prompt, context="中文学术扩写专家，严格遵守扩写要求", max_tokens=32768)
            result = self._clean_ai_artifacts(result)
            
            # 检测是否包含英文段落
            import re
            english_pattern = r'[A-Za-z]{3,}(?:\s+[A-Za-z]{3,}){19,}'
            if re.search(english_pattern, result):
                logger.warning(f"扩写结果包含大量英文内容，保留原文")
                return content
            
            # 检测是否包含省略标记
            lazy_patterns = ['【后续内容保持不变】', '【其他内容', '...省略', '（略）', '此处省略', '[省略]']
            for lazy_pattern in lazy_patterns:
                if lazy_pattern in result:
                    logger.warning(f"扩写结果包含省略标记'{lazy_pattern}'，保留原文")
                    return content
            
            # 验证扩写效果：扩写后应该变长（至少不能变短）
            if len(result) < original_length:
                logger.warning(f"扩写后内容反而变短（原{original_length}字 -> 现{len(result)}字），保留原文")
                return content
            
            # 验证结果不为空
            if not result or len(result.strip()) < 100:
                logger.warning(f"扩写结果为空或过短，保留原文")
                return content
            
            logger.info(f"  章节扩写完成: {original_length}字 -> {len(result)}字 (+{(len(result)/original_length-1)*100:.0f}%)")
            return result
            
        except Exception as e:
            logger.error(f"章节扩写失败: {e}")
            return content

