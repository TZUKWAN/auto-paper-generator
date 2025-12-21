
import sys
import os

# 确保能找到模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import main

project_name = "20251220_203641_红色文化中的生态基因传承与中国式现代化生态观建构研究"
lit_path = r"D:\自动化商业计划书脚本\自动化论文脚本\data\projects\20251220_203641_红色文化中的生态基因传承与中国式现代化生态观建构研究\literature\literature_pool.txt"

idea = """首先，梳理红色文化的核心内涵，挖掘其中蕴含的生态智慧（如革命时期的资源节约理念、人与自然共生的实践经验、人民至上理念与生态惠民的内在契合性等），界定红色生态基因的核心范畴。其次，解析中国式现代化生态观的理论框架与时代特征，明确其“人与自然和谐共生”的核心要义及实践要求。再次，重点分析红色生态基因与中国式现代化生态观的内在契合点，论证前者对后者的理论滋养与文化支撑作用。最后，结合当代生态治理实践案例，探讨如何激活红色生态基因，为中国式现代化生态观的落地提供文化赋能路径，并提出规避传承异化的对策建议。"""

print(f"准备运行项目: {project_name}")
print(f"文献池路径: {lit_path}")
print(f"核心思路长: {len(idea)} 字符")
print("-" * 50)

try:
    main(
        project_name=project_name, 
        literature_txt_path=lit_path, 
        extra_idea=idea
    )
    print("生成任务执行完成")
except Exception as e:
    print(f"执行出错: {str(e)}")
    import traceback
    traceback.print_exc()
