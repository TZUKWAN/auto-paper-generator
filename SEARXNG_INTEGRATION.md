# SearXNG联网检索集成说明

## ✅ 已完成的功能

系统**已支持**SearXNG联网检索，且配置为**至少30条搜索结果**。

---

## 🌐 核心特性

### 1. 自动联网检索
- 在生成每个段落时，自动使用SearXNG搜索相关内容
- **默认返回30条搜索结果**（可配置）
- 搜索结果作为上下文提供给AI，增强内容质量

### 2. 智能内容增强
生成流程：
```
论文主题 → SearXNG搜索（30条） → PDF参考 → 文献池检索 → AI生成段落
```

### 3. 多源信息融合
每个段落生成时自动融合：
- ✅ **SearXNG联网搜索**（30条最新信息）
- ✅ **PDF参考文档**（用户上传）
- ✅ **文献池**（学术文献）

---

## ⚙️ 配置

### config.yaml 配置

```yaml
literature:
  external_search:
    enabled: true  # 启用外部检索
    mode: "searxng"  # 使用SearXNG
    searxng_url: "http://localhost:8080"  # SearXNG服务地址
    results_per_query: 30  # 每次搜索返回30条结果
```

### 启动SearXNG服务

#### Docker方式（推荐）

```bash
# 拉取SearXNG镜像
docker pull searxng/searxng:latest

# 启动服务（端口8080）
docker run -d \
  -p 8080:8080 \
  --name searxng \
  searxng/searxng:latest
```

#### 验证服务

```bash
# 访问SearXNG
http://localhost:8080

# 测试API
curl "http://localhost:8080/search?q=人工智能伦理&format=json"
```

---

## 📊 使用示例

### 自动模式（默认）

系统会自动在以下情况使用SearXNG：

1. **生成引言时**
   - 搜索研究背景和现状
   - 获取最新研究动态
   - 30条搜索结果 → AI综合分析

2. **生成主体内容时**
   - 搜索相关理论和观点
   - 补充学术文献池
   - 确保内容时效性

3. **生成结论时**
   - 搜索最新发展趋势
   - 参考前沿研究

### 手动触发（Web API）

```python
from core.external_search import SearXNGSearcher

# 创建搜索器
searcher = SearXNGSearcher(
    searxng_url="http://localhost:8080",
    results_per_query=30  # 30条结果
)

# 搜索
results = searcher.search("人工智能伦理")

# 格式化为AI可读文本
formatted = searcher.format_results_for_llm(results)
print(formatted)
```

### 输出示例

```
【联网检索结果】

1. 人工智能伦理问题研究综述
   近年来，随着人工智能技术的快速发展，其伦理问题日益凸显。主要包括算法偏见、隐私保护、责任归属等方面...
   来源: https://example.com/ai-ethics

2. AI算法偏见的社会影响
   算法偏见是人工智能领域最受关注的伦理问题之一。研究发现，机器学习模型可能继承和放大训练数据中的偏见...
   来源: https://example.com/algorithm-bias

... (共30条)
```

---

## 🔧 高级配置

### 调整搜索结果数量

```yaml
external_search:
  results_per_query: 50  # 改为50条
```

### 多查询批量搜索

```python
searcher = SearXNGSearcher("http://localhost:8080", 30)

# 批量多个查询
queries = ["AI伦理", "算法偏见", "隐私保护"]
all_results = searcher.search_multiple_queries(queries, num_results_per_query=10)
# 自动去重，每个查询10条，总共最多30条
```

### 自定义搜索语言

编辑SearXNG配置或在请求中指定：

```python
params = {
    'q': query,
    'format': 'json',
    'language': 'en'  # 英文搜索
}
```

---

## 📈 性能优化

### 缓存策略

系统会自动缓存搜索结果（基于查询词）：
- 相同查询24小时内不重复搜索
- 减少API调用次数
- 提升生成速度

### 超时设置

```python
# 默认30秒超时
response = requests.get(search_url, params=params, timeout=30)
```

### 并发控制

- 每次生成限制并发搜索数
- 避免过载SearXNG服务
- 建议配置：每秒最多2次搜索

---

## 🛠️ 故障排查

### 问题1: SearXNG无法访问

**解决方案**：
```bash
# 检查Docker容器状态
docker ps | grep searxng

# 重启容器
docker restart searxng

# 查看日志
docker logs searxng
```

### 问题2: 搜索结果为空

**原因**：
- SearXNG服务未配置搜索引擎
- 网络连接问题
- 查询词过于特殊

**解决方案**：
1. 访问 `http://localhost:8080` 检查设置
2. 在SearXNG管理界面启用更多搜索引擎
3. 测试基础查询词

### 问题3: 搜索速度慢

**优化建议**：
- 减少 `results_per_query` 数量
- 在SearXNG中禁用慢速搜索引擎
- 使用本地缓存

---

## 📋 完整工作流

```
1. 用户启动论文生成
2. 系统读取配置（SearXNG enabled=true, 30条搜索）
3. 对于每个段落：
   a. 提取主题关键词
   b. 调用SearXNG搜索（30条结果）
   c. 格式化搜索结果
   d. 合并PDF参考内容
   e. 提供给AI作为上下文
   f. AI生成高质量段落
4. 输出最终论文
```

---

## ✅ 验证检查清单

- [ ] Docker中运行SearXNG服务
- [ ] 访问 http://localhost:8080 确认可用
- [ ] config.yaml中 `enabled: true`
- [ ] `results_per_query: 30` 已配置
- [ ] 运行 `python main.py` 查看日志确认搜索成功

---

**状态**: ✅ SearXNG联网检索已集成，默认30条搜索结果
**更新时间**: 2025-12-20 19:30
