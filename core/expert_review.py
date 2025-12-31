"""5专家AI审稿系统（优化版：客观评分+任务拆解+循环优化）"""
import logging
import re
import json
import asyncio
from core.web_search import WebSearchIntegration

logger = logging.getLogger(__name__)

class ExpertReviewSystem:
    """专家审稿系统（含循环优化机制）"""

    def __init__(self, model_router, output_dir=None, web_search=None,
                 max_rounds=3, target_score=90):
        """
        初始化专家审稿系统

        Args:
            model_router: 大模型路由器
            output_dir: 中间结果保存目录（可选）
            web_search: 网络搜索引擎集成（可选）
            max_rounds: 最大审稿轮次（默认3轮）
            target_score: 合格分数阈值（默认90分）
        """
        self.router = model_router
        self.output_dir = output_dir
        self.web_search = web_search
        self.max_rounds = max_rounds
        self.target_score = target_score
        logger.info(f"专家审稿系统初始化完成（目标评分≥{self.target_score}分，最多{self.max_rounds}轮）")
    
    def review_and_optimize_iteratively(self, paper_content):
        """
        迭代审稿和优化流程（直到≥90分或达到最大轮次）
        
        [*] 核心改进：保持最佳版本，如果修改后评分下降则回退
        """
        logger.info("="*60)
        logger.info("开始迭代审稿优化流程")
        logger.info("="*60)
        
        current_paper = paper_content
        all_reviews = []
        
        # [*] 追踪最佳版本
        best_paper = paper_content
        best_score = 0
        
        for round_num in range(1, self.max_rounds + 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"第 {round_num}/{self.max_rounds} 轮审稿")
            logger.info(f"{'='*60}")
            
            # 执行一轮完整审稿
            review_result = self._single_round_review_and_optimize(current_paper, round_num)
            
            all_reviews.append(review_result)
            optimized_paper = review_result['optimized_paper']
            current_score = review_result['综合评分']
            
            logger.info(f"第{round_num}轮综合评分: {current_score}/100")
            
            # [*] 检查是否比之前更好
            if current_score > best_score:
                best_paper = optimized_paper
                best_score = current_score
                current_paper = optimized_paper
                logger.info(f"[OK] 评分提升！更新最佳版本 ({best_score}分)")
            else:
                # 评分下降，回退到最佳版本
                logger.warning(f"[!] 评分下降 ({current_score} < {best_score})，回退到最佳版本")
                current_paper = best_paper
            
            # 判断是否达标
            if best_score >= self.target_score:
                logger.info(f"[OK] 最佳评分已达{best_score}分（≥{self.target_score}），停止优化")
                break
            else:
                logger.info(f"未达标（需≥{self.target_score}分），继续下一轮优化...")
            
            # [*] 实时保存本轮结果
            if self.output_dir:
                try:
                    import os
                    round_file = os.path.join(self.output_dir, f'expert_review_round_{round_num}.json')
                    with open(round_file, 'w', encoding='utf-8') as f:
                        json.dump(review_result, f, ensure_ascii=False, indent=2)
                    logger.info(f"第{round_num}轮审稿结果已保存: {round_file}")
                except Exception as e:
                    logger.error(f"保存第{round_num}轮审稿结果失败: {e}")
        
        logger.info("="*60)
        logger.info(f"审稿优化流程完成！共{round_num}轮，最终评分{best_score}/100")
        logger.info("="*60)
        
        return {
            'final_paper': best_paper,  # [*] 返回最佳版本
            'rounds': round_num,
            'final_score': best_score,
            'all_reviews': all_reviews
        }
    
    def _single_round_review_and_optimize(self, paper, round_num):
        """
        单轮审稿和优化
        
        Returns:
            {
                'expert_reviews': {...},
                'integrated_feedback': str,
                'task_list': [...],
                'optimized_paper': str,
                '综合评分': float
            }
        """
        # 阶段1: 4位专家并行审稿
        logger.info(f"阶段1: 4位专家并行审稿...")
        
        expert1_feedback = self._expert1_innovation_review(paper)
        expert1_score = self._extract_score(expert1_feedback)
        logger.info(f"  [OK] 专家1（创新点）: {expert1_score}/25")
        
        expert2_feedback = self._expert2_logic_review(paper)
        expert2_score = self._extract_score(expert2_feedback)
        logger.info(f"  [OK] 专家2（逻辑性）: {expert2_score}/25")
        
        expert3_feedback = self._expert3_accuracy_review(paper)
        expert3_score = self._extract_score(expert3_feedback)
        logger.info(f"  [OK] 专家3（准确性）: {expert3_score}/25")
        
        expert4_feedback = self._expert4_norm_review(paper)
        expert4_score = self._extract_score(expert4_feedback)
        logger.info(f"  [OK] 专家4（规范性）: {expert4_score}/25")
        
        # 阶段2: 整合意见并计算综合评分
        logger.info(f"\n阶段2: 专家5整合意见并评分...")
        integrated_result = self._expert5_integrate_feedback(
            expert1_feedback, expert2_feedback, 
            expert3_feedback, expert4_feedback
        )
        
        # [*] 先尝试从专家5整合结果提取评分
        comprehensive_score = self._extract_comprehensive_score(integrated_result)
        
        # [*] 如果提取失败（返回60默认分），直接使用已有的4位专家分数求和
        if comprehensive_score == 60.0:
            direct_sum = expert1_score + expert2_score + expert3_score + expert4_score
            if direct_sum > 0:
                comprehensive_score = direct_sum
                logger.info(f"  使用4位专家分数直接求和: {comprehensive_score}/100")
        
        logger.info(f"  [OK] 综合评分: {comprehensive_score}/100")
        
        # 阶段3: 中间层AI拆解任务
        logger.info(f"\n阶段3: 中间层AI拆解修改任务...")
        task_list = self._task_decomposer(paper, integrated_result)
        logger.info(f"  [OK] 拆解出 {len(task_list)} 个修改任务")
        
        # 阶段4: 写作AI逐条执行任务
        logger.info(f"\n阶段4: 写作AI逐条执行修改...")
        optimized_paper = self._execute_tasks_sequentially(paper, task_list)
        logger.info(f"  [OK] 所有任务执行完成")
        
        return {
            'expert_reviews': {
                'innovation': {'feedback': expert1_feedback, 'score': expert1_score},
                'logic': {'feedback': expert2_feedback, 'score': expert2_score},
                'accuracy': {'feedback': expert3_feedback, 'score': expert3_score},
                'norm': {'feedback': expert4_feedback, 'score': expert4_score}
            },
            'integrated_feedback': integrated_result,
            'task_list': task_list,
            'optimized_paper': optimized_paper,
            '综合评分': comprehensive_score
        }
    
    def _expert1_innovation_review(self, paper):
        """专家1: 创新点审稿（客观严谨但不悲观）"""
        prompt = f"""你是一位资深学术审稿专家，专注于评估论文的创新点。

审稿原则：
- 保持客观、严谨、公正，但不悲观
- 给出真实的评价，不讨好作者，也不过度批评
- 既要指出不足，也要认可优点
- **特别注意**：本文为【纯理论研究】，**禁止**建议加入量化分析、数据统计、实证模型或具体案例分析。
- **绝对禁止**：
  1. **禁止建议删除任何文献引用编号**（如[1]），这是学术规范的红线。
  2. **绝对禁止建议插入图片、图表、表格（Table）或任何形式的图示**。本学科纯理论研究不使用图表。
  3. **禁止建议补充“案例选择标准”、“数据来源说明”或“文本分析步骤”**。这些属于实证/质性研究范畴，纯理论不需要。
  4. **结构铁律**：引言和结论禁止使用任何小标题（必须是纯段落）；正文最多使用二级标题，禁止建议三级标题。

请审阅以下论文，从4个维度评价创新性（每项0-6.25分，总分25分）：

1. **研究问题创新性**：研究问题是否新颖、有价值？
2. **理论视角独特性**：理论框架或分析视角是否有创新？
3. **研究发现原创性**：核心论点和发现是否具有原创性？
4. **差异化程度**：与现有研究的区别度如何？

论文内容：
{paper}

请按以下格式输出（严格遵守格式）：

## 创新点评分
研究问题创新性: X.XX/6.25
理论视角独特性: X.XX/6.25
研究发现原创性: X.XX/6.25
差异化程度: X.XX/6.25
**小计: X.XX/25**

## 主要优点
1. ...
2. ...

## 创新性不足
1. ...
2. ...

## 改进建议
1. ...
2. ...
"""
        
        return self.router.generate(
            prompt,
            context="你是创新点评审专家，客观严谨但不悲观",
            node_id="expert_review",
            max_tokens=32768
        )
    
    def _expert2_logic_review(self, paper):
        """专家2: 逻辑审稿"""
        prompt = f"""你是一位逻辑严密的学术审稿专家，专注于评估论文的行文逻辑。

审稿原则：
- 保持客观、严谨、公正，但不悲观
- 给出真实的评价，不讨好作者，也不过度批评
- 既要指出逻辑漏洞，也要认可合理之处
- **特别注意**：本文为【纯理论研究】，**禁止**建议加入量化分析或案例验证。
- **绝对禁止**：
  1. **禁止建议删除任何文献引用编号**（如[1]）。
  2. **绝对禁止建议插入图片、图表或表格**。
  3. **结构铁律**：引言和结论禁止使用小标题；正文最多到二级标题。

请审阅以下论文，从4个维度评价逻辑性（每项0-6.25分，总分25分）：

1. **整体结构逻辑**：章节安排是否合理、层次清晰？
2. **论证完整性**：论证过程是否完整、严密？
3. **章节衔接**：各部分之间的过渡是否自然？
4. **结论一致性**：结论是否与前文论证一致？

论文内容：
{paper}

请按以下格式输出（严格遵守格式）：

## 逻辑性评分
整体结构逻辑: X.XX/6.25
论证完整性: X.XX/6.25
章节衔接: X.XX/6.25
结论一致性: X.XX/6.25
**小计: X.XX/25**

## 逻辑优势
1. ...
2. ...

## 逻辑缺陷
1. ...
2. ...

## 改进建议
1. ...
2. ...
"""
        
        return self.router.generate(
            prompt,
            context="你是逻辑评审专家，客观严谨但不悲观",
            node_id="expert_review",
            max_tokens=32768
        )
    
    def _expert3_accuracy_review(self, paper):
        """专家3: 准确性审稿"""
        prompt = f"""你是一位严谨的学术审稿专家，专注于评估论文的内容准确性。

审稿原则：
- 保持客观、严谨、公正，但不悲观
- 给出真实的评价，不讨好作者，也不过度批评
- 既要指出错误和不足，也要认可准确之处
- **特别注意**：本文为【纯理论研究】，重点考察概念定义的准确性和理论引用的恰当性。
- **绝对禁止**：
  1. **禁止建议删除任何文献引用编号**（如[1]），这会导致学术不端。
  2. **绝对禁止建议插入图片、图表或表格**。
  3. **结构铁律**：引言和结论必须是纯文本段落。

请审阅以下论文，从4个维度评价准确性（每项0-6.25分，总分25分）：

1. **概念准确性**：核心概念的定义和使用是否准确？
2. **引用适当性**：文献引用是否恰当、权威？
3. **论据充分性**：论据是否充分支撑论点？
4. **事实正确性**：陈述的事实、数据是否准确？

论文内容：
{paper}

请按以下格式输出（严格遵守格式）：

## 准确性评分
概念准确性: X.XX/6.25
引用适当性: X.XX/6.25
论据充分性: X.XX/6.25
事实正确性: X.XX/6.25
**小计: X.XX/25**

## 准确之处
1. ...
2. ...

## 准确性问题
1. ...
2. ...

## 改进建议
1. ...
2. ...
"""
        
        return self.router.generate(
            prompt,
            context="你是准确性评审专家，客观严谨但不悲观",
            node_id="expert_review",
            max_tokens=32768
        )
    
    def _expert4_norm_review(self, paper):
        """专家4: 规范性审稿"""
        prompt = f"""你是一位注重细节的学术审稿专家，专注于评估论文的规范性和表达。

审稿原则：
- 保持客观、严谨、公正，但不悲观
- 给出真实的评价，不讨好作者，也不过度批评
- 既要指出不规范之处，也要认可规范的部分
- **特别注意**：本文为【纯理论研究】，请重点关注学术语言的规范性和引用的标准化。
- **绝对禁止**：
  1. **禁止建议删除任何文献引用编号**（如[1]），这是最严重的规范错误。
  2. **绝对禁止建议插入图片、图表或表格**。
  3. **结构铁律**：引言和结论严禁分小节（无标题）；正文层级严禁超过二级标题。

请审阅以下论文，从4个维度评价规范性（每项0-6.25分，总分25分）：

1. **用词规范性**：学术用词是否规范、专业？
2. **句式通顺性**：句子是否通顺、易读？
3. **标点规范性**：标点符号使用是否正确？
4. **格式一致性**：引用格式、章节编号等是否一致？

论文内容：
{paper}

请按以下格式输出（严格遵守格式）：

## 规范性评分
用词规范性: X.XX/6.25
句式通顺性: X.XX/6.25
标点规范性: X.XX/6.25
格式一致性: X.XX/6.25
**小计: X.XX/25**

## 规范之处
1. ...
2. ...

## 规范性问题
1. ...
2. ...

## 改进建议
1. ...
2. ...
"""
        
        return self.router.generate(
            prompt,
            context="你是规范性评审专家，客观严谨但不悲观",
            node_id="expert_review",
            max_tokens=32768
        )
    
    def _expert5_integrate_feedback(self, expert1, expert2, expert3, expert4):
        """专家5: 整合意见并给出综合评分（0-100分）"""
        prompt = f"""你是一位经验丰富的主编，负责整合多位审稿专家的意见并给出客观的综合评分。

评分原则：
- 保持客观、公正，不偏不倚
- 不讨好作者，给出真实评价
- 综合评分要准确反映论文质量
- **特别注意**：本文为【纯理论研究】，**必须剔除**所有关于“量化分析”、“实证数据”、“案例研究”等建议。
- **过滤红线**：
  1. **直接剔除**所有“建议删除引用编号”的谬误意见。
  2. **直接剔除**所有“建议插入图片/图表/表格”的意见。本学科不使用任何图表。
  3. **严格结构**：确保修改建议不违反“引言/结论无标题、正文限二级标题”的规则。

以下是4位审稿专家的评审意见：

### 专家1（创新点，满分25）：
{expert1}

### 专家2（逻辑性，满分25）：
{expert2}

### 专家3（准确性，满分25）：
{expert3}

### 专家4（规范性，满分25）：
{expert4}

请整合以上意见，按优先级生成统一的修改方案。

输出格式（严格遵守）：

## 综合评分
创新点得分: X.XX/25
逻辑性得分: X.XX/25
准确性得分: X.XX/25
规范性得分: X.XX/25
**综合评分: X.XX/100**

## 总体评价
（客观评价论文的整体质量水平）

## 必须修改的关键问题（优先级1）
1. ...
2. ...

## 建议改进的重要问题（优先级2）
1. ...
2. ...

## 可选优化的细节问题（优先级3）
1. ...
2. ...
"""
        
        return self.router.generate(
            prompt,
            context="你是总编辑，负责整合审稿意见并给出客观评分",
            node_id="expert_review",
            max_tokens=32768
        )
    
    def _task_decomposer(self, paper, integrated_feedback):
        """
        AI任务拆解器（纯AI对AI交流版）
        
        核心设计：
        - 不要求精确段落索引，只输出文本描述的任务
        - 由修改AI自己在全文中定位要修改的位置
        """
        prompt = f"""你是一位专业的论文修改任务规划专家。

【任务】根据专家审稿意见，梳理出需要修改的具体任务。

【审稿意见】
{integrated_feedback}

【输出要求】
请输出3-6个修改任务，每个任务包含：
1. 问题描述：专家指出的具体问题
2. 修改要求：具体的操作指导
3. 定位线索：帮助找到需要修改内容的关键词或特征

【输出格式】每行一个任务，用"|"分隔三部分：
问题描述|修改要求|定位线索

【示例】
概念界定模糊|明确'生态基因'的内涵与外延，增加学术化定义|生态基因、定义、概念
论证深度不足|强化理论分析，增加逻辑递进，补充学理阐释|论证、分析不足
衔接不够顺畅|加强段落之间的过渡，使用承上启下的句式|衔接、过渡

【禁止事项】
- 禁止建议添加图表、删除引用
- 禁止建议补充案例数据或实证分析
- 只输出任务列表，不要其他内容
"""
        
        response = self.router.generate(
            prompt,
            context="你是任务规划专家，输出清晰的修改任务列表",
            node_id="expert_review",
            max_tokens=2048
        )
        
        # 解析文本格式的任务
        tasks = []
        for line in response.strip().split('\n'):
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('【'):
                continue
            
            parts = line.split('|')
            if len(parts) >= 2:
                tasks.append({
                    'task_id': len(tasks) + 1,
                    'problem': parts[0].strip(),
                    'requirement': parts[1].strip(),
                    'keywords': parts[2].strip() if len(parts) > 2 else ''
                })
                logger.info(f"  任务{len(tasks)}: {parts[0].strip()[:40]}...")
        
        if not tasks:
            logger.warning("任务解析为空，创建通用优化任务")
            tasks.append({
                'task_id': 1,
                'problem': '整体论证需要加强',
                'requirement': '根据审稿意见优化正文内容',
                'keywords': ''
            })
        
        logger.info(f"拆解出 {len(tasks)} 个修改任务")
        return tasks
    
    def _parse_tasks_with_regex(self, response, paragraphs, feedback):
        """正则备用解析（用于JSON解析失败时）"""
        tasks = []
        # 尝试匹配 "段落X|原因|要求" 格式
        for line in response.strip().split('\n'):
            line = line.strip()
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 3:
                    idx_match = re.search(r'\d+', parts[0])
                    if idx_match:
                        idx = int(idx_match.group())
                        if 0 <= idx < len(paragraphs):
                            tasks.append({
                                'task_id': len(tasks) + 1,
                                'location': paragraphs[idx]['location'],
                                'first_sentence': paragraphs[idx]['preview'][:50],
                                'paragraph_index': idx,
                                'full_text': paragraphs[idx]['full_text'],
                                'criticism': parts[1].strip(),
                                'requirements': parts[2].strip(),
                                'hints': ''
                            })
        return tasks
    
    def _extract_tasks_from_feedback(self, feedback, paragraphs):
        """从审稿意见中直接提取任务（最终备用）"""
        tasks = []
        
        # 用AI再次尝试提取
        prompt = f"""请从以下审稿意见中提取3个最重要的修改任务。

【审稿意见】
{feedback[:3000]}

【要求】每行输出一个任务，格式：
任务描述|修改要求

只输出任务，不要其他内容。"""

        try:
            response = self.router.generate(
                prompt,
                context="提取修改任务",
                node_id="expert_review",
                max_tokens=1024
            )
            
            for line in response.strip().split('\n'):
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 2:
                        # 尝试关键词匹配段落
                        keywords = re.findall(r'[\u4e00-\u9fa5]{3,6}', parts[0])
                        matched_para = None
                        for p in paragraphs:
                            if any(k in p['full_text'] for k in keywords[:3]):
                                matched_para = p
                                break
                        
                        if matched_para:
                            tasks.append({
                                'task_id': len(tasks) + 1,
                                'location': matched_para['location'],
                                'first_sentence': matched_para['preview'][:50],
                                'paragraph_index': matched_para['idx'],
                                'full_text': matched_para['full_text'],
                                'criticism': parts[0].strip()[:100],
                                'requirements': parts[1].strip(),
                                'hints': ''
                            })
                        
                        if len(tasks) >= 3:
                            break
        except Exception as e:
            logger.error(f"任务提取失败: {e}")
        
        return tasks
    
    def _extract_paper_paragraphs(self, paper):
        """提取论文所有段落结构 - 增强版：支持多种标题格式"""
        paragraphs = []
        current_section = "摘要"
        
        # 标题识别正则 - 支持多种格式
        heading_patterns = [
            r'^##\s+(.+)',                    # Markdown: ## 标题
            r'^###\s+(.+)',                   # Markdown: ### 标题
            r'^#\s+(.+)',                     # Markdown: # 标题
            r'^[一二三四五六七八九十]+[、．.]\s*(.+)',  # 中文数字: 一、标题
            r'^（[一二三四五六七八九十]+）\s*(.+)',     # 中文括号: （一）标题
            r'^\d+[\.\、]\s*(.+)',             # 阿拉伯数字: 1. 或 1、标题
        ]
        
        for para in paper.split('\n\n'):
            para = para.strip()
            if not para:
                continue
            
            # 检查是否是标题
            is_heading = False
            for pattern in heading_patterns:
                match = re.match(pattern, para)
                if match:
                    current_section = match.group(1).strip()[:20] if match.groups() else para[:20]
                    is_heading = True
                    # 标题也加入段落列表（但会被跳过修改）
                    paragraphs.append({
                        'idx': len(paragraphs),
                        'location': current_section,
                        'preview': para[:100],
                        'full_text': para,
                        'is_heading': True
                    })
                    break
            
            if is_heading:
                continue
            
            # 跳过参考文献条目
            if para.startswith('[') and ']' in para[:20]:
                continue
            # 降低阈值：只跳过极短的段落（如单个标点）
            if len(para) < 20:
                continue
            
            paragraphs.append({
                'idx': len(paragraphs),
                'location': current_section,
                'preview': para[:100],
                'full_text': para,
                'is_heading': False
            })
        
        return paragraphs

    
    def _generate_fallback_tasks(self, feedback, paragraphs=None):
        """当AI解析失败时生成默认任务（增强版）"""
        tasks = []
        
        # [*] 尝试多种模式提取关键问题
        # 模式1: 必须修改的关键问题（优先级1）
        patterns = [
            r'必须修改.*?\n([\s\S]*?)(?=##|$)',  # 宽松版：取"必须修改"后的所有内容
            r'关键问题.*?\n([\s\S]*?)(?=##|$)',
            r'优先级1.*?\n([\s\S]*?)(?=##|优先级2|$)',
            r'建议改进.*?\n([\s\S]*?)(?=##|$)',
        ]
        
        issues = []
        for pattern in patterns:
            match = re.search(pattern, feedback, re.DOTALL)
            if match:
                content = match.group(1)
                # 提取带数字序号的条目
                found_issues = re.findall(r'\d+[\.、]\s*\*?\*?([^*\n]+)', content)
                if found_issues:
                    issues = found_issues[:3]  # 最多取3条
                    break
        
        # [*] 如果正则提取失败，生成通用默认任务
        if not issues:
            logger.warning("无法从反馈中提取具体问题，生成通用修改任务")
            issues = [
                "论述深度需要加强，建议强化理论分析和论证逻辑",
                "部分段落表达需要优化，提升学术规范性",
            ]
        
        # 生成任务
        for i, issue in enumerate(issues):
            task = {
                'task_id': i + 1,
                'location': '需手动定位',
                'first_sentence': '',
                'criticism': issue.strip()[:100],
                'requirements': '根据审稿意见进行修改优化',
                'hints': ''
            }
            
            # 尝试通过关键词匹配定位段落
            if paragraphs:
                for p in paragraphs:
                    keywords = re.findall(r'[\u4e00-\u9fa5]{2,4}', issue)
                    if any(k in p['full_text'] for k in keywords[:3]):
                        task['location'] = p['location']
                        task['first_sentence'] = p['preview'][:50]
                        task['full_text'] = p['full_text']
                        break
            
            tasks.append(task)
        
        logger.info(f"Fallback: 生成了 {len(tasks)} 个默认修改任务")
        return tasks
    
    def _execute_tasks_sequentially(self, paper, task_list):
        """
        逐条执行修改任务（Patch-Based 局部修改模式）
        
        核心逻辑：
        1. 解析论文结构，建立段落索引
        2. 根据任务定位到具体段落
        3. 只提取该段落（及少量上下文）发送给AI修改
        4. 将AI返回的新段落精准替换回原文结构
        5. 重新组装论文
        
        优势：
        - 物理隔离：未修改的段落100%保持原样（引用、标题不会丢）
        - 专注度高：AI只关注300-500字，质量更高
        - 稳定性强：杜绝了全量重写带来的结构崩坏风险
        """
        if not task_list:
            return paper
            
        logger.info("开始执行 Patch-Based 局部修改...")
        
        # 1. 解析论文结构
        # sections = [{'title': '...', 'content': '...', 'full_text': '...'}, ...]
        paragraphs = self._extract_paper_paragraphs(paper)
        if not paragraphs:
            logger.warning("论文结构解析失败，无法执行局部修改")
            return paper
            
        modified_indices = set()
        
        # 2. 逐个任务执行
        for task in task_list:
            task_id = task.get('task_id', '?')
            problem = task.get('problem', '')
            keywords = task.get('keywords', '')
            
            logger.info(f"  任务{task_id}: {problem[:30]}...")
            
            # 定位目标段落
            target_para = None
            
            # 优先使用任务中已有的location信息（如果之前匹配过）
            if 'paragraph_index' in task:
                idx = task['paragraph_index']
                if 0 <= idx < len(paragraphs):
                    target_para = paragraphs[idx]
            
            # 如果没有索引，尝试通过关键词匹配
            if not target_para and keywords:
                # 简单的关键词匹配打分
                best_score = 0
                search_keys = str(keywords).split()
                if problem:
                    search_keys.extend(problem[:10]) # 加入问题描述的前几个字作为辅助
                    
                for p in paragraphs:
                    # 跳过标题行
                    if p['full_text'].strip().startswith('#'):
                        continue
                        
                    score = 0
                    for k in search_keys:
                        if k in p['full_text']:
                            score += 1
                    
                    if score > best_score and score >= 1: # 至少匹配一个词
                        best_score = score
                        target_para = p
            
            if not target_para:
                logger.warning(f"  无法定位任务{task_id}对应的段落，跳过")
                continue
                
            if target_para['idx'] in modified_indices:
                logger.warning(f"  段落{target_para['idx']}已被修改过，跳过避免冲突")
                continue
                
            # 执行局部修改
            logger.info(f"  定位成功: [{target_para['location']}] {target_para['preview'][:30]}...")
            new_content = self._patch_modify_paragraph(target_para['full_text'], task)
            
            if new_content and new_content != target_para['full_text']:
                # 更新段落内容
                paragraphs[target_para['idx']]['full_text'] = new_content
                modified_indices.add(target_para['idx'])
                logger.info(f"  修改完成 (索引{target_para['idx']})")
        
        # 3. 重新组装论文
        logger.info(f"局部修改完成，共修改 {len(modified_indices)} 处")
        new_paper = "\n\n".join([p['full_text'] for p in paragraphs])
        
        return new_paper

    def _patch_modify_paragraph(self, original_text, task):
        """对单个段落进行微创修改"""
        problem = task.get('problem', '')
        requirement = task.get('requirement', '')
        
        # 如果段落太短（可能是标题），不修改
        if len(original_text) < 20 or original_text.startswith('#'):
            return original_text
            
        prompt = f"""你是一位专业的论文修改专家。请针对以下【特定段落】进行微调优化。
        
【待修改段落】
{original_text}

【修改依据】
指出问题：{problem}
修改要求：{requirement}

【严格约束】
1. **只修改上述段落**，不要发挥或扩写其他内容
2. **必须保留**段落中的所有引用编号（如[1][2]），一个都不能少！
3. 保持学术语气的连贯性
4. 禁止使用"首先、其次"等机械连接词
5. 修改后的长度应与原段落相当（±20%）

【输出】
直接输出修改后的段落内容，不要任何解释："""

        try:
            result = self.router.generate(
                prompt,
                context="局部段落修改专家",
                node_id="expert_review",
                max_tokens=2048  # 局部修改不需要太大的窗口
            ).strip()
            
            # 基础验证
            if not result or len(result) < 10:
                return original_text
            
            # [P2修复] 增强引用验证：提取具体编号对比
            orig_refs = set(re.findall(r'\[(\d+)\]', original_text))
            new_refs = set(re.findall(r'\[(\d+)\]', result))
            
            if orig_refs:
                lost_refs = orig_refs - new_refs
                if lost_refs:
                    logger.warning(f"  修改导致引用丢失: {lost_refs}，回退到原文")
                    return original_text
            
            # 验证长度变化不超过50%
            length_ratio = len(result) / len(original_text)
            if length_ratio < 0.5 or length_ratio > 2.0:
                logger.warning(f"  修改后长度变化过大 ({length_ratio:.1f}x)，回退到原文")
                return original_text
                
            return result
            
        except Exception as e:
            logger.error(f"  局部修改失败: {e}")
            return original_text
    
    def _rewrite_paragraph(self, paper, task, search_context=""):
        """整段重写策略（AI驱动定位版）"""
        location = task.get('location', '')
        first_sentence = task.get('first_sentence', '')
        criticism = task.get('criticism', '')
        
        paragraphs = paper.split('\n\n')
        
        # 构建段落列表供AI定位
        para_list = "\n".join([
            f"段落{idx}: {para[:100]}..."
            for idx, para in enumerate(paragraphs) if para.strip() and not para.strip().startswith('#')
        ])
        
        # [*] 用AI定位目标段落
        locate_prompt = f"""你是段落定位专家。请从以下段落列表中找出需要修改的段落编号。

【需要修改的内容描述】
位置: {location}
首句: {first_sentence[:80]}
问题: {criticism[:50]}

【论文段落列表】
{para_list}

【输出要求】
只输出一个数字（段落编号），不要其他任何内容。
如果找不到完全匹配的段落，输出最相关的段落编号。
"""
        
        try:
            response = self.router.generate(
                locate_prompt,
                context="段落定位专家，只输出数字",
                node_id="expert_review",
                max_tokens=32
            ).strip()
            
            # 提取数字
            match = re.search(r'\d+', response)
            if match:
                target_idx = int(match.group())
                if 0 <= target_idx < len(paragraphs):
                    logger.info(f"  [OK] AI定位成功，定位到段落 {target_idx}")
                else:
                    logger.warning(f"  AI返回编号{target_idx}超出范围，使用第一个正文段落")
                    target_idx = next((i for i, p in enumerate(paragraphs) if p.strip() and not p.startswith('#')), 1)
            else:
                logger.warning(f"  AI定位失败，无法解析: {response}")
                return paper
                
        except Exception as e:
            logger.error(f"  AI定位异常: {e}")
            return paper
        
        original_para = paragraphs[target_idx]
        
        # 构建重写提示
        context_info = f"\n\n参考资料：\n{search_context}" if search_context else ""
        
        prompt = f"""请重写以下段落，修复专家指出的问题。

【原段落】
{original_para}

【专家批评】
{task.get('criticism', '无具体批评')}

【修改要求】
{task.get('requirements', '优化表达')}

【重写提示】
{task.get('hints', '保持学术性')}
{context_info}

**要求**：
1. 必须保留所有文献引用[1][2]等
2. 保持原段落的核心观点
3. 输出重写后的完整段落（3-5个自然句，段内不换行）
4. 只输出段落内容，不要任何前言后语
5. 这个问题看似简单实际上非常难，请你谨慎的思考，深入的研究和搜索。让我们一步一步来，从多个角度考虑这个问题，学术化表达，逻辑严谨，层层递进，语言要平实的学术语言，不要夸张，不要自造新词，少用引号，不要创造新概念，多用学术表达，要易懂，但是用词要有专业性，整体要有较高的学术质感。禁止使用类似“首先”“其次”“再次”“最后”等机械感很强的词汇，也禁止使用“重构”“重建”“填补空白”等夸张吹嘘表达，同时更禁止随意使用引号、冒号、破折号等一看就很AI的标点符号，要自然表述，禁止任何的小标题和分点，形成段落化文本，多分几个自然段，不要出现“如何”“何以”“为何”等提问字样。字数别太多，控制篇幅
"""
        
        try:
            new_para = self.router.generate(
                prompt,
                context="段落重写专家",
                node_id="expert_review",
                max_tokens=1024
            ).strip()
            
            # 替换段落
            paragraphs[target_idx] = new_para
            logger.info(f"  [OK] 已重写段落 (原{len(original_para)}字 -> 新{len(new_para)}字)")
            
            return '\n\n'.join(paragraphs)
        except Exception as e:
            logger.error(f"  段落重写失败: {e}")
            return paper
    
    def _execute_single_task(self, paper, task, search_context=""):
        """执行单个修改任务"""
        context_prompt = ""
        if search_context:
            context_prompt = f"\n\n参考资料（来自互联网）：\n{search_context}\n"

        prompt = f"""你是一位专业的学术论文写作AI。

修改任务：
- 位置：{task.get('location', '全文')}
- 动作：{task.get('action', '修改')}
- **专家批评（核心罪名）：{task.get('criticism', '无')}**
- 详细要求：{task.get('description', '')}
- 期望结果：{task.get('expected_result', '')}
{context_prompt}
当前论文：
{paper}

请根据任务要求对论文进行修改，要求：
1. **针对专家批评进行“定向爆破”，必须彻底解决该问题，以提升评分为首要目标。**
2. **如果原段落逻辑无法修复，允许“推倒重写”该段落（但保持核心观点不变）。**
3. **最高指令：绝对禁止删除任何文献引用[1]等。即便任务要求你删除，你也必须保留！**
4. 只修改相关部分，不改动无关内容。
5. 确保修改后逻辑清晰、表达规范。
6. 这个问题看似简单实际上非常难，请你谨慎的思考，深入的研究和搜索。让我们一步一步来，从多个角度考虑这个问题，学术化表达，逻辑严谨，层层递进，语言要平实的学术语言，不要夸张，不要自造新词，少用引号，不要创造新概念，多用学术表达，要易懂，但是用词要有专业性，整体要有较高的学术质感。禁止使用类似“首先”“其次”“再次”“最后”等机械感很强的词汇，也禁止使用“重构”“重建”“填补空白”等夸张吹嘘表达，同时更禁止随意使用引号、冒号、破折号等一看就很AI的标点符号，要自然表述，禁止任何的小标题和分点，形成段落化文本，多分几个自然段，不要出现“如何”“何以”“为何”等提问字样。字数别太多，控制篇幅
输出修改后的完整论文。
"""
        
        return self.router.generate(
            prompt,
            context="请根据任务要求修改论文",
            node_id="expert_review",
            max_tokens=8192
        )
    
    def _extract_score(self, feedback):
        """从专家反馈中提取小计分数"""
        # 匹配 "小计: X.XX/25" 或 "**小计: X.XX/25**"
        match = re.search(r'小计[:：]\s*(\d+(?:\.\d+)?)/25', feedback)
        if match:
            return float(match.group(1))
        
        # 备用：匹配多个分数并求和
        scores = re.findall(r'(\d+(?:\.\d+)?)/6\.25', feedback)
        if scores:
            return sum(float(s) for s in scores)
        
        logger.warning("未能提取专家评分，默认返回0")
        return 0.0
    
    def _extract_comprehensive_score(self, integrated_feedback):
        """从整合意见中提取综合评分（0-100）"""
        # [*] 尝试多种匹配模式（优化版）
        
        # 模式1: 带星号格式 "**综合评分: X.XX/100**" 或 "**综合评分：X/100**"
        match = re.search(r'\*?\*?综合评分[:：]\s*\*?\*?\s*(\d+(?:\.\d+)?)/100', integrated_feedback)
        if match:
            score = float(match.group(1))
            logger.info(f"  评分提取成功(模式1): {score}/100")
            return score
        
        # 模式2: 纯数字格式 "综合评分: 75" 或 "综合评分：75分"
        match = re.search(r'综合评分[:：]\s*(\d+(?:\.\d+)?)(?:分|/100)?', integrated_feedback)
        if match:
            score = float(match.group(1))
            if score <= 100:  # 确保是百分制
                logger.info(f"  评分提取成功(模式2): {score}/100")
                return score
        
        # 模式3: 带计算公式 "综合评分: (计算公式) = X.XX" 或 "≈ X"
        match = re.search(r'综合评分[:：].*?[=≈]\s*(\d+(?:\.\d+)?)', integrated_feedback)
        if match:
            score = float(match.group(1))
            logger.info(f"  评分提取成功(模式3): {score}/100")
            return score
        
        # 模式4: 总分格式 "总分: X/100"
        match = re.search(r'总分[:：]\s*(\d+(?:\.\d+)?)/100', integrated_feedback)
        if match:
            score = float(match.group(1))
            logger.info(f"  评分提取成功(模式4-总分): {score}/100")
            return score
        
        # 模式5: 备用 - 直接查找0-100范围的分数（取最后一个）
        matches = re.findall(r'(\d{1,3}(?:\.\d+)?)/100', integrated_feedback)
        if matches:
            score = float(matches[-1])
            logger.info(f"  评分提取成功(模式5-末尾匹配): {score}/100")
            return score
        
        logger.warning("未能直接提取综合评分，尝试从专家分数求和...")
        
        # 模式6: 从各维度得分求和
        dimension_scores = re.findall(r'(?:创新点|逻辑性|准确性|规范性)得分[:：]\s*(\d+(?:\.\d+)?)/25', integrated_feedback)
        if len(dimension_scores) == 4:
            total = sum(float(s) for s in dimension_scores)
            logger.info(f"  从维度得分求和: {total}/100")
            return total
        
        # 模式7: 从四位专家小计求和（最终备用）
        expert_scores = re.findall(r'小计[:：]\s*(\d+(?:\.\d+)?)/25', integrated_feedback)
        if len(expert_scores) >= 4:
            total = sum(float(s) for s in expert_scores[:4])
            logger.info(f"  从专家小计求和: {total}/100")
            return total
        
        logger.warning("所有评分提取模式均失败，默认返回60分（避免过低导致无限循环）")
        return 60.0  # [*] 返回60而非0，避免触发无限优化循环
