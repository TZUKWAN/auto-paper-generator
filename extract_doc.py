"""提取Word文档内容的辅助脚本"""
from docx import Document
import json

doc = Document('理论研究.docx')

# 提取所有段落
content = {
    'paragraphs': [],
    'sections': []
}

current_section = None

for para in doc.paragraphs:
    text = para.text.strip()
    if not text:
        continue
    
    # 检测是否是标题
    if para.style.name.startswith('Heading'):
        if current_section:
            content['sections'].append(current_section)
        current_section = {
            'title': text,
            'level': para.style.name,
            'content': []
        }
    elif current_section:
        current_section['content'].append(text)
    else:
        content['paragraphs'].append(text)

if current_section:
    content['sections'].append(current_section)

# 输出为JSON
with open('理论研究_内容.json', 'w', encoding='utf-8') as f:
    json.dump(content, f, ensure_ascii=False, indent=2)

print(f"提取完成！共{len(content['sections'])}个章节")
print("\n章节列表：")
for i, section in enumerate(content['sections'], 1):
    print(f"{i}. {section['title']} ({len(section['content'])} 段)")
