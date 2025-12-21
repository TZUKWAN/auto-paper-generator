# 前端API配置接口文档

## 🎯 概述

系统提供完整的前端API配置接口，支持在网页界面自行配置硅基流动API的所有参数。

---

## 📡 API端点

### 1. 获取当前配置

```http
GET /api/config/silicon
```

**响应示例**：
```json
{
  "success": true,
  "config": {
    "model": "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
    "max_tokens": 4096,
    "temperature": 0.7,
    "top_p": 0.7,
    "top_k": 50,
    "min_p": 0.05,
    "frequency_penalty": 0.5,
    "enable_thinking": true,
    "thinking_budget": 4096
  }
}
```

### 2. 更新配置

```http
POST /api/config/silicon
Content-Type: application/json

{
  "api_key": "sk-your-api-key-here",
  "model": "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
  "max_tokens": 4096,
  "temperature": 0.7,
  "top_p": 0.7,
  "top_k": 50,
  "min_p": 0.05,
  "frequency_penalty": 0.5,
  "enable_thinking": true,
  "thinking_budget": 4096
}
```

**响应**：
```json
{
  "success": true,
  "message": "配置已更新（当前会话有效）"
}
```

### 3. 获取可用模型列表

```http
GET /api/models/available
```

**响应**：
```json
{
  "success": true,
  "models": [
    {
      "id": "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
      "name": "DeepSeek R1 (Qwen3-8B)",
      "description": "深度思考模型，支持思维链",
      "supports_thinking": true
    },
    {
      "id": "Qwen/Qwen2.5-72B-Instruct",
      "name": "Qwen2.5 72B",
      "description": "通义千问大模型，综合能力强",
      "supports_thinking": false
    }
  ]
}
```

---

## 🎨 前端示例代码

### React/Vue 配置组件示例

```javascript
// 获取当前配置
async function loadConfig() {
  const response = await fetch('http://localhost:5000/api/config/silicon');
  const data = await response.json();
  
  if (data.success) {
    console.log('当前配置:', data.config);
    // 更新UI
  }
}

// 更新配置
async function updateConfig(newConfig) {
  const response = await fetch('http://localhost:5000/api/config/silicon', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      api_key: newConfig.apiKey,
      model: newConfig.model,
      temperature: newConfig.temperature,
      max_tokens: newConfig.maxTokens,
      enable_thinking: newConfig.enableThinking,
      thinking_budget: newConfig.thinkingBudget
    })
  });
  
  const data = await response.json();
  
  if (data.success) {
    alert('配置更新成功！');
  } else {
    alert('配置更新失败: ' + data.error);
  }
}

// 获取可用模型
async function loadModels() {
  const response = await fetch('http://localhost:5000/api/models/available');
  const data = await response.json();
  
  if (data.success) {
    return data.models;
  }
}
```

### HTML配置表单示例

```html
<!DOCTYPE html>
<html>
<head>
  <title>硅基流动API配置</title>
  <style>
    .config-form { max-width: 600px; margin: 0 auto; padding: 20px; }
    .form-group { margin-bottom: 15px; }
    label { display: block; margin-bottom: 5px; font-weight: bold; }
    input, select { width: 100%; padding: 8px; }
    button { padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer; }
  </style>
</head>
<body>
  <div class="config-form">
    <h2>硅基流动API配置</h2>
    
    <div class="form-group">
      <label>API密钥</label>
      <input type="password" id="apiKey" placeholder="sk-xxx">
    </div>
    
    <div class="form-group">
      <label>模型</label>
      <select id="model">
        <option value="deepseek-ai/DeepSeek-R1-0528-Qwen3-8B">DeepSeek R1 (Qwen3-8B)</option>
        <option value="Qwen/Qwen2.5-72B-Instruct">Qwen2.5 72B</option>
        <option value="Qwen/Qwen2.5-7B-Instruct">Qwen2.5 7B</option>
      </select>
    </div>
    
    <div class="form-group">
      <label>最大Token数</label>
      <input type="number" id="maxTokens" value="4096">
    </div>
    
    <div class="form-group">
      <label>温度 (0-1)</label>
      <input type="number" id="temperature" step="0.1" min="0" max="1" value="0.7">
    </div>
    
    <div class="form-group">
      <label>Top P</label>
      <input type="number" id="topP" step="0.1" min="0" max="1" value="0.7">
    </div>
    
    <div class="form-group">
      <label>启用思维链 (DeepSeek模型)</label>
      <input type="checkbox" id="enableThinking" checked>
    </div>
    
    <div class="form-group">
      <label>思维预算</label>
      <input type="number" id="thinkingBudget" value="4096">
    </div>
    
    <button onclick="saveConfig()">保存配置</button>
  </div>
  
  <script>
    async function saveConfig() {
      const config = {
        api_key: document.getElementById('apiKey').value,
        model: document.getElementById('model').value,
        max_tokens: parseInt(document.getElementById('maxTokens').value),
        temperature: parseFloat(document.getElementById('temperature').value),
        top_p: parseFloat(document.getElementById('topP').value),
        enable_thinking: document.getElementById('enableThinking').checked,
        thinking_budget: parseInt(document.getElementById('thinkingBudget').value)
      };
      
      const response = await fetch('http://localhost:5000/api/config/silicon', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      
      const data = await response.json();
      alert(data.success ? '配置保存成功！' : '保存失败: ' + data.error);
    }
    
    // 页面加载时获取当前配置
    window.onload = async function() {
      const response = await fetch('http://localhost:5000/api/config/silicon');
      const data = await response.json();
      
      if (data.success) {
        document.getElementById('model').value = data.config.model;
        document.getElementById('maxTokens').value = data.config.max_tokens;
        document.getElementById('temperature').value = data.config.temperature;
        document.getElementById('topP').value = data.config.top_p;
        document.getElementById('enableThinking').checked = data.config.enable_thinking;
        document.getElementById('thinkingBudget').value = data.config.thinking_budget;
      }
    };
  </script>
</body>
</html>
```

---

## 📋 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `api_key` | string | - | 硅基流动API密钥 |
| `model` | string | DeepSeek-R1 | 模型ID |
| `max_tokens` | int | 4096 | 最大生成token数 |
| `temperature` | float | 0.7 | 温度参数（0-1），越高越随机 |
| `top_p` | float | 0.7 | 核采样参数 |
| `top_k` | int | 50 | Top-K采样 |
| `min_p` | float | 0.05 | 最小概率阈值 |
| `frequency_penalty` | float | 0.5 | 频率惩罚 |
| `enable_thinking` | bool | true | 启用思维链（仅DeepSeek） |
| `thinking_budget` | int | 4096 | 思维链预算token数 |

---

## 🔒 安全提示

⚠️ **重要**：
- API密钥通过POST请求传输，建议使用HTTPS
- 配置仅在当前会话有效，重启服务器后恢复默认
- 如需持久化配置，需手动编辑`config.yaml`或`.env`文件

---

## 🚀 快速测试

```bash
# 启动Web API服务
python web_api.py

# 测试获取配置
curl http://localhost:5000/api/config/silicon

# 测试更新配置
curl -X POST http://localhost:5000/api/config/silicon \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "sk-xxx",
    "model": "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
    "temperature": 0.8
  }'
```

---

**更新时间**: 2025-12-20 19:25
**状态**: 已完成前端API配置系统
