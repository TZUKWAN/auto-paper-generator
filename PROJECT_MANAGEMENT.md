# 项目级文献池管理说明

## 📁 新架构：每个论文项目独立管理

### 项目文件夹结构

```
data/projects/
├── 20251220_190000_AI伦理研究/
│   ├── literature/
│   │   └── literature_pool.txt  # 该项目的文献池
│   ├── pdfs/                    # 该项目的PDF参考文档
│   │   ├── 论文1.pdf
│   │   └── 论文2.pdf
│   └── output/                  # 该项目的输出文件
│       ├── 论文初稿.md
│       ├── 论文初稿_审稿报告.json
│       └── quality_report.json
│
├── 20251220_200000_另一个研究/
│   ├── literature/
│   ├── pdfs/
│   └── output/
│
└── ...
```

---

## 🚀 使用方法

### 方法1: 命令行模式

```bash
# 创建新项目并生成论文
python main.py \
  --project "AI伦理问题研究" \
  --literature "path/to/uploaded_literature.txt" \
  --pdfs "path/to/pdf_folder"
```

**参数说明**：
- `--project`: 项目名称（必选）
- `--literature`: 上传的文献池TXT文件路径（可选）
- `--pdfs`: PDF参考文档文件夹路径（可选）

### 方法2: Python调用

```python
from main import main

# 创建新项目
output_path = main(
    project_name="AI伦理问题研究",
    literature_txt_path="path/to/literature.txt",
    pdf_folder_path="path/to/pdfs"
)

print(f"论文已生成: {output_path}")
```

### 方法3: Web界面（前端上传）

**推荐流程**：

1. **前端提供文献池上传功能**
   - 用户在Web界面上传TXT文件
   - 后端接收并保存到临时文件

2. **调用论文生成API**
   ```python
   POST /api/generate_paper
   
   {
     "project_name": "AI伦理问题研究",
     "literature_txt_path": "/tmp/uploaded_literature.txt",
     "pdf_folder_path": null  // 可选
   }
   ```

3. **系统自动**：
   - 创建项目文件夹（带时间戳）
   - 复制文献池TXT到项目的`literature/`目录
   - 重命名为标准文件名`literature_pool.txt`
   - 生成论文并保存到项目的`output/`目录

---

## 📤 文献池TXT格式

上传的TXT文件格式保持不变：

```
[1]刘卓红, 郝慧玲. 马克思主义思想精髓...[J]. 社会科学家, 2025, (06): 47-53. 摘要:...

[2]作者2. 论文标题2[J]. 期刊名, 年份, (卷期): 页码. 摘要:...

[3]作者3. 论文标题3[J]. 期刊名, 年份, (卷期): 页码. 摘要:...
```

**系统会自动**：
- 保存到项目文献池文件夹
- 重命名为`literature_pool.txt`
- 无需用户手动修改文件名

---

## 🔧 配置说明

### config.yaml 新增配置

```yaml
literature:
  # 启用项目级管理
  use_project_manager: true
  projects_base_dir: "data/projects"
  
  # 传统单一文献池（兼容模式）
  pool_path: "data/literature_pool.txt"
```

**配置说明**：
- `use_project_manager`: 是否启用项目级管理（默认true）
- `projects_base_dir`: 所有项目的存放目录
- `pool_path`: 兼容模式下使用的单一文献池路径

---

## 🎯 核心优势

### 1. 项目隔离
- 每个论文独立文献池
- 互不干扰
- 易于管理和归档

### 2. 自动化管理
- 自动创建项目文件夹
- 自动重命名文献池文件
- 自动组织输出文件

### 3. 可追溯性
- 项目ID包含时间戳
- 完整保留生成记录
- 方便后续查找

### 4. 灵活性
- 支持前端上传
- 支持命令行调用
- 支持Python API

---

## 🛠️ Web API示例（Flask）

```python
from flask import Flask, request, jsonify
import os
from main import main

app = Flask(__name__)

@app.route('/api/upload_literature', methods=['POST'])
def upload_literature():
    """上传文献池TXT"""
    file = request.files['literature_file']
    
    # 保存到临时文件
    temp_path = f"/tmp/literature_{int(time.time())}.txt"
    file.save(temp_path)
    
    return jsonify({
        'success': True,
        'temp_path': temp_path
    })

@app.route('/api/generate_paper', methods=['POST'])
def generate_paper():
    """生成论文"""
    data = request.json
    
    try:
        output_path = main(
            project_name=data['project_name'],
            literature_txt_path=data.get('literature_txt_path'),
            pdf_folder_path=data.get('pdf_folder_path')
        )
        
        return jsonify({
            'success': True,
            'output_path': output_path
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(port=5000)
```

---

## 📊 项目管理API

```python
from core.project_manager import ProjectLiteratureManager

# 创建管理器
proj_mgr = ProjectLiteratureManager("data/projects")

# 列出所有项目
projects = proj_mgr.list_projects()
for proj in projects:
    print(f"项目ID: {proj['id']}")
    print(f"路径: {proj['path']}")
    print(f"创建时间: {proj['created']}")

# 获取项目路径
project_path = projects[0]['path']

# 获取项目的文献池路径
lit_pool = proj_mgr.get_literature_pool_path(project_path)

# 获取项目的PDF文件夹
pdf_folder = proj_mgr.get_pdf_folder_path(project_path)

# 获取项目的输出文件夹
output_folder = proj_mgr.get_output_folder_path(project_path)
```

---

## ✅ 已删除的功能

根据用户需求，已确认删除：
- ❌ 图片生成功能
- ❌ 表格生成功能
- ❌ Mermaid图表功能

论文中不会包含任何图片和表格内容。

---

**更新时间**：2025-12-20 19:15
**状态**：已完成项目级文献池管理功能
