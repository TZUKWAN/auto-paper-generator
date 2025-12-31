"""
STARTSYSTEM.py - 项目启动器
功能：
1. 自动检测并杀死所有本项目的旧进程
2. 启动本项目GUI
"""
import subprocess
import os
import sys
import psutil
import time

# 项目标识 - 用于识别本项目的进程
PROJECT_MARKERS = [
    'wx_gui.py',
    'main.py',
    '自动化论文纯线上'
]

def find_project_processes():
    """查找所有本项目相关的Python进程"""
    project_pids = []
    current_pid = os.getpid()
    
    # 获取当前进程的父进程链，这些都不能杀
    protected_pids = {current_pid}
    try:
        current_proc = psutil.Process(current_pid)
        for parent in current_proc.parents():
            protected_pids.add(parent.pid)
    except:
        pass
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # 跳过受保护的进程（当前进程及其父进程链）
            if proc.info['pid'] in protected_pids:
                continue
            
            # 检查是否是Python进程
            if 'python' not in proc.info['name'].lower():
                continue
            
            # 检查命令行参数中是否包含项目标识
            cmdline = proc.info['cmdline']
            if cmdline:
                cmdline_str = ' '.join(cmdline)
                
                # 跳过启动器自己
                if 'STARTSYSTEM' in cmdline_str:
                    continue
                
                for marker in PROJECT_MARKERS:
                    if marker in cmdline_str:
                        project_pids.append({
                            'pid': proc.info['pid'],
                            'cmdline': cmdline_str[:100]
                        })
                        break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    return project_pids

def kill_processes(processes):
    """杀死指定的进程列表"""
    killed = 0
    for proc_info in processes:
        try:
            proc = psutil.Process(proc_info['pid'])
            print(f"  正在终止进程 PID={proc_info['pid']}: {proc_info['cmdline'][:60]}...")
            proc.terminate()
            proc.wait(timeout=3)
            killed += 1
            print(f"    ✅ 已终止")
        except psutil.NoSuchProcess:
            print(f"    ⚠️ 进程已不存在")
        except psutil.TimeoutExpired:
            try:
                print(f"    ⚠️ 进程未响应，强制结束...")
                proc.kill()
                killed += 1
            except:
                print(f"    ❌ 无法终止")
        except Exception as e:
            print(f"    ❌ 终止失败: {e}")
    
    return killed

def start_project():
    """启动项目GUI"""
    project_dir = os.path.dirname(os.path.abspath(__file__))
    gui_script = os.path.join(project_dir, 'wx_gui.py')
    
    if not os.path.exists(gui_script):
        print(f"❌ 找不到GUI脚本: {gui_script}")
        return False
    
    print(f"\n🚀 启动项目...")
    print(f"   目录: {project_dir}")
    print(f"   脚本: wx_gui.py")
    
    # 使用subprocess启动，不等待
    try:
        # Windows下使用pythonw避免控制台窗口
        python_exe = sys.executable
        if sys.platform == 'win32':
            pythonw = python_exe.replace('python.exe', 'pythonw.exe')
            if os.path.exists(pythonw):
                python_exe = pythonw
        
        subprocess.Popen(
            [python_exe, gui_script],
            cwd=project_dir,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
        )
        print("   ✅ 项目已启动")
        return True
    except Exception as e:
        print(f"   ❌ 启动失败: {e}")
        return False

def main():
    print("=" * 50)
    print("    AI论文生成系统 - 启动器")
    print("=" * 50)
    
    # 第一步：查找旧进程
    print("\n📋 步骤1: 检查运行中的项目进程...")
    old_processes = find_project_processes()
    
    if old_processes:
        print(f"   发现 {len(old_processes)} 个项目进程:")
        for p in old_processes:
            print(f"   - PID {p['pid']}: {p['cmdline'][:60]}...")
        
        # 第二步：杀死旧进程
        print("\n🔄 步骤2: 终止旧进程...")
        killed = kill_processes(old_processes)
        print(f"   已终止 {killed} 个进程")
        
        # 等待进程完全退出
        time.sleep(1)
    else:
        print("   没有发现运行中的项目进程")
    
    # 第三步：启动项目
    print("\n🚀 步骤3: 启动项目...")
    success = start_project()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ 项目启动完成！")
    else:
        print("❌ 项目启动失败，请检查错误信息")
    print("=" * 50)
    
    # 等待用户确认
    if sys.platform == 'win32':
        input("\n按回车键退出...")

if __name__ == "__main__":
    main()
