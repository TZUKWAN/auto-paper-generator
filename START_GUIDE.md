# 🚀 论文生成系统启动指南

## ✅ 当前状态

### 1. SearXNG服务 ✓
- 状态：已运行
- 端口：8080
- 地址：http://localhost:8080

### 2. 环境配置 ✓  
- .env文件已创建
- API密钥已配置（请替换为您的真实密钥）
- 项目文件夹已创建

---

## 🎯 启动系统

### 方式1: Web API模式（推荐）

```bash
# 启动Web API服务器
cd "D:\自动化商业计划书脚本\自动化论文脚本"
python web_api.py
```

**访问地址**：
- API服务：http://localhost:5000
- 健康检查：http://localhost:5000/api/health

### 方式2: 命令行模式

```bash
# 直接生成论文
python main.py --project "测试论文" --literature "path/to/literature.txt"
```

---

## 📋 完整功能检查清单

✅ SearXNG联网检索（30条搜索结果）
✅ 硅基流动API配置（DeepSeek R1模型）
✅ 5专家AI审稿系统
✅ PDF参考文档支持
✅ 项目级文献池管理
✅ 前端API配置接口

---

## 🔑 配置API密钥

编辑 `.env` 文件：

```bash
# 您的真实硅基流动API密钥
SILICON_API_KEY=sk-你的真实密钥
```

获取密钥：https://cloud.siliconflow.cn/

---

## 🧪 测试系统

### 1. 测试SearXNG

```bash
curl "http://localhost:8080/search?q=人工智能&format=json"
```

### 2. 测试Web API

```bash
# 健康检查
curl http://localhost:5000/api/health

# 获取配置
curl http://localhost:5000/api/config/silicon
```

### 3. 生成测试论文

```bash
curl -X POST http://localhost:5000/api/generate_paper \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "AI伦理研究",
    "literature_txt_path": null
  }'
```

---

## 📊 系统架构

```
前端配置界面
    ↓
Web API (端口5000)
    ↓
论文生成引擎
    ├── SearXNG联网检索 (30条)
    ├── PDF参考文档
    ├── 文献池检索
    ├── 5专家审稿
    └── AI生成优化
    ↓
输出最终论文
```

---

## 🛠️ 常用命令

```bash
# 查看SearXNG日志
docker logs searxng

# 重启SearXNG
docker restart searxng

# 查看Python依赖
pip list

# 安装/更新依赖
pip install -r requirements.txt
```

---

## ⚠️ 注意事项

1. **API密钥**：请替换.env中的测试密钥为您的真实密钥
2. **SearXNG**：已在运行，无需重复启动
3. **端口占用**：Web API使用5000端口，SearXNG使用8080端口
4. **网络连接**：确保能访问硅基流动API

---

## 📞 快速帮助

- 系统文档：`README.md`
- API配置：`FRONTEND_API_CONFIG.md`
- SearXNG集成：`SEARXNG_INTEGRATION.md`
- LM Studio配置：`LMSTUDIO_CONFIG.md`

---

**系统已就绪，现在可以启动生成论文！** 🎉
