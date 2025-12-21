# 自动化论文生成系统

## 项目简介

这是一个**模板驱动的哲学社科论文自动写作流水线**，支持理论论文和实证论文两种模式。系统通过智能文献管理、高密度引用策略和可扩展的分析插件，实现从配置到初稿的全自动化生成。

## 核心特性

- ✅ **双模板系统**：理论论文模板 + 实证论文模板
- ✅ **混合大模型路由**：本地LM Studio + 在线硅基流动API
- ✅ **智能文献管理**：TXT文献池解析、FAISS语义检索、严格去重
- ✅ **高密度引用**：不重复引用 + 尽可能多引用策略
- ✅ **外部检索补充**：SearXNG本地搜索 / 智谱AI搜索
- ✅ **实证分析自动化**：可扩展插件系统（描述统计、回归、稳健性等）
- ✅ **动态章节处理**：AI设计框架后分别展开详细内容
- ✅ **质量审计**：引用密度、达标情况、文献余额统计
- ⭐ **5专家AI审稿**：创新/逻辑/准确/规范/整合，≥90分停止优化
- ⭐ **项目级文献池**：每个论文独立管理文献和PDF

## 技术栈

- **Python 3.8+**
- **本地大模型**：LM Studio（OpenAI兼容API）
- **在线大模型**：硅基流动API
- **语义检索**：Sentence-Transformers + FAISS
- **数据分析**：Pandas, Statsmodels, Matplotlib
- **文档处理**：python-docx

## 项目结构

```
自动化论文脚本/
├── config.yaml                  # 主配置文件
├── templates/                   # 模板库
│   ├── theoretical_paper.yaml   # 理论论文模板
│   └── empirical_paper.yaml     # 实证论文模板
├── data/                        # 数据目录
│   └── projects/                # 项目文件夹（每个论文独立）
│       └── 20251220_项目名/
│           ├── literature/      # 文献池
│           ├── pdfs/            # PDF参考文档
│           └── output/          # 输出文件
├── core/                        # 核心模块
│   ├── template_engine.py       # 模板引擎
│   ├── model_router.py          # 大模型路由（LM Studio + 硅基流动）
│   ├── literature_parser.py     # 文献解析器
│   ├── semantic_retriever.py    # 语义检索
│   ├── citation_manager.py      # 引用管理器
│   ├── expert_review.py         # 5专家审稿系统
│   ├── pdf_reference.py         # PDF参考管理
│   └── project_manager.py       # 项目管理器
├── main.py                      # 主程序
├── web_api.py                   # Web API服务器
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

### 2. 配置LM Studio本地模型

1. 下载并安装 [LM Studio](https://lmstudio.ai/)
2. 在LM Studio中下载模型（推荐：Qwen2.5-7B-Instruct或类似模型）
3. 启动本地服务器（默认端口1234）
4. 确保服务运行在 `http://localhost:1234`

### 3. 准备文献池

在前端上传或直接创建 TXT 文件，格式：
```
[1]作者1, 作者2. 文章标题[J]. 期刊名, 年份, (卷期): 页码. 摘要:这里是摘要内容...
[2]作者3. 另一篇文章[J]. 期刊名2, 年份, (卷期): 页码. 摘要:这里是摘要...
```

### 4. 配置项目

编辑 `config.yaml`：
```yaml
project:
  title: "人工智能伦理问题研究"
  keywords: "人工智能, 伦理, 算法偏见"

model_routing:
  default: "lmstudio"
  lmstudio:
    base_url: "http://localhost:1234/v1"
    model: "local-model"
```

### 5. 运行生成

```bash
# 命令行模式
python main.py \
  --project "AI伦理研究" \
  --literature "path/to/literature.txt"

# 或启动Web API
python web_api.py
```

## 使用说明

### 理论论文模式

1. 选择理论论文模板
2. 配置研究主题和关键词
3. 准备文献池（建议100+条）
4. 系统自动生成包含高密度引用的论文初稿

### 实证论文模式

1. 选择实证论文模板
2. 准备原始数据（CSV/Excel）
3. 配置分析计划（选择插件）
4. 系统自动完成数据分析并生成论文

## 高级特性

### 动态章节处理

类似商业计划书的产品功能模块，论文模板也支持动态章节：

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
  mode: "searxng"  # 或 "zhipu"
  trigger_threshold: 0.8
```

## 质量报告

生成完成后，系统会输出 `quality_report.json`：
```json
{
  "total_citations": 156,
  "citations_per_paragraph": 4.2,
  "citations_per_sentence": 2.1,
  "target_met": true,
  "unused_literature_count": 23,
  "external_search_triggered": false,
  "threshold_rejections": 12
}
```

## 开发计划

- [x] 项目架构设计
- [x] 核心模块实现
- [x] 模板系统
- [x] 混合模型路由 (SiliconFlow/RedPlan)
- [x] 核心算法优化 (Expert Review)
- [x] Web界面 (Modern UI + Dual Download)
- [ ] 实证分析插件
- [ ] 协同编辑

## 许可证
仅供学习研究使用

## 联系方式
如有问题请提Issue
