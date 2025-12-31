# AI学术助手 - 打包与发布指南

## 概述

本文档说明如何将 AI学术助手 打包成 Windows 可执行程序(.exe) 和安装包。

## 方法一：快速打包（生成便携版）

### 步骤

1. **双击运行** `build_exe.bat`
2. 等待构建完成（约5-10分钟）
3. 生成的程序在 `dist/AI学术助手/` 目录下

### 输出

```
dist/
└── AI学术助手/
    ├── AI学术助手.exe    ← 主程序
    ├── config.yaml        ← 配置文件
    ├── templates/         ← 模板目录
    ├── output/            ← 输出目录
    └── ... (其他运行时文件)
```

### 分发方式

将整个 `AI学术助手` 文件夹打包成 ZIP，用户解压后即可运行。

---

## 方法二：创建安装包（推荐）

### 前置要求

1. 下载安装 [Inno Setup](https://jrsoftware.org/isdl.php)
2. 先运行 `build_exe.bat` 生成 EXE

### 步骤

1. 打开 **Inno Setup Compiler**
2. 点击 `File` → `Open` → 选择 `installer.iss`
3. 点击 `Build` → `Compile`
4. 生成的安装包在 `installer_output/` 目录

### 输出

```
installer_output/
└── AI学术助手_安装程序_v1.0.0.exe   ← 安装包（约 500MB-1GB）
```

### 安装包特性

- ✅ 标准 Windows 安装向导
- ✅ 自动创建开始菜单快捷方式
- ✅ 可选创建桌面快捷方式
- ✅ 支持卸载
- ✅ 中文安装界面

---

## 首次运行配置

用户安装后首次运行需要：

1. **配置 API Key**
   - 打开程序 → 模型配置 标签页
   - 输入 API Key（如 SiliconFlow、DeepSeek 等）

2. **准备文献池**（可选）
   - 准备 `.txt` 格式的文献池文件
   - 在程序中上传

---

## 注意事项

### 体积优化

打包后的程序较大（500MB-1GB），主要因为：
- PyTorch 和 Transformers 库
- Sentence-Transformers 模型
- wxPython GUI 库

### 依赖问题

如果遇到依赖缺失：
1. 确保虚拟环境已激活
2. 运行 `pip install -r requirements.txt`
3. 重新执行打包

### 杀毒软件误报

部分杀毒软件可能误报 PyInstaller 打包的程序。解决方案：
1. 添加到白名单
2. 使用代码签名证书签名程序

---

## 程序图标

如需自定义程序图标：

1. 准备 `.ico` 格式图标文件
2. 放置到 `assets/icon.ico`
3. 重新运行打包脚本

推荐图标尺寸：256x256 像素

---

## 构建环境

- Windows 10/11 x64
- Python 3.10+
- PyInstaller 6.0+
- 可用磁盘空间：5GB+

---

## 常见问题

### Q: 打包失败，提示缺少模块？

运行以下命令确保依赖完整：
```bash
pip install sentence-transformers torch faiss-cpu wxPython pyinstaller
```

### Q: 程序启动时闪退？

1. 检查 `config.yaml` 是否存在
2. 检查 `.env` 文件是否配置了有效的 API Key
3. 查看 `logs/` 目录下的日志文件

### Q: 安装后找不到程序？

检查开始菜单 → AI学术助手 或桌面快捷方式
