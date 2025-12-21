# 自动化论文生成系统测试脚本

## 前置准备

1. **启动Ollama本地模型**：
```bash
ollama serve
# 确保qwen3:8b模型已下载
ollama pull qwen3:8b
```

2. **安装依赖**：
```bash
pip install -r requirements.txt
```

3. **配置环境变量**（可选）：
```bash
# 复制示例文件
copy .env.example .env

# 编辑.env，填入API密钥（如果使用在线模型）
```

## 快速测试

### 测试1: 文献池解析
```bash
python -c "from core.literature_parser import LiteratureParser; p = LiteratureParser(); lit = p.parse_txt_pool('data/literature_pool.txt'); print(f'解析成功: {len(lit)} 条文献')"
```

### 测试2: 语义检索
```bash
python -c "from core.literature_parser import LiteratureParser; from core.semantic_retriever import SemanticRetriever; p = LiteratureParser(); pool = p.parse_txt_pool('data/literature_pool.txt'); r = SemanticRetriever(pool); results = r.search('马克思主义哲学', top_k=2); print(f'检索到 {len(results)} 条相关文献')"
```

### 测试3: 生成完整论文
```bash
python main.py
```

## 检查输出

- 论文文件：`output/论文初稿.docx`
- 质量报告：`output/quality_report.json`
- 日志文件：`logs/generation_YYYYMMDD_HHMMSS.log`

## 自定义配置

编辑 `config.yaml` 修改：
- 论文题目和关键词
- 模型路由规则
- 引用密度参数
- 输出格式

## 常见问题

**Q: Ollama连接失败？**
A: 确保Ollama服务已启动，默认端口11434

**Q: FAISS索引构建慢？**
A: 正常现象，取决于文献数量，首次运行会慢一些

**Q: 引用数量不足？**
A: 增加文献池数量或降低 `citation.similarity_threshold`

**Q: 想使用在线模型？**
 A: 在config.yaml中设置 `model_routing.default: "silicon"` 并配置API密钥
