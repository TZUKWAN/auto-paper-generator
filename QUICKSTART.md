# 快速启动指南

## ⚠️ 重要：配置API密钥

系统现已配置为**在线模式**，无需启动LM Studio即可运行！

### 步骤1: 配置API密钥

编辑 `.env` 文件（如果不存在则创建）：

```bash
# 硅基流动API密钥（必需）
SILICON_API_KEY=你的硅基流动API密钥

# 智谱AI API密钥（可选，用于外部检索）
ZHIPU_API_KEY=你的智谱AI密钥
```

**获取API密钥**：
- 硅基流动：https://cloud.siliconflow.cn/
- 智谱AI：https://open.bigmodel.cn/

### 步骤2: 准备文献池

创建测试文献池文件（或上传你的文献）：

```bash
# 在 data/literature_pool.txt 中添加文献
[1]示例作者. 示例论文标题[J]. 示例期刊, 2024, (01): 1-10. 摘要:这是示例摘要内容...
```

### 步骤3: 启动系统

```bash
# 方式1: 直接运行（使用在线API）
python main.py --project "测试论文"

# 方式2: 启动Web API服务
python web_api.py
```

---

## 🔄 模式切换

### 当前模式：在线模式 ✓

- 使用硅基流动API
- 无需本地LM Studio
- 需要配置API密钥

### 切换到本地模式

如果你想使用本地LM Studio：

1. 启动LM Studio并加载模型
2. 修改`config.yaml`：
   ```yaml
   model_routing:
     default: "lmstudio"  # 改为lmstudio
   ```
3. 运行系统

### 混合模式（推荐）

可以同时使用两种模式：

```yaml
model_routing:
  default: "silicon"  # 默认在线
  
  routing_rules:
    local_nodes:  # 这些节点用本地（如果LM Studio可用）
      - "main_body"
    online_nodes:  # 这些节点用在线（更高质量）
      - "expert_review"
      - "abstract"
```

---

## ✅ 现在可以启动了

```bash
# 确保在项目目录
cd "D:\自动化商业计划书脚本\自动化论文脚本"

# 安装依赖（如果还没安装）
pip install -r requirements.txt

# 配置好API密钥后，运行
python main.py --project "我的第一篇论文" --literature "path/to/literature.txt"
```

**状态**: 系统已配置为在线模式，配置好API密钥即可运行！
