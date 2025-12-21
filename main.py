"""主程序 - 自动化论文生成（项目级文献池版本）"""
import sys
import json
import os
from config import config
from utils.logger import setup_logging
from core.literature_parser import LiteratureParser
from core.semantic_retriever import SemanticRetriever
from core.model_router import ModelRouter
from core.citation_manager import CitationManager
from core.template_engine import TemplateEngine
from core.expert_review import ExpertReviewSystem
from core.pdf_reference import PDFReferenceManager
from core.project_manager import ProjectLiteratureManager

# 初始化日志
logger = setup_logging(
    log_path=config.get('logging.path'),
    level=config.get('logging.level')
)

def main(project_name=None, literature_txt_path=None, pdf_folder_path=None, extra_idea=None):
    """
    主函数
    
    Args:
        project_name: 项目名称
        literature_txt_path: 文献池路径（可选）
        pdf_folder_path: PDF文件夹路径（可选）
        extra_idea: 项目核心思路/关键词（可选）
    """
    try:
        logger.info("="*60)
        logger.info("自动化论文生成系统启动（含专家审稿）")
        logger.info("="*60)
        
        # 0. 项目管理 - 修正逻辑：如果项目已存在（通过project_name传入的是ID或项目目录已建），则复用
        # 但此处我们做一个简单假设：如果project_name匹配特定ID格式，则查找；否则新建
        # 为了兼容API的调用，API应负责管理ID传递
        
        project_path = None
        
        # 简单检查：project_name是否看起来像ID
        is_existing_id = False
        if project_name and os.path.exists(os.path.join(config.get('literature.projects_base_dir'), project_name)):
            is_existing_id = True
            project_path = os.path.join(config.get('literature.projects_base_dir'), project_name)
            logger.info(f"使用现有项目: {project_path}")
        
        # 路径解析优先级：传入参数 > 项目文件夹推断 > 默认配置
        if literature_txt_path:
            # 最高优先级：明确传入的路径
            lit_pool_path = literature_txt_path
        elif project_path:
            # 次优先级：从现有项目推断
            lit_pool_path = os.path.join(project_path, "literature", "literature_pool.txt")
        else:
            # 兜底：使用默认配置
            lit_pool_path = config.get('literature.pool_path')
        
        if pdf_folder_path:
            pdf_folder = pdf_folder_path
        elif project_path:
            pdf_folder = os.path.join(project_path, "pdfs")
        else:
            pdf_folder = config.get('reference_documents.pdf_folder')
        
        if project_path:
            # 过程数据：在项目文件夹下
            process_data_folder = project_path
        else:
            process_data_folder = "data/temp"
            
        # 最终成果：在根目录 output 文件夹下
        output_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        os.makedirs(output_folder, exist_ok=True)
        logger.info(f"最终输出目录: {output_folder}")
        
        # 1. 加载文献池
        logger.info(f"步骤1: 加载文献池: {lit_pool_path}")
        parser = LiteratureParser()
        literature_pool = parser.parse_txt_pool(lit_pool_path)
        logger.info(f"文献池加载完成: {len(literature_pool)} 条文献")
        
        # 2. 构建语义检索引擎
        logger.info("步骤2: 构建语义检索引擎...")
        retriever = SemanticRetriever(literature_pool)
        
        # 3. 加载PDF参考文档（如果启用）
        pdf_ref_mgr = None
        if config.get('reference_documents.enabled', False):
            logger.info(f"步骤3: 加载PDF参考文档: {pdf_folder}")
            pdf_ref_mgr = PDFReferenceManager(pdf_folder)
            logger.info(f"PDF参考文档加载完成: {len(pdf_ref_mgr.documents)} 个文件")
        else:
            logger.info("步骤3: PDF参考功能未启用，跳过")
        
        # 4. 初始化大模型路由
        logger.info("步骤4: 初始化大模型路由...")
        router = ModelRouter(config)
        
        # 5. 初始化引用管理器
        logger.info("步骤5: 初始化引用管理器...")
        citation_mgr = CitationManager(literature_pool, retriever, config)
        
        # 6. 准备项目上下文
        project_title = config.get('project.title')
        if is_existing_id:
            # 尝试从目录名中提取真实标题（如果需要），或者就用项目ID
            # 更好的做法是在项目目录存一个meta.json，但为了简化，我们这里如果传了extra_idea就用它
            pass
        
        if project_name and not is_existing_id:
             project_title = project_name
             
        project_keywords = config.get('project.keywords')
        
        # 构建上下文
        idea_content = extra_idea if extra_idea else project_keywords
        
        # 4. 初始化模板引擎
        logger.info("步骤6: 加载模板...")
        
        # 将过程文件夹加入上下文，供中间保存使用
        project_context = {
            'title': project_name,
            'keywords': config.get('project.keywords', ''),
            'extra_idea': extra_idea,
            'output_folder': process_data_folder  # ⭐ 过程文件（分章节MD）保存在Data项目文件夹
        }
        
        engine = TemplateEngine(
            template_path=config.get('template.path'),
            model_router=router,
            citation_manager=citation_mgr,
            project_context=project_context,
            pdf_reference_mgr=pdf_ref_mgr,
            config=config
        )
        
        logger.info("步骤7: 生成论文初稿...")
        paper_draft = engine.generate_paper()
        
        # 8. 专家审稿与优化（如果启用）
        final_paper = paper_draft
        review_results = None
        
        if config.get('expert_review.enabled', False):
            logger.info("\n" + "="*60)
            logger.info("步骤8: 专家审稿系统介入...")
            expert_system = ExpertReviewSystem(router, output_dir=process_data_folder, external_search=engine.external_search)
            review_results = expert_system.review_and_optimize_iteratively(paper_draft)
            
            final_paper = review_results['final_paper']
            
            # 保存审稿报告（所有轮次）- 放在项目文件夹内
            review_report_path = os.path.join(process_data_folder, '审稿报告.json')
            
            with open(review_report_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'rounds': review_results['rounds'],
                    'final_score': review_results['final_score'],
                    'all_reviews': review_results['all_reviews']
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"审稿报告已保存: {review_report_path}")
            logger.info(f"优化轮次: {review_results['rounds']} 轮")
            logger.info(f"最终评分: {review_results['final_score']}/100")
        else:
            logger.info("步骤8: 专家审稿未启用，跳过")
        
        # 9. 保存优化版论文 (V1 - 未扩写)
        safe_filename = "".join([c for c in project_name if c.isalnum() or c in (' ', '-', '_', '\u4e00-\u9fa5')]).strip()
        output_path_v1 = os.path.join(output_folder, f'{safe_filename}_标准优化版.md')
        
        logger.info(f"步骤9: 保存标准优化版到 {output_path_v1}...")
        
        with open(output_path_v1, 'w', encoding='utf-8') as f:
            f.write(final_paper)
            
        # 导出Word (V1)
        try:
            from core.docx_exporter import convert_markdown_to_docx
            docx_path_v1 = os.path.join(output_folder, f'{safe_filename}_标准优化版.docx')
            convert_markdown_to_docx(final_paper, docx_path_v1)
            logger.info(f"Word文档(标准版)已导出: {docx_path_v1}")
        except Exception as e:
            logger.error(f"导出Word文档失败: {str(e)}")

        # 10. 执行终极扩写 (V2)
        logger.info("\n" + "="*60)
        logger.info("步骤10: 执行终极扩写 (目标：内容深度翻倍)...")
        expanded_paper = engine.expand_full_paper_content(final_paper)
        
        # 保存扩写版 (V2)
        output_path_v2 = os.path.join(output_folder, f'{safe_filename}_深度扩写版.md')
        logger.info(f"保存深度扩写版到 {output_path_v2}...")
        
        with open(output_path_v2, 'w', encoding='utf-8') as f:
            f.write(expanded_paper)
            
        # 导出Word (V2)
        try:
            docx_path_v2 = os.path.join(output_folder, f'{safe_filename}_深度扩写版.docx')
            convert_markdown_to_docx(expanded_paper, docx_path_v2)
            logger.info(f"Word文档(扩写版)已导出: {docx_path_v2}")
        except Exception as e:
            logger.error(f"导出Word文档失败: {str(e)}")
        
        # 11. 生成质量报告 (基于扩写版)
        if config.get('quality_metrics.enabled'):
            stats = citation_mgr.get_statistics()
            stats['output_file'] = output_path_v2
            stats['word_count_v1'] = len(final_paper)
            stats['word_count_v2'] = len(expanded_paper)
            stats['expert_review_enabled'] = config.get('expert_review.enabled', False)
            stats['pdf_reference_enabled'] = config.get('reference_documents.enabled', False)
            stats['project_path'] = project_path if project_path else "传统模式"
            
            if pdf_ref_mgr:
                stats['pdf_documents_count'] = len(pdf_ref_mgr.documents)
            
            report_path = os.path.join(output_folder, 'quality_report.json')
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            
            logger.info(f"质量报告已生成: {report_path}")
            logger.info(f"标准版字数: {stats['word_count_v1']}")
            logger.info(f"扩写版字数: {stats['word_count_v2']}")
            logger.info(f"总引用数: {stats['total_citations']}")
        
        logger.info("="*60)
        logger.info("论文生成全流程完成!")
        logger.info(f"V1 输出: {output_path_v1}")
        logger.info(f"V2 输出: {output_path_v2}")
        if project_path:
            logger.info(f"项目路径: {project_path}")
        logger.info("="*60)
        
        return {
            'v1': output_path_v1,
            'v2': output_path_v2
        }
        
    except KeyboardInterrupt:
        logger.info("用户中断程序")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    # 命令行模式：可以通过参数指定项目信息
    import argparse
    
    parser = argparse.ArgumentParser(description='自动化论文生成')
    parser.add_argument('--project', type=str, help='项目名称')
    parser.add_argument('--literature', type=str, help='文献池TXT文件路径')
    parser.add_argument('--pdfs', type=str, help='PDF文件夹路径')
    
    args = parser.parse_args()
    
    main(
        project_name=args.project,
        literature_txt_path=args.literature,
        pdf_folder_path=args.pdfs
    )
