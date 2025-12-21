"""文献解析器 - 解析TXT文献池"""
import re
import os
import logging

logger = logging.getLogger(__name__)

class LiteratureParser:
    """TXT文献池解析器"""
    
    def __init__(self):
        pass
    
    def parse_txt_pool(self, filepath):
        """
        解析TXT文献池（支持多行格式：题录行 + 摘要行）
        
        Args:
            filepath: 文献池TXT文件路径
            
        Returns:
            文献列表
        """
        if not os.path.exists(filepath):
            logger.warning(f"文献池文件不存在: {filepath}，将进入纯网络检索模式")
            return []

        logger.info(f"开始解析文献池: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        literature_pool = []
        current_entry = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 判断是否为新的引用行 (以 [数字] 开头)
            id_match = re.match(r'^\[(\d+)\]', line)
            
            if id_match:
                # 保存上一个条目
                if current_entry:
                    current_entry['used'] = False
                    literature_pool.append(current_entry)
                
                # 开始新条目
                current_entry = self._parse_citation_line(line, id_match)
            
            elif current_entry:
                # 如果不是新引用行，且当前有正在处理的条目，则归为摘要或补充信息
                # 处理 "摘要:" 前缀
                clean_line = line
                if clean_line.startswith('摘要:'):
                    clean_line = clean_line[3:]
                elif clean_line.startswith('Abstract:'):
                    clean_line = clean_line[9:]
                
                # 追加到摘要
                if current_entry['abstract']:
                    current_entry['abstract'] += " " + clean_line.strip()
                else:
                    current_entry['abstract'] = clean_line.strip()
            
            else:
                # 既不是新条目，也没有当前条目（可能是文件头的杂讯），跳过
                pass
        
        # 保存最后一个条目
        if current_entry:
            current_entry['used'] = False
            literature_pool.append(current_entry)
        
        # 去重
        unique_pool = self._deduplicate(literature_pool)
        
        logger.info(f"文献池解析完成: 原始{len(literature_pool)}条，去重后{len(unique_pool)}条")
        return unique_pool

    def _parse_citation_line(self, line, id_match):
        """解析引用行基础信息"""
        try:
            entry_id = int(id_match.group(1))
            content = line[id_match.end():].strip()
            
            # 尝试分离行内摘要（虽然现在主要是多行格式，但兼容单行）
            abstract = ""
            if '摘要:' in content:
                content, abstract = content.split('摘要:', 1)
            
            # 解析作者、标题、来源
            # 典型格式: 张三. 文章标题[J]. 期刊名, 2025, (1): 123.
            
            authors = "未知作者"
            title = "未知标题"
            year = "未知"
            journal = "未知"
            source = content
            
            # 1. 提取作者 (第一个点之前)
            parts = content.split('.', 1)
            if len(parts) >= 2:
                authors = parts[0].strip()
                remainder = parts[1].strip()
                
                # 2. 提取标题 ([J], [M] 等之前)
                # 常见的文献标识符
                type_match = re.search(r'\[([A-Z])\]', remainder)
                if type_match:
                    title_end = type_match.start()
                    title = remainder[:title_end].strip()
                    source_part = remainder[type_match.end():].strip('. ')
                    
                    # 3. 解析来源详情
                    # 格式: 期刊名, 年份, ...
                    source_parts = source_part.split(',')
                    if len(source_parts) >= 1:
                        journal = source_parts[0].strip()
                    
                    # 尝试寻找年份 20xx
                    year_match = re.search(r'(20\d{2}|19\d{2})', source_part)
                    if year_match:
                        year = year_match.group(1)
                else:
                    # 没有标准标识符，做简单分割
                    title = remainder
            
            return {
                'id': entry_id,
                'authors': authors,
                'title': title,
                'year': year,
                'journal': journal,
                'source': source,
                'abstract': abstract.strip(),
                'full_citation': line
            }
        except Exception as e:
            logger.warning(f"解析引用行出错: {line[:30]}... {e}")
            return {
                'id': int(id_match.group(1)),
                'authors': '未知',
                'title': line,
                'year': '未知',
                'journal': '未知',
                'source': line,
                'abstract': '',
                'full_citation': line
            }
            
    def _deduplicate(self, pool):
        """基于标题去重"""
        seen_titles = set()
        unique_pool = []
        
        for lit in pool:
            # 简单清洗标题再比对
            clean_title = re.sub(r'\s+', '', lit['title'])
            if clean_title not in seen_titles:
                seen_titles.add(clean_title)
                unique_pool.append(lit)
            else:
                logger.debug(f"重复文献已过滤: {lit['title']}")
        
        return unique_pool
