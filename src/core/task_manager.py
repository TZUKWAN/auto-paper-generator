# -*- coding: utf-8 -*-
"""
任务管理器
管理任务的创建、编辑、删除和执行
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from uuid import uuid4
import json

from src.core.logger import get_logger


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "待处理"
    IN_PROGRESS = "执行中"
    COMPLETED = "已完成"
    FAILED = "失败"
    CANCELLED = "已取消"


class Task:
    """任务类"""

    def __init__(self, task_id: str = None, title: str = "", description: str = "",
                 task_type: str = "generation", params: Dict = None):
        """
        初始化任务
        
        Args:
            task_id: 任务ID
            title: 任务标题
            description: 任务描述
            task_type: 任务类型
            params: 任务参数
        """
        self.task_id = task_id or str(uuid4())
        self.title = title
        self.description = description
        self.task_type = task_type
        self.params = params or {}
        self.status = TaskStatus.PENDING
        self.progress = 0
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.result = None
        self.error = None

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'task_id': self.task_id,
            'title': self.title,
            'description': self.description,
            'task_type': self.task_type,
            'params': self.params,
            'status': self.status.value,
            'progress': self.progress,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result': self.result,
            'error': self.error
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Task':
        """从字典创建任务"""
        task = cls(
            task_id=data.get('task_id'),
            title=data.get('title', ''),
            description=data.get('description', ''),
            task_type=data.get('task_type', 'generation'),
            params=data.get('params', {})
        )
        task.status = TaskStatus(data.get('status', TaskStatus.PENDING.value))
        task.progress = data.get('progress', 0)
        if data.get('created_at'):
            task.created_at = datetime.fromisoformat(data['created_at'])
        if data.get('started_at'):
            task.started_at = datetime.fromisoformat(data['started_at'])
        if data.get('completed_at'):
            task.completed_at = datetime.fromisoformat(data['completed_at'])
        task.result = data.get('result')
        task.error = data.get('error')
        return task


class TaskManager:
    """任务管理器"""

    def __init__(self):
        """初始化任务管理器"""
        self.logger = get_logger()
        self.tasks: Dict[str, Task] = {}
        self.task_queue: List[str] = []
        self.current_task_id: Optional[str] = None

    def create_task(self, title: str, description: str = "", task_type: str = "generation",
                    params: Dict = None) -> str:
        """
        创建新任务
        
        Args:
            title: 任务标题
            description: 任务描述
            task_type: 任务类型
            params: 任务参数
            
        Returns:
            任务ID
        """
        task = Task(title=title, description=description, 
                   task_type=task_type, params=params)
        self.tasks[task.task_id] = task
        self.task_queue.append(task.task_id)
        
        self.logger.info(f"创建任务: {title} (ID: {task.task_id})")
        return task.task_id

    def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            Task对象或None
        """
        return self.tasks.get(task_id)

    def update_task_status(self, task_id: str, status: TaskStatus, 
                           progress: int = None, error: str = None) -> bool:
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
            progress: 进度百分比
            error: 错误信息
            
        Returns:
            更新成功返回True
        """
        task = self.get_task(task_id)
        if not task:
            self.logger.warning(f"任务不存在: {task_id}")
            return False
        
        task.status = status
        
        if progress is not None:
            task.progress = progress
        
        if error:
            task.error = error
        
        if status == TaskStatus.IN_PROGRESS and not task.started_at:
            task.started_at = datetime.now()
        
        if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            task.completed_at = datetime.now()
            if self.current_task_id == task_id:
                self.current_task_id = None
        
        self.logger.debug(f"任务状态更新: {task_id} -> {status.value}")
        return True

    def update_task_progress(self, task_id: str, progress: int, message: str = None) -> bool:
        """
        更新任务进度
        
        Args:
            task_id: 任务ID
            progress: 进度百分比 (0-100)
            message: 进度消息
            
        Returns:
            更新成功返回True
        """
        task = self.get_task(task_id)
        if not task:
            return False
        
        task.progress = max(0, min(100, progress))
        
        if progress > 0 and task.status == TaskStatus.PENDING:
            self.update_task_status(task_id, TaskStatus.IN_PROGRESS)
        
        if progress >= 100:
            self.update_task_status(task_id, TaskStatus.COMPLETED)
        
        return True

    def set_task_result(self, task_id: str, result: Any) -> bool:
        """
        设置任务结果
        
        Args:
            task_id: 任务ID
            result: 任务结果
            
        Returns:
            设置成功返回True
        """
        task = self.get_task(task_id)
        if not task:
            return False
        
        task.result = result
        self.update_task_status(task_id, TaskStatus.COMPLETED, progress=100)
        
        return True

    def delete_task(self, task_id: str) -> bool:
        """
        删除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            删除成功返回True
        """
        if task_id in self.tasks:
            del self.tasks[task_id]
            if task_id in self.task_queue:
                self.task_queue.remove(task_id)
            self.logger.info(f"删除任务: {task_id}")
            return True
        return False

    def get_all_tasks(self, status: TaskStatus = None) -> List[Task]:
        """
        获取所有任务
        
        Args:
            status: 过滤状态，None表示不过滤
            
        Returns:
            任务列表
        """
        tasks = list(self.tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)

    def get_pending_tasks(self) -> List[Task]:
        """获取待处理任务"""
        return self.get_all_tasks(TaskStatus.PENDING)

    def get_in_progress_tasks(self) -> List[Task]:
        """获取执行中任务"""
        return self.get_all_tasks(TaskStatus.IN_PROGRESS)

    def clear_completed_tasks(self) -> int:
        """清除已完成的任务"""
        count = 0
        for task_id in list(self.tasks.keys()):
            if self.tasks[task_id].status == TaskStatus.COMPLETED:
                self.delete_task(task_id)
                count += 1
        self.logger.info(f"清除了 {count} 个已完成任务")
        return count

    def get_task_count(self, status: TaskStatus = None) -> int:
        """
        获取任务数量
        
        Args:
            status: 过滤状态，None表示全部
            
        Returns:
            任务数量
        """
        tasks = self.get_all_tasks(status)
        return len(tasks)

    def save_to_file(self, filepath: str) -> bool:
        """
        保存任务到文件
        
        Args:
            filepath: 文件路径
            
        Returns:
            保存成功返回True
        """
        try:
            data = [task.to_dict() for task in self.tasks.values()]
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"任务已保存到: {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"保存任务失败: {e}")
            return False

    def load_from_file(self, filepath: str) -> bool:
        """
        从文件加载任务
        
        Args:
            filepath: 文件路径
            
        Returns:
            加载成功返回True
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.tasks = {}
            for task_data in data:
                task = Task.from_dict(task_data)
                self.tasks[task.task_id] = task
            
            self.logger.info(f"从文件加载了 {len(self.tasks)} 个任务")
            return True
        except Exception as e:
            self.logger.error(f"加载任务失败: {e}")
            return False


# 全局任务管理器实例
_global_task_manager = None


def get_task_manager() -> TaskManager:
    """获取全局任务管理器实例"""
    global _global_task_manager
    if _global_task_manager is None:
        _global_task_manager = TaskManager()
    return _global_task_manager
