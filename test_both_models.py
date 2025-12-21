# -*- coding: utf-8 -*-
"""
诊断脚本：测试本地和在线模型连接
"""
import requests
import sys
import os

print("="*60)
print("模型连接诊断工具")
print("="*60)

# 测试1：LM Studio 本地模型
print("\n[测试1] LM Studio 本地模型")
print("-"*60)
try:
    response = requests.get("http://localhost:1234/v1/models", timeout=5)
    if response.status_code == 200:
        print("[OK] LM Studio 服务正常运行")
        models = response.json()
        print("可用模型数: {}".format(len(models.get('data', []))))
        for m in models.get('data', [])[:3]:
            print("  - {}".format(m['id']))
    else:
        print("[WARN] LM Studio 返回异常状态码: {}".format(response.status_code))
except requests.exceptions.ConnectionError:
    print("[FAIL] 无法连接到 LM Studio (http://localhost:1234)")
    print("   请确认:")
    print("   1. LM Studio 软件已打开")
    print("   2. 在左侧 'Local Server' 选项卡点击了 'Start Server'")
    print("   3. 端口为 1234 (默认)")
except Exception as e:
    print("[FAIL] LM Studio 测试失败: {}".format(str(e)))

# 测试1.1：实际调用测试
print("\n[测试1.1] LM Studio 实际调用测试")
print("-"*60)
try:
    response = requests.post(
        "http://localhost:1234/v1/chat/completions",
        json={
            "model": "qwen/qwen3-8b",
            "messages": [{"role": "user", "content": "你好"}],
            "max_tokens": 50
        },
        timeout=30
    )
    if response.status_code == 200:
        data = response.json()
        reply = data['choices'][0]['message']['content']
        print("[OK] LM Studio 调用成功")
        print("回复: {}".format(reply[:100]))
    else:
        print("[FAIL] LM Studio 调用失败: {}".format(response.status_code))
        print("响应: {}".format(response.text[:200]))
except Exception as e:
    print("[FAIL] LM Studio 调用失败: {}".format(str(e)))

# 测试2：SiliconFlow 在线模型
print("\n[测试2] SiliconFlow 在线模型")
print("-"*60)

# 读取配置文件获取 API Key
api_key = None
try:
    import yaml
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        api_key = config.get('model_routing', {}).get('silicon', {}).get('api_key')
except:
    pass

if not api_key:
    api_key = os.environ.get('SILICON_API_KEY')

if not api_key:
    print("[FAIL] 未找到 API Key")
    print("   请在 config.yaml 中设置或通过 UI 保存配置")
else:
    print("[OK] API Key 已找到: {}...{}".format(api_key[:10], api_key[-5:]))
    
    # 测试调用
    try:
        response = requests.post(
            "https://api.siliconflow.cn/v1/chat/completions",
            headers={
                "Authorization": "Bearer {}".format(api_key),
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
                "messages": [{"role": "user", "content": "你好"}],
                "max_tokens": 50
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            reply = data['choices'][0]['message']['content']
            print("[OK] SiliconFlow 调用成功")
            print("回复: {}".format(reply[:100]))
        elif response.status_code == 401:
            print("[FAIL] SiliconFlow 认证失败 (401 Unauthorized)")
            print("   请检查 API Key 是否正确")
        else:
            print("[FAIL] SiliconFlow 调用失败: {}".format(response.status_code))
            print("响应: {}".format(response.text[:200]))
    except Exception as e:
        print("[FAIL] SiliconFlow 调用失败: {}".format(str(e)))

print("\n" + "="*60)
print("诊断完成")
print("="*60)
