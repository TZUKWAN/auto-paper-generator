"""项目级文献池管理器"""
import os
import shutil
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ProjectLiteratureManager:
    """项目级文献池管理器"""
    
    def __init__(self, base_dir="data/projects"):
        """
        初始化项目文献池管理器
        
        Args:
            base_dir: 项目基础目录
        """
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
        logger.info(f"项目文献池管理器初始化: {base_dir}")
    
    def create_project(self, project_name):
        """
        创建新项目文件夹
        
        Args:
            project_name: 项目名称
            
        Returns:
            项目路径
        """
        # 生成项目ID（时间戳+项目名）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        project_id = f"{timestamp}_{self._sanitize_filename(project_name)}"
        
        project_path = os.path.join(self.base_dir, project_id)
        os.makedirs(project_path, exist_ok=True)
        
        # 创建子文件夹
        os.makedirs(os.path.join(project_path, "literature"), exist_ok=True)
        os.makedirs(os.path.join(project_path, "pdfs"), exist_ok=True)
        os.makedirs(os.path.join(project_path, "output"), exist_ok=True)
        
        logger.info(f"创建项目: {project_id}")
        return project_path
    
    def save_literature_txt(self, project_path, uploaded_file_path):
        """
        保存上传的文献池TXT文件
        
        Args:
            project_path: 项目路径
            uploaded_file_path: 上传的文件路径
            
        Returns:
            标准化后的文件路径
        """
        literature_dir = os.path.join(project_path, "literature")
        
        # 统一命名为 literature_pool.txt
        target_path = os.path.join(literature_dir, "literature_pool.txt")
        
        # 复制文件
        shutil.copy2(uploaded_file_path, target_path)
        
        logger.info(f"文献池已保存: {target_path}")
        return target_path
    
    def get_literature_pool_path(self, project_path):
        """获取项目的文献池路径"""
        return os.path.join(project_path, "literature", "literature_pool.txt")
    
    def get_pdf_folder_path(self, project_path):
        """获取项目的PDF文件夹路径"""
        return os.path.join(project_path, "pdfs")
    
    def get_output_folder_path(self, project_path):
        """获取项目的输出文件夹路径"""
        return os.path.join(project_path, "output")
    
    def list_projects(self):
        """列出所有项目"""
        projects = []
        
        if not os.path.exists(self.base_dir):
            return projects
        
        for item in os.listdir(self.base_dir):
            item_path = os.path.join(self.base_dir, item)
            if os.path.isdir(item_path):
                projects.append({
                    'id': item,
                    'path': item_path,
                    'created': os.path.getctime(item_path)
                })
        
        # 按创建时间倒序
        projects.sort(key=lambda x: x['created'], reverse=True)
        
        return projects
    
    def _sanitize_filename(self, filename):
        """清理文件名，移除非法字符"""
        # 替换非法字符为下划线
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # 限制长度
        return filename[:50]
