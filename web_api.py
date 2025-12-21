"""简易Web API服务器 - 支持UI界面、文献池上传和论文生成"""
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import os
import time
import logging
import threading
import uuid
import queue
from datetime import datetime
from main import main as generate_paper_main
from core.project_manager import ProjectLiteratureManager

# 自定义日志处理器，用于将日志输出到内存队列，供前端轮询
class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        try:
            msg = self.format(record)
            self.log_queue.put(msg)
        except Exception:
            self.handleError(record)

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# 基础配置
logging.basicConfig(level=logging.INFO)
system_logger = logging.getLogger(__name__)

TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

proj_mgr = ProjectLiteratureManager("data/projects")

# 全局任务存储 {task_id: task_info}
tasks = {}

def run_generation_task(task_id, project_name, literature_txt_path, pdf_folder_path):
    """后台运行生成任务"""
    task = tasks[task_id]
    log_queue = task['log_queue']
    
    # 设置根日志记录器以捕获所有模块的日志
    root_logger = logging.getLogger()
    queue_handler = QueueHandler(log_queue)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    queue_handler.setFormatter(formatter)
    root_logger.addHandler(queue_handler)
    
    try:
        task['status'] = 'running'
        task['logs'].append(f"任务开始: {project_name}")
        
        # 调用主程序
        output_path = generate_paper_main(
            project_name=project_name,
            literature_txt_path=literature_txt_path,
            pdf_folder_path=pdf_folder_path
        )
        
        # 获取项目ID（假设是最新的一个）
        projects = proj_mgr.list_projects()
        current_project = next((p for p in projects if project_name in p['id']), projects[0] if projects else None)
        
        task['status'] = 'completed'
        task['output_result'] = output_path  # Now a dict
        task['project_id'] = current_project['id'] if current_project else None
        task['logs'].append("任务完成！")
        
    except Exception as e:
        task['status'] = 'failed'
        task['error'] = str(e)
        task['logs'].append(f"任务出错: {str(e)}")
        system_logger.error(f"Task {task_id} failed: {e}", exc_info=True)
    finally:
        # 清理handler
        root_logger.removeHandler(queue_handler)

@app.route('/')
def index():
    """返回前端主页"""
    return send_from_directory('static', 'index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'})

