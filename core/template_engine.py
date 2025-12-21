"""模板引擎 - 解析模板并生成论文"""
import logging
import re
import yaml
import os  # ⭐ 补充缺失的import
from core.model_router import ModelRouter
from core.citation_manager import CitationManager
from core.external_search import ExternalSearchIntegration

logger = logging.getLogger(__name__)

class TemplateEngine:
    """论文模板引擎"""
    
    def __init__(self, template_path, model_router, citation_manager, project_context, pdf_reference_mgr=None, config=None):
        """
        初始化模板引擎
        
        Args:
            template_path: 模板YAML文件路径
            model_router: 大模型路由器
            citation_manager: 引用管理器
            project_context: 项目上下文（题目、关键词等）
            pdf_reference_mgr: PDF参考文档管理器（可选）
            config: 配置对象（用于外部检索）
        """
        self.template_path = template_path
        self.router = model_router
        self.citation_mgr = citation_manager
        self.project_context = project_context
        self.pdf_ref_mgr = pdf_reference_mgr  # ⭐ 新增
        
        # ⭐ 新增：外部检索集成
        self.external_search = ExternalSearchIntegration(config) if config else None
        
        # 加载模板
        self.template = self._load_template()
        logger.info(f"模板引擎初始化: {self.template['template_name']}")
    
    def _load_template(self):
        """加载YAML模板"""
        with open(self.template_path, 'r', encoding='utf-8') as f:
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

    def generate_paper(self):
        """
        生成论文
        
        Returns:
            论文内容字符串
        """
        logger.info("开始生成论文...")
        
        sections_content = []
        
        # 处理动态章节
        expanded_sections = self._expand_dynamic_sections(self.template['sections'])
        
        # 逐章节生成
        # 逐章节生成（跳过摘要）
        body_sections = []
        abstract_section_config = None
        
        for section in expanded_sections:
            # 识别摘要章节
            if '摘要' in section['title'] or 'Abstract' in section['title']:
                abstract_section_config = section
                continue
            
            logger.info(f"生成章节: {section['title']}")
            
            section_text = self._generate_section(section)
            
            # 实时保存中间结果
            if hasattr(self, 'project_context') and 'output_folder' in self.project_context:
                temp_dir = os.path.join(self.project_context['output_folder'], 'temp_sections')
                os.makedirs(temp_dir, exist_ok=True)
                safe_title = "".join([c for c in section['title'] if c.isalnum() or c in (' ', '-', '_')]).strip()
                temp_path = os.path.join(temp_dir, f"{len(sections_content)+1:02d}_{safe_title}.md")
                with open(temp_path, 'w', encoding='utf-8') as f:
                    f.write(section_text)
                logger.info(f"章节已保存临时文件: {temp_path}")

            sections_content.append(section_text)
            body_sections.append(section_text)
        
        # 生成参考文献
        references = self.citation_mgr.generate_reference_list()
        ref_text = ""
        if references:
            ref_text = f"\n\n## 参考文献\n\n{references}"
            sections_content.append(ref_text)
            
        # 组合正文（用于生成摘要）
        full_body_text = "\n\n".join(body_sections)
        
        # ⭐ 最后生成摘要（如果找到配置）
        if abstract_section_config:
            logger.info("生成最终摘要（基于全文，无引用）...")
            abstract_text = self._generate_final_abstract(abstract_section_config, full_body_text)
            # 插入到最前面
            sections_content.insert(0, abstract_text)
            
            # 保存摘要临时文件
            if hasattr(self, 'project_context') and 'output_folder' in self.project_context:
                temp_dir = os.path.join(self.project_context['output_folder'], 'temp_sections')
                temp_path = os.path.join(temp_dir, f"00_最终摘要.md")
                with open(temp_path, 'w', encoding='utf-8') as f:
                    f.write(abstract_text)
        
        # 组合完整论文
        paper = "\n\n".join(sections_content)
        
        logger.info("论文生成完成")
        return paper

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

