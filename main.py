"""主程序 - 自动化论文生成（重构版）
重构内容：
- 移除PDF参考功能
- 添加outline_data参数支持
- 分章节MD文件生成
"""
import sys
import json
import os
import re
from config import config
from utils.logger import setup_logging
from core.literature_parser import LiteratureParser
from core.semantic_retriever import SemanticRetriever
from core.model_router import ModelRouter
from core.citation_manager import CitationManager
from core.template_engine import TemplateEngine
from core.expert_review import ExpertReviewSystem
from core.project_manager import ProjectLiteratureManager

# 初始化日志
logger = setup_logging(
    log_path=config.get('logging.path'),
    level=config.get('logging.level')
)

def main(project_name=None, literature_txt_path=None, extra_idea=None, outline_data=None, progress_callback=None):
    """
    主函数
    
    Args:
        project_name: 项目名称/论文题目
        literature_txt_path: 文献池路径（可选）
        extra_idea: 项目核心思路/关键词（可选）
        outline_data: 用户编辑后的大纲数据（可选）
        progress_callback: 进度回调函数（可选），签名: (progress, stage, word_count, api_calls)
    """
    # 辅助函数：发送进度
    def report_progress(pct, stage, word_count=None, api_calls=None):
        if progress_callback:
            try:
                progress_callback(pct, stage, word_count, api_calls)
            except Exception:
                pass  # 忽略回调错误
    try:
        logger.info("="*60)
        logger.info("自动化论文生成系统启动（重构版）")
        logger.info("="*60)
        
        # 0. 项目路径设置
        project_path = None
        is_existing_id = False
        
        if project_name and os.path.exists(os.path.join(config.get('literature.projects_base_dir'), project_name)):
            is_existing_id = True
            project_path = os.path.join(config.get('literature.projects_base_dir'), project_name)
            logger.info(f"使用现有项目: {project_path}")
        
        # 路径解析优先级：传入参数 > 项目文件夹推断 > 默认配置
        if literature_txt_path:
            lit_pool_path = literature_txt_path
        elif project_path:
            lit_pool_path = os.path.join(project_path, "literature", "literature_pool.txt")
        else:
            lit_pool_path = config.get('literature.pool_path')
        
        if project_path:
            process_data_folder = project_path
        else:
            # 为每个项目创建唯一目录
            safe_name = re.sub(r'[<>:"/\\|?*]', '', project_name or 'unnamed').strip()
            process_data_folder = os.path.join("data", "projects", safe_name)
            os.makedirs(process_data_folder, exist_ok=True)
            
        # 创建sections目录用于存储分章节MD
        sections_folder = os.path.join(process_data_folder, "sections", "v1")
        os.makedirs(sections_folder, exist_ok=True)
            
        # 最终成果：在根目录 output 文件夹下
        output_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        os.makedirs(output_folder, exist_ok=True)
        logger.info(f"最终输出目录: {output_folder}")
        logger.info(f"章节文件目录: {sections_folder}")
        
        # 1. 加载文献池
        logger.info(f"步骤1: 加载文献池: {lit_pool_path}")
        parser = LiteratureParser()
        literature_pool = parser.parse_txt_pool(lit_pool_path)
        logger.info(f"文献池加载完成: {len(literature_pool)} 条文献")
        report_progress(15, "构建语义检索引擎")
        
        # 2. 构建语义检索引擎
        logger.info("步骤2: 构建语义检索引擎...")
        retriever = SemanticRetriever(literature_pool)
        report_progress(20, "初始化大模型路由")
        
        # 3. 初始化大模型路由
        logger.info("步骤3: 初始化大模型路由...")
        router = ModelRouter(config)
        
        # 4. 初始化引用管理器
        logger.info("步骤4: 初始化引用管理器...")
        citation_mgr = CitationManager(literature_pool, retriever, config, model_router=router)
        
        # 5. 准备项目上下文
        project_context = {
            'title': project_name,
            'keywords': config.get('project.keywords', ''),
            'extra_idea': extra_idea,
            'output_folder': process_data_folder,
            'sections_folder': sections_folder,
            'outline_data': outline_data  # 传递用户编辑的大纲
        }
        
        # 6. 初始化模板引擎
        logger.info("步骤5: 加载模板...")
        engine = TemplateEngine(
            template_path=config.get('template.path'),
            model_router=router,
            citation_manager=citation_mgr,
            project_context=project_context,
            config=config
        )
        report_progress(25, "生成论文初稿")
        
        # 7. 生成论文初稿
        logger.info("步骤6: 生成论文初稿...")
        paper_draft = engine.generate_paper(progress_callback=progress_callback)
        
        # 强制添加标题
        if not paper_draft.strip().startswith('# '):
            paper_draft = f"# {project_name}\n\n{paper_draft}"

        # 保存初稿
        safe_filename = re.sub(r'[<>:"/\\|?*]', '', project_name).strip()
        output_path_draft = os.path.join(output_folder, f'{safe_filename}_初稿版.md')
        with open(output_path_draft, 'w', encoding='utf-8') as f:
            f.write(paper_draft)
        logger.info(f"初稿版已保存: {output_path_draft}")
        report_progress(70, "专家审稿优化", word_count=len(paper_draft))
        
        # 8. 专家审稿与优化（如果启用）
        final_paper = paper_draft
        review_results = None
        
        if config.get('expert_review.enabled', False):
            logger.info("\n" + "="*60)
            logger.info("步骤7: 专家审稿系统介入...")
            expert_system = ExpertReviewSystem(
                router,
                output_dir=process_data_folder,
                web_search=engine.web_search,
                max_rounds=config.get('expert_review.max_rounds', 3),
                target_score=config.get('expert_review.target_score', 80)
            )
            review_results = expert_system.review_and_optimize_iteratively(paper_draft)
            
            final_paper = review_results['final_paper']
            
            # 保存审稿报告
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
            logger.info("步骤7: 专家审稿未启用，跳过")
        
        # 9. V2: 逐章节优化（清理AI痕迹）- 标准版
        logger.info("\n" + "="*60)
        logger.info("步骤8: 生成标准版（清理AI痕迹、规范正文）...")
        optimized_paper = engine.optimize_paper_sections(final_paper)
        report_progress(85, "生成扩写版", word_count=len(optimized_paper))
        
        # 保存标准版MD
        output_path_std = os.path.join(output_folder, f'{safe_filename}_标准版.md')
        with open(output_path_std, 'w', encoding='utf-8') as f:
            f.write(optimized_paper)
        
        # 导出标准版Word
        docx_path_std = os.path.join(output_folder, f'{safe_filename}_标准版.docx')
        try:
            from core.docx_exporter import convert_markdown_to_docx
            convert_markdown_to_docx(optimized_paper, docx_path_std)
            logger.info(f"标准版Word已导出: {docx_path_std}")
        except Exception as e:
            logger.error(f"导出标准版Word失败: {str(e)}")
            docx_path_std = output_path_std

        # 10. V3: 逐章节扩写 - 扩写版
        logger.info("\n" + "="*60)
        logger.info("步骤9: 生成扩写版（内容丰富化）...")
        expanded_paper = engine.expand_paper_sections(optimized_paper)
        
        # 保存扩写版MD
        output_path_exp = os.path.join(output_folder, f'{safe_filename}_扩写版.md')
        with open(output_path_exp, 'w', encoding='utf-8') as f:
            f.write(expanded_paper)
        
        # 导出扩写版Word
        docx_path_exp = os.path.join(output_folder, f'{safe_filename}_扩写版.docx')
        try:
            convert_markdown_to_docx(expanded_paper, docx_path_exp)
            logger.info(f"扩写版Word已导出: {docx_path_exp}")
        except Exception as e:
            logger.error(f"导出扩写版Word失败: {str(e)}")
            docx_path_exp = output_path_exp
        
        report_progress(95, "生成质量报告", word_count=len(expanded_paper))
        
        # 11. 生成质量报告
        if config.get('quality_metrics.enabled'):
            stats = citation_mgr.get_statistics()
            stats['output_file'] = output_path_exp
            stats['word_count_draft'] = len(paper_draft)
            stats['word_count_std'] = len(optimized_paper)
            stats['word_count_exp'] = len(expanded_paper)
            stats['expert_review_enabled'] = config.get('expert_review.enabled', False)
            stats['project_path'] = process_data_folder
            
            report_path = os.path.join(output_folder, 'quality_report.json')
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            
            logger.info(f"质量报告已生成: {report_path}")
        
        logger.info("="*60)
        logger.info("论文生成全流程完成!")
        logger.info(f"标准版: {docx_path_std}")
        logger.info(f"扩写版: {docx_path_exp}")
        logger.info("="*60)
        
        return {
            'success': True,
            '标准版': docx_path_std,
            '扩写版': docx_path_exp,
            'output_folder': output_folder,
            'message': '论文生成全流程完成'
        }
        
    except KeyboardInterrupt:
        logger.info("用户中断程序")
        return {
            'success': False,
            'error': '用户中断程序',
            'cancelled': True
        }
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}", exc_info=True)
        raise e

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='自动化论文生成')
    parser.add_argument('--project', type=str, help='项目名称')
    parser.add_argument('--literature', type=str, help='文献池TXT文件路径')
    parser.add_argument('--idea', type=str, help='核心思路')
    
    args = parser.parse_args()
    
    main(
        project_name=args.project,
        literature_txt_path=args.literature,
        extra_idea=args.idea
    )
