
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
import re
import os

def convert_markdown_to_docx(markdown_text, output_path):
    """
    将Markdown文本转换为Word文档（学术论文标准排版）
    
    排版标准：
    - 一级标题：三号（16pt）加粗，居中
    - 二级标题：小三号（15pt）加粗，左对齐
    - 三级标题：四号（14pt）加粗，左对齐
    - 正文：小四号（12pt），中文宋体，英文Times New Roman
    - 行距：1.5倍
    """
    doc = Document()
    
    # --- 基础样式设置 ---
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)
    # 设置中文字体
    style._element.rPr.rFonts.set_qn('w:eastAsia', '宋体')
    
    # 设置行距 1.5倍
    paragraph_format = style.paragraph_format
    paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    
    # --- 标题样式定义 ---
    # Python-docx的默认Heading样式需要手动调整
    
    def set_heading_style(level, font_size_pt, is_bold=True, alignment=None):
        style_name = f'Heading {level}'
        if style_name not in doc.styles:
            return
            
        style = doc.styles[style_name]
        font = style.font
        font.name = 'Times New Roman'
        font.size = Pt(font_size_pt)
        font.bold = is_bold
        font.color.rgb = RGBColor(0, 0, 0)  # 纯黑
        style._element.rPr.rFonts.set_qn('w:eastAsia', '宋体')
        
        if alignment is not None:
            style.paragraph_format.alignment = alignment
            
        # 段前段后间距
        style.paragraph_format.space_before = Pt(12)
        style.paragraph_format.space_after = Pt(6)
        style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE

    # 应用样式配置
    set_heading_style(1, 16, True, WD_ALIGN_PARAGRAPH.CENTER) # 一级：三号(16pt)
    set_heading_style(2, 15, True, WD_ALIGN_PARAGRAPH.LEFT)   # 二级：小三(15pt)
    set_heading_style(3, 14, True, WD_ALIGN_PARAGRAPH.LEFT)   # 三级：四号(14pt)

    # --- 内容解析与写入 ---
    lines = markdown_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('# '):
            # 标题1: 三号加粗
            # 移除Markdown标记
            content = line.replace('#', '').strip()
            p = doc.add_heading(content, level=1)
            # 强制再设置一次对齐确保生效
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
        elif line.startswith('## '):
            # 标题2: 小三号加粗
            content = line.replace('##', '').strip()
            doc.add_heading(content, level=2)
            
        elif line.startswith('### '):
            # 标题3: 四号加粗
            content = line.replace('###', '').strip()
            doc.add_heading(content, level=3)
            
        elif line.startswith('- ') or line.startswith('* '):
            # 列表
            content = line[2:]
            p = doc.add_paragraph(content, style='List Bullet')
            
        else:
            # 正文
            # 清理Markdown加粗符号（如果需要）
            clean_line = line.replace('**', '')
            
            p = doc.add_paragraph(clean_line)
            # 首行缩进 2字符 (约24pt)
            p.paragraph_format.first_line_indent = Pt(24)
            # 确保行距
            p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE

    doc.save(output_path)
    return output_path