@app.route('/api/projects/create', methods=['POST'])
def create_project_api():
    """创建新项目"""
    try:
        data = request.json
        title = data.get('title')
        if not title:
            return jsonify({'success': False, 'error': 'Title required'}), 400
        
        project_path = proj_mgr.create_project(title)
        project_id = os.path.basename(project_path)
        
        # 可以选择保存idea到文件
        
        return jsonify({
            'success': True, 
            'project_id': project_id,
            'project_path': project_path
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/projects/<project_id>/upload', methods=['POST'])
def upload_to_project(project_id):
    """上传文件到指定项目"""
    try:
        project_path = os.path.join(proj_mgr.base_dir, project_id)
        if not os.path.exists(project_path):
            return jsonify({'success': False, 'error': 'Project not found'}), 404

        uploaded = []
        
        # 处理文献池TXT
        if 'literature_file' in request.files:
            file = request.files['literature_file']
            if file.filename:
                # 存到 literature/literature_pool.txt
                # 直接保存到目标位置
                target_path = os.path.join(project_path, "literature", "literature_pool.txt")
                file.save(target_path)
                uploaded.append("literature_pool.txt")

        # 处理PDF
        if 'pdf_files' in request.files:
            files = request.files.getlist('pdf_files')
            pdf_dir = proj_mgr.get_pdf_folder_path(project_path)
            for file in files:
                if file.filename:
                    file.save(os.path.join(pdf_dir, file.filename))
                    uploaded.append(file.filename)
                    
        return jsonify({'success': True, 'message': f"Uploaded {len(uploaded)} files"})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def run_gen_task(task_id, project_id, extra_idea):
    task = tasks[task_id]
    log_queue = task['log_queue']
    root_logger = logging.getLogger()
    queue_handler = QueueHandler(log_queue)
    root_logger.addHandler(queue_handler)
    
    try:
        task['status'] = 'running'
        task['logs'].append(f"启动生成任务: {project_id}")
        
        # 强制重新加载配置文件，确保获取最新的模型模式设置
        from config import config
        config._config = config._load_config()
        task['logs'].append(f"当前模型模式: {config.get('model_routing.default')}")
        
        # 获取项目特定的绝对路径
        project_path = os.path.join(proj_mgr.base_dir, project_id)
        
        # 1. 明确指定文献池路径
        uploaded_pool = os.path.join(project_path, "literature", "literature_pool.txt")
        if os.path.exists(uploaded_pool):
            lit_path = uploaded_pool
        else:
            # 即使不存在也传这个路径（让main去处理"纯网络模式"）
            # 或者传None让main处理? main如果不传会用默认。
            # 为了避免用默认，如果文件不存在，应该传None? 
            # 不，main里如果传了path但文件不存在，LiteratureParser会返回空列表（符合预期）
            # 但如果传None，main可能会去读config.yaml里的默认路径
            lit_path = uploaded_pool

        # 2. 明确指定PDF路径
        project_pdf_dir = os.path.join(project_path, "pdfs")
        # 确保PDF目录存在
        if not os.path.exists(project_pdf_dir):
            os.makedirs(project_pdf_dir)
        pdf_path = project_pdf_dir

        # 3. 强制确保配置已更新（如果main重新加载config）
        # 在这里再次尝试重新应用一下当前内存里的配置到环境变量，作为双重保险
        from config import config
        if config.get('model_routing.default') == 'lmstudio':
             pass # 已经是一个内存对象了
        
        # 调用main
        output_path = generate_paper_main(
            project_name=project_id,
            literature_txt_path=lit_path,
            pdf_folder_path=pdf_path,
            extra_idea=extra_idea
        )
        
        task['status'] = 'completed'
        task['output_result'] = output_path # Now a dict
        task['project_id'] = project_id
        task['logs'].append("任务完成！")
    except Exception as e:
        task['status'] = 'failed'
        task['error'] = str(e)
        system_logger.error(f"Task failed: {e}", exc_info=True)
    finally:
        root_logger.removeHandler(queue_handler)

@app.route('/api/generate_ex', methods=['POST'])
def generate_ex():
    """新版生成接口"""
    data = request.json
    project_id = data.get('project_id')
    extra_idea = data.get('extra_idea')
    
    task_id = str(uuid.uuid4())
    log_queue = queue.Queue()
    tasks[task_id] = {
        'id': task_id,
        'status': 'pending', 
        'logs': [], 
        'log_queue': log_queue,
        'created_at': datetime.now().isoformat()
    }
    
    t = threading.Thread(target=run_gen_task, args=(task_id, project_id, extra_idea))
    t.daemon = True
    t.start()
    
    return jsonify({'success': True, 'task_id': task_id})


@app.route('/api/task_status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """获取任务状态和新日志"""
    task = tasks.get(task_id)
    if not task:
        return jsonify({'success': False, 'error': '任务不存在'}), 404
        
    # 从队列读取新日志并追加到logs列表
    new_logs = []
    try:
        while True:
            msg = task['log_queue'].get_nowait()
            task['logs'].append(msg)
            new_logs.append(msg)
    except queue.Empty:
        pass
    
    return jsonify({
        'success': True,
        'status': task['status'],
        'logs': task['logs'],  # 返回所有日志或增量日志，前端可以处理
        'project_id': task.get('project_id'),
        'output_result': task.get('output_result'), # Pass full result dict
        'error': task.get('error')
    })

@app.route('/api/download/<project_id>/<filename>', methods=['GET'])
def download_file(project_id, filename):
    try:
        project_path = os.path.join(proj_mgr.base_dir, project_id)
        file_path = os.path.join(project_path, "output", filename)
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': '文件不存在'}), 404
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/open_folder/<project_id>', methods=['GET'])
def open_folder(project_id):
    """在资源管理器中打开文件夹"""
    try:
        project_path = os.path.join(proj_mgr.base_dir, project_id, "output")
        os.startfile(project_path)  # 仅Windows有效
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/config/all', methods=['GET'])
def get_all_config():
    """获取所有配置"""
    try:
        from config import config
        return jsonify({
            'success': True,
            'config': {
                'default_mode': config.get('model_routing.default'),
                'silicon': {
                    'model': config.get('model_routing.silicon.model'),
                    'max_tokens': config.get('model_routing.silicon.max_tokens'),
                    'temperature': config.get('model_routing.silicon.temperature'),
                    'enable_thinking': config.get('model_routing.silicon.enable_thinking'),
                    'thinking_budget': config.get('model_routing.silicon.thinking_budget')
                },
                'lmstudio': {
                    'base_url': config.get('model_routing.lmstudio.base_url'),
                    'model': config.get('model_routing.lmstudio.model')
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/config/update', methods=['POST'])
def update_config():
    """更新配置"""
    try:
        data = request.json
        from config import config
        
        # 1. 更新模式
        if 'mode' in data:
            config._config['model_routing']['default'] = data['mode']
        
        # 3. 更新Silicon Flow
        silicon = config._config['model_routing']['silicon']
        if 'api_key' in data and data['api_key']:
            os.environ['SILICON_API_KEY'] = data['api_key']
            silicon['api_key'] = data['api_key']  # 关键修复：保存到配置对象以便持久化到文件
            
        if 'silicon_model' in data: silicon['model'] = data['silicon_model']
        if 'thinking_budget' in data: silicon['thinking_budget'] = data['thinking_budget']
        if 'enable_thinking' in data: silicon['enable_thinking'] = data['enable_thinking']
        if 'temperature' in data: silicon['temperature'] = data['temperature']
        if 'max_tokens' in data: silicon['max_tokens'] = data['max_tokens']
        
        # 4. 更新LM Studio
        lmstudio = config._config['model_routing']['lmstudio']
        if 'local_url' in data: lmstudio['base_url'] = data['local_url']
        if 'local_model' in data: lmstudio['model'] = data['local_model']
        
        # 保存到文件
        config.save()
        
        system_logger.info(f"配置已更新并保存: {data}")
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print(f"WEB UI服务启动: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, threaded=True)

