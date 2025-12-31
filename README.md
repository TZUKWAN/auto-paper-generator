# 自动化论文生成系统（纯线上版）

## 项目简介

这是一个**模板驱动的哲学社科理论论文自动写作流水线**。系统通过智能文献管理、高密度引用策略，实现从配置到初稿的全自动化生成。

**纯线上版本**：完全依赖在线大模型API，无需配置本地模型。

## 核心特性

- **理论论文模板**：专注于理论研究的论文生成
- **在线大模型路由**：支持硅基流动、智谱AI、通义千问等多个API
- **智能文献管理**：TXT文献池解析、FAISS语义检索、严格去重
- **高密度引用**：不重复引用 + 尽可能多引用策略
- **外部检索补充**：SearXNG本地搜索 / 智谱AI搜索
- **动态章节处理**：AI设计框架后分别展开详细内容
- **质量审计**：引用密度、达标情况、文献余额统计
- **5专家AI审稿**：创新/逻辑/准确/规范/整合，≥90分停止优化
- **项目级文献池**：每个论文独立管理文献和PDF

## 技术栈

- **Python 3.8+**
- **在线大模型**：硅基流动API（默认）、智谱AI、通义千问等
- **语义检索**：Sentence-Transformers + FAISS
- **文档处理**：python-docx

## 项目结构

```
自动化论文脚本/
├── config.yaml                  # 主配置文件
├── templates/                   # 模板库
│   └── theoretical_paper.yaml   # 理论论文模板
├── data/                        # 数据目录
│   └── projects/                # 项目文件夹（每个论文独立）
│       └── 20251220_项目名/
│           ├── literature/      # 文献池
│           ├── pdfs/            # PDF参考文档
│           └── output/          # 输出文件
├── core/                        # 核心模块
│   ├── template_engine.py       # 模板引擎
│   ├── model_router.py          # 大模型路由
│   ├── literature_parser.py     # 文献解析器
│   ├── semantic_retriever.py    # 语义检索
│   ├── citation_manager.py      # 引用管理器
│   ├── expert_review.py         # 5专家审稿系统
│   ├── pdf_reference.py         # PDF参考管理
│   └── project_manager.py       # 项目管理器
├── main.py                      # 主程序
└── requirements.txt             # 依赖包
```

## 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置API密钥

编辑 `config.yaml`，配置在线API密钥：

```yaml
model_routing:
  default_provider: siliconflow
  providers:
    siliconflow:
      enabled: true
      api_key: "你的API密钥"
      base_url: "https://api.siliconflow.cn/v1"
```

支持的API提供商：
- 硅基流动（默认）
- 智谱AI
- 通义千问
- DeepSeek
- OpenAI

### 3. 准备文献池

创建 TXT 文件，格式如下：

```
[1]作者1, 作者2. 文章标题[J]. 期刊名, 年份, (卷期): 页码. 摘要:这里是摘要内容...
[2]作者3. 另一篇文章[J]. 期刊名2, 年份, (卷期): 页码. 摘要:这里是摘要...
```

建议准备100+条文献以获得更好的效果。

### 4. 配置项目

编辑 `config.yaml`：

```yaml
project:
  title: "红色文化中的生态基因传承与中国式现代化生态观建构研究"
  keywords: "红色文化, 生态基因, 中国式现代化, 生态观, 传承与建构"
```

### 5. 运行生成

```bash
python main.py \
  --project "红色文化中的生态基因传承与中国式现代化生态观建构研究" \
  --literature "data/literature_pool.txt"
```

## 输出说明

系统会生成三个版本的论文：

1. **V1初稿版**：经过专家审稿的基础版本
2. **V2标准版**：清理AI痕迹、规范正文
3. **V3扩写版**：内容丰富化、更加详细

每个版本都会导出 Markdown 和 Word 两种格式。

## 高级特性

### 动态章节处理

论文模板支持动态章节展开：

**示例：研究维度动态展开**
```yaml
sections:
  - id: "research_dimensions_overview"
    prompt: "请提出本研究的4个核心研究维度"
    dynamic: true
    expand_count: 4

  - id: "dimension_detail_template"
    prompt: "详细阐述该研究维度的理论基础、关键问题和文献支撑"
    is_template: true
```

系统会：
1. 第一轮：调用AI获取4个研究维度
2. 第二轮：为每个维度生成详细内容
3. 自动为每个维度高密度引用相关文献

### 引用策略配置

```yaml
citation:
  target_per_sentence: 2-4       # 每句目标引用数
  min_per_paragraph: 3           # 每段最低引用数
  similarity_threshold: 0.6      # 相关性阈值
  diversity_weight: 0.3          # 多样性权重（作者/年份分散）
```

### 外部检索补充

当文献池不足时自动触发：

```yaml
external_search:
  enabled: true
  mode: "deep"
  results_per_query: 10
```

### 5专家审稿系统

系统会自动进行多轮审稿优化：

- 专家1：创新点评估
- 专家2：逻辑性评估
- 专家3：准确性评估
- 专家4：规范性评估
- 专家5：整合建议

直到综合评分达到目标分数（默认90分）或达到最大轮次。

## 质量报告

生成完成后，系统会输出 `quality_report.json`：

```json
{
  "total_citations": 156,
  "citations_per_paragraph": 4.2,
  "citations_per_sentence": 2.1,
  "target_met": true,
  "unused_literature_count": 23,
  "word_count_v1": 15000,
  "word_count_v2": 18000,
  "word_count_v3": 25000
}
```

## 许可证

仅供学习研究使用

## 联系方式

如有问题请提Issue