请只输出摘要内容和关键词。
"""
        return self.router.generate(prompt, context="你是专业的学术编辑，负责撰写摘要", max_tokens=1000)
    
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
                    expanded_section['title'] = f"{section['title']}: {l1_title}"
                    expanded_section['framework_summary'] = item['summary']
                    
                    # ⭐ 关键修改：将二级标题转换为"段落"配置，实现分块生成
                    if item['subsections']:
                        paragraphs = []
                        for sub_idx, sub_title in enumerate(item['subsections']):
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
""",
                                'id': f"{expanded_section.get('id', 'section')}_sub_{idx}_{sub_idx}",
                                'target_sentences': 8
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
            章节内容字符串
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
        
        # ⭐ 阶段0: 联网检索（如果启用）
        search_context = ""
        if self.external_search and self.external_search.enabled:
            # 从提示词中提取主题关键词
            topic = prompt[:100]  # 使用提示词前100字符作为搜索查询
            search_results = self.external_search.search_for_context(topic, num_results=30)
            
            if search_results:
                search_context = search_results + "\n\n"
                logger.info(f"已添加SearXNG检索上下文")
        
        # ⭐ 阶段0+: 检索PDF相关内容（如果启用）
        pdf_context = ""
        if self.pdf_ref_mgr and self.pdf_ref_mgr.documents:
            query = prompt[:200]  # 使用提示词前200字符作为查询
            pdf_snippets = self.pdf_ref_mgr.search_relevant_snippets(query, top_k=2)
            
            if pdf_snippets:
                pdf_context = "\n\n【参考文档片段】\n" + "\n".join(pdf_snippets[:2]) + "\n"
                logger.debug(f"为段落添加了 {len(pdf_snippets)} 个PDF参考片段")
        
        # 阶段1: 生成句子骨架与检索查询
        skeleton_prompt = f"""{additional_context}{search_context}{pdf_context}

{prompt}

要求：
1. 生成{target_sentences}个句子的骨架（不含引用）
2. 为每个句子生成语义检索查询词（用于文献检索）

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
        
        # 解析骨架和查询
        sentences_and_queries = self._parse_skeleton_response(skeleton_response)
        
        # 阶段2: 本地检索挂引用
        cited_sentences = []
        for sentence, query in sentences_and_queries:
            cited_sentence, _ = self.citation_mgr.generate_sentence_with_citations(
                sentence, query
            )
            cited_sentences.append(cited_sentence)
        
        # 阶段3: 轻度润色（可选）
        paragraph_draft = '\n'.join(cited_sentences)
        
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
            
            prompt = f"""
请为我扩写这一段内容。

**原始内容**：
{para}

**扩写要求**：
1. **不改变原意**：核心观点保持一致，通过强化逻辑推理或深化阐述来扩充。
2. **学术深度**：从多个角度考虑，学术化表达，逻辑严谨，层层递进。
3. **语言风格**：平实的学术语言，不要夸张，不造新词，少用引号，不创造新概念。
4. **禁止机械词**：严禁使用“首先”“其次”“再次”“最后”等词汇。
5. **禁止夸张**：严禁使用“重构”“重建”“填补空白”等吹嘘表达。
6. **禁止AI标点**：严禁随意使用引号、冒号、破折号。
7. **形式要求**：严禁使用小标题和分点，只写**一个自然段**。
8. **内容丰富**：字数越多越好，内容越丰富越好（目标：扩写到原来的2-3倍）。
9. **严禁举例**：不要出现任何具体案例，不要出现“如何”“何以”“为何”等提问。
10. **保留引用**：绝对不能删除原文中的文献引用编号（如[1]、[2-3]），它们必须保留在扩写后的对应位置。

请直接输出扩写后的段落，不要包含任何前言后语。
"""
            try:
                expanded_para = self.router.generate(prompt, context="严格扩写专家", max_tokens=2048)
                # 简单清洗
                if expanded_para:
                    clean_para = expanded_para.replace('首先', '').replace('其次', '').replace('**', '')
                    expanded_paragraphs.append(clean_para)
                else:
                    expanded_paragraphs.append(para)
            except Exception as e:
                logger.error(f"段落扩写失败: {e}")
                expanded_paragraphs.append(para)
                
        return "\n\n".join(expanded_paragraphs)
    
    def _parse_skeleton_response(self, response):
        """解析骨架和查询响应"""
        import re
        
        sentences_and_queries = []
        
        # 匹配 "句子N:" 和 "查询N:"
        lines = response.split('\n')
        
        sentence = ""
        query = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if re.match(r'句子\d+[:：]', line):
                sentence = re.sub(r'句子\d+[:：]\s*', '', line).strip()
            elif re.match(r'查询\d+[:：]', line):
                query = re.sub(r'查询\d+[:：]\s*', '', line).strip()
                
                if sentence and query:
                    sentences_and_queries.append((sentence, query))
                    sentence = ""
                    query = ""
        
        # 如果解析失败，尝试简单分句
        if not sentences_and_queries:
            sentences = [s.strip() for s in response.split('。') if s.strip()]
            for s in sentences[:5]:  # 最多5句
                sentences_and_queries.append((s, s))  # 查询词就用句子本身
        
        return sentences_and_queries
