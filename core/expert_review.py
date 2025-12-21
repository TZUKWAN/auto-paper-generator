"""5专家AI审稿系统（优化版：客观评分+任务拆解+循环优化）"""
import logging
import re
import json

logger = logging.getLogger(__name__)

class ExpertReviewSystem:
    """专家审稿系统（含循环优化机制）"""
    
    def __init__(self, model_router, output_dir=None, external_search=None):
        """
        初始化专家审稿系统
        
        Args:
            model_router: 大模型路由器
            output_dir: 中间结果保存目录（可选）
            external_search: 外部搜索引擎集成（可选）
        """
        self.router = model_router
        self.output_dir = output_dir
        self.external_search = external_search
        self.max_rounds = 3  # 最多优化3轮
        self.target_score = 90  # 目标综合评分
        logger.info("专家审稿系统初始化完成（目标评分≥90分）")
    
    def review_and_optimize_iteratively(self, paper_content):
        """
        迭代审稿和优化流程（直到≥90分或达到最大轮次）
        
        Args:
            paper_content: 论文初稿内容
            
        Returns:
            {
                'final_paper': str,  # 最终优化后论文
                'rounds': int,  # 优化轮次
                'final_score': float,  # 最终综合评分
                'all_reviews': [...]  # 所有轮次的审稿记录
            }
        """
        logger.info("="*60)
        logger.info("开始迭代审稿优化流程")
        logger.info("="*60)
        
        current_paper = paper_content
        all_reviews = []
        
        for round_num in range(1, self.max_rounds + 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"第 {round_num}/{self.max_rounds} 轮审稿")
            logger.info(f"{'='*60}")
            
            # 执行一轮完整审稿
            review_result = self._single_round_review_and_optimize(current_paper, round_num)
            
            all_reviews.append(review_result)
            current_paper = review_result['optimized_paper']
            final_score = review_result['综合评分']
            
            logger.info(f"第{round_num}轮综合评分: {final_score}/100")
            
            # 判断是否达标
            if final_score >= self.target_score:
                logger.info(f"✓ 综合评分已达{final_score}分（≥{self.target_score}），停止优化")
                break
            else:
                logger.info(f"未达标（需≥{self.target_score}分），继续下一轮优化...")
            
            # ⭐ 实时保存本轮结果
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
        logger.info(f"审稿优化流程完成！共{round_num}轮，最终评分{final_score}/100")
        logger.info("="*60)
        
        return {
            'final_paper': current_paper,
            'rounds': round_num,
            'final_score': final_score,
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
        logger.info(f"  ✓ 专家1（创新点）: {expert1_score}/25")
        
        expert2_feedback = self._expert2_logic_review(paper)
        expert2_score = self._extract_score(expert2_feedback)
        logger.info(f"  ✓ 专家2（逻辑性）: {expert2_score}/25")
        
        expert3_feedback = self._expert3_accuracy_review(paper)
        expert3_score = self._extract_score(expert3_feedback)
        logger.info(f"  ✓ 专家3（准确性）: {expert3_score}/25")
        
        expert4_feedback = self._expert4_norm_review(paper)
        expert4_score = self._extract_score(expert4_feedback)
        logger.info(f"  ✓ 专家4（规范性）: {expert4_score}/25")
        
        # 阶段2: 整合意见并计算综合评分
        logger.info(f"\n阶段2: 专家5整合意见并评分...")
        integrated_result = self._expert5_integrate_feedback(
            expert1_feedback, expert2_feedback, 
            expert3_feedback, expert4_feedback
        )
        
        comprehensive_score = self._extract_comprehensive_score(integrated_result)
        logger.info(f"  ✓ 综合评分: {comprehensive_score}/100")
        
        # 阶段3: 中间层AI拆解任务
        logger.info(f"\n阶段3: 中间层AI拆解修改任务...")
        task_list = self._task_decomposer(paper, integrated_result)
        logger.info(f"  ✓ 拆解出 {len(task_list)} 个修改任务")
        
        # 阶段4: 写作AI逐条执行任务
        logger.info(f"\n阶段4: 写作AI逐条执行修改...")
        optimized_paper = self._execute_tasks_sequentially(paper, task_list)
        logger.info(f"  ✓ 所有任务执行完成")
        
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
        中间层AI：任务拆解器
        
        根据综合审稿意见，拆解为具体的修改任务
        """
        prompt = f"""你是一位论文修改任务规划专家。

你的任务：根据审稿意见，拆解为具体的、可执行的修改任务列表。

审稿意见：
{integrated_feedback}

论文当前内容：
{paper}

请将修改意见拆解为具体任务，每个任务应：
1. 明确指出修改位置（章节、段落）
2. 清晰说明修改内容
3. **引用专家原始批评（criticism）**：必须指出是哪位专家的哪个具体批评导致了该任务
4. 给出具体要求
5. **安全检查**：
   - 绝对不允许生成“删除引用”、“去掉角标”的任务。
   - **绝对不允许生成“制作表格”、“绘制图表”、“添加图示”的任务**。
   - **绝对不允许生成“补充案例选择标准”、“描述数据来源”、“详解分析步骤”的任务**（这属于实证研究误区）。如果是此类建议，请转化为“深化理论阐述”。

输出格式（严格JSON数组）：

输出格式（严格JSON数组）：
[
  {{
    "task_id": 1,
    "priority": "高/中/低",
    "location": "章节/段落位置",
    "action": "添加/删除/修改/优化",
    "criticism": "专家指出的具体问题/低分原因",
    "description": "具体修改要求",
    "expected_result": "期望达到的效果"
  }},
  ...
]

只输出JSON数组，不要其他内容。
"""
        
        response = self.router.generate(
            prompt,
            context="你是任务拆解专家",
            node_id="expert_review",
            max_tokens=32768
        )
        
        # 解析JSON
        try:
            # 提取JSON部分
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                task_list = json.loads(json_match.group())
                return task_list
            else:
                logger.warning("未能解析任务列表，使用空列表")
                return []
        except Exception as e:
            logger.error(f"任务列表解析失败: {e}")
            return []
    
    def _execute_tasks_sequentially(self, paper, task_list):
        """
        写作AI逐条执行修改任务
        
        Args:
            paper: 当前论文
            task_list: 任务列表
            
        Returns:
            优化后的论文
        """
        current_paper = paper
        
        for task in task_list:
            logger.info(f"  执行任务{task.get('task_id')}: {task.get('description', '')[:50]}...")
            
            logger.info(f"  执行任务{task.get('task_id')}: {task.get('description', '')[:50]}...")
            logger.info(f"  (系统提示：正在对全文进行定向修改，本地模型处理约需 3-5 分钟，请耐心等待...)")
            
            # 调用写作AI执行单个任务
            current_paper = self._execute_single_task(current_paper, task)
        
        return current_paper
    
        if self.external_search and task.get('action') in ['添加', '修改', '优化']:
             # 提取搜索关键词（简单策略：直接搜索任务描述，或者让LLM提取）
             # 这里为了效率，直接使用任务描述的前50个字作为查询
             search_query = task.get('description', '')[:50]
             logger.info(f"  [联网] 正在检索资料协助修改: {search_query}...")
             search_results = self.external_search.search(search_query)
        else:
             search_results = ""
             
        current_paper = self._execute_single_task(current_paper, task, search_results)
        
        return current_paper
    
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
        # 匹配 "综合评分: X.XX/100" 或 "**综合评分: X.XX/100**"
        match = re.search(r'综合评分[:：]\s*(\d+(?:\.\d+)?)/100', integrated_feedback)
        if match:
            return float(match.group(1))
        
        logger.warning("未能提取综合评分，默认返回0")
        return 0.0
