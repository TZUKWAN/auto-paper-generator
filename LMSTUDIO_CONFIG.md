# LM Studio配置说明

## 🎯 为什么选择LM Studio？

相比Ollama，LM Studio有以下优势：
- ✅ **更好的性能释放**：GPU利用率更高
- ✅ **OpenAI兼容API**：标准化接口，易于集成
- ✅ **图形界面**：可视化管理模型和配置
- ✅ **灵活的参数调整**：实时调整温度、top-p等参数
- ✅ **更稳定的推理**：资源管理更优秀

---

## 📥 安装和配置

### 1. 下载LM Studio

访问 [https://lmstudio.ai/](https://lmstudio.ai/) 下载对应系统的版本。

### 2. 下载模型

在LM Studio中搜索并下载模型，推荐：
- **Qwen2.5-7B-Instruct-GGUF**（中文性能优秀）
- **Llama-3.1-8B-Instruct-GGUF**（英文性能优秀）
- **Mistral-7B-Instruct-GGUF**（平衡选择）

### 3. 启动本地服务器

1. 在LM Studio中点击"Local Server"标签
2. 选择已下载的模型
3. 点击"Start Server"
4. 默认运行在 `http://localhost:1234`

---

## ⚙️ 系统配置

### config.yaml 配置

```yaml
model_routing:
  default: "lmstudio"
  
  lmstudio:
    base_url: "http://localhost:1234/v1"
    model: "local-model"  # 可以是任意名称，LM Studio会使用当前加载的模型
  
  silicon:
    api_key: "your_api_key_here"
    model: "Qwen/Qwen2.5-72B-Instruct"
  
  routing_rules:
    local_nodes:
      - "main_body"
      - "literature_review"
    online_nodes:
      - "introduction"
      - "conclusion"
      - "abstract"
      - "expert_review"
```

---

## 🔧 API调用示例

### 直接测试LM Studio API

```bash
curl http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local-model",
    "messages": [
      {"role": "system", "content": "你是一位学术写作专家"},
      {"role": "user", "content": "请简要介绍人工智能伦理"}
    ],
    "temperature": 0.7,
    "max_tokens": 500
  }'
```

### Python调用示例

```python
import requests

response = requests.post(
    "http://localhost:1234/v1/chat/completions",
    json={
        "model": "local-model",
        "messages": [
            {"role": "system", "content": "你是一位学术写作专家"},
            {"role": "user", "content": "请简要介绍人工智能伦理"}
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }
)

result = response.json()
print(result['choices'][0]['message']['content'])
```

---

## 🎛️ 性能优化建议

### 1. GPU设置
- 确保LM Studio使用GPU加速
- 在设置中查看GPU利用率
- 根据显存大小选择模型量化版本（Q4/Q5/Q8）

### 2. 上下文长度
- 根据显存调整上下文窗口大小
- 建议：8GB显存 → 4096 tokens，16GB显存 → 8192 tokens

### 3. 并发设置
- LM Studio支持并发请求
- 但建议论文生成时使用单线程（确保质量）

### 4. 温度参数
- 学术写作推荐：0.7
- 需要更保守的输出：0.5
- 需要更多创意：0.8-0.9

---

## 🔄 从Ollama迁移

### 已完成的修改

1. **core/model_router.py**
   - 替换 `OllamaClient` 为 `LMStudioClient`
   - 使用OpenAI兼容API格式

2. **config.yaml**
   - 将 `ollama` 配置替换为 `lmstudio`
   - 更新默认模式为 `lmstudio`

3. **README.md**
   - 更新快速开始指南
   - 添加LM Studio安装说明

### 无需修改的部分
- 所有其他核心模块（文献管理、引用系统、审稿系统等）
- 配置文件结构和路由规则
- Web API接口

---

## ❓ 常见问题

**Q: LM Studio服务启动失败？**
A: 检查端口1234是否被占用，或在LM Studio设置中更改端口

**Q: 模型推理速度慢？**
A: 
- 检查是否使用GPU加速
- 尝试更小的模型或更低的量化版本（Q4）
- 减少max_tokens参数

**Q: 需要更改端口号？**
A: 在LM Studio设置中更改端口，同时更新 `config.yaml` 中的 `base_url`

**Q: 支持多模型切换吗？**
A: LM Studio一次只能加载一个模型，切换需要在界面中手动操作

---

**更新时间**：2025-12-20 19:20
**状态**：已完成从Ollama到LM Studio的迁移
