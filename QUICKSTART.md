# 快速启动指南

## ⚠️ 重要：配置API密钥

本系统为**纯线上版本**，完全依赖在线大模型API运行。

### 步骤1: 配置API密钥

编辑 `config.yaml` 文件：

```yaml
model_routing:
  default_provider: siliconflow
  providers:
    siliconflow:
      enabled: true
      api_key: "你的硅基流动API密钥"
```

**获取API密钥**：
- 硅基流动：https://cloud.siliconflow.cn/
- 智谱AI：https://open.bigmodel.cn/
- 通义千问：https://dashscope.aliyuncs.com/
- DeepSeek：https://platform.deepseek.com/

### 步骤2: 准备文献池

创建文献池文件：

```bash
# 在 data/literature_pool.txt 中添加文献
[1]示例作者. 示例论文标题[J]. 示例期刊, 2024, (01): 1-10. 摘要:这是示例摘要内容...
```

建议准备100+条文献以获得更好的效果。

### 步骤3: 启动系统

```bash
# 命令行模式
python main.py --project "测试论文" --literature "data/literature_pool.txt"
```

---

## ✅ 现在可以启动了

```bash
# 确保在项目目录
cd "D:\自动化商业计划书脚本\自动化论文纯线上"

# 安装依赖（如果还没安装）
pip install -r requirements.txt

# 配置好API密钥后，运行
python main.py --project "我的第一篇论文" --literature "data/literature_pool.txt"
```

**状态**: 系统为纯线上版本，配置好API密钥即可运行！
