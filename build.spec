# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File for AI Academic Assistant
构建命令: pyinstaller build.spec
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 项目根目录
project_dir = os.path.dirname(os.path.abspath(SPEC))

# 收集 sentence_transformers 数据
sentence_transformers_datas = collect_data_files('sentence_transformers')

# 隐式导入
hidden_imports = [
    'sentence_transformers',
    'torch',
    'transformers',
    'huggingface_hub',
    'tokenizers',
    'safetensors',
    'faiss',
    'numpy',
    'pandas',
    'yaml',
    'requests',
    'PIL',
    'docx',
    'markdown',
    'bs4',
    'httpx',
    'tqdm',
    'loguru',
    'wx',
    'wx.adv',
    'wx.lib.newevent',
    'matplotlib',
    'seaborn',
    'statsmodels',
]

# 需要打包的数据文件
datas = [
    ('config.yaml', '.'),
    ('templates', 'templates'),
    ('assets', 'assets'),
    ('.env.example', '.'),
]
datas.extend(sentence_transformers_datas)

# 分析入口
a = Analysis(
    ['wx_gui.py'],
    pathex=[project_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'test',
        'tests',
        'IPython',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

# 精简不必要的文件
a.binaries = [x for x in a.binaries if not x[0].startswith('api-ms-')]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AI学术助手',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 无控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AI学术助手',
)
