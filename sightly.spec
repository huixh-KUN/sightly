# -*- mode: python ; coding: utf-8 -*-

import sys
import os

sys.setrecursionlimit(5000)

block_cipher = None

project_root = os.getcwd()

a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=[],
    datas=[
        ('voice/*.mp3', 'voice'),
        ('icon/*.ico', 'icon'),
        ('icon/*.png', 'icon'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtMultimedia',
        'core',
        'ui',
        'modules',
        'input',
        'utils',
        'config',
        'rapidocr_onnxruntime',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'turtle',
        'test',
        'unittest',
        'setuptools',
        'pip',
        'email',
        'html',
        'http',
        'xml',
        'xmlrpc',
        'pdb',
        'doctest',
        'pydoc',
        'asyncio',
        'multiprocessing',
        'concurrent',
        'PyQt5',
        'scipy',
        'matplotlib',
        'pandas',
        'tensorflow',
        'torch',
        'torchvision',
        'Cython',
        'IPython',
        'jupyter',
        'jedi',
        'parso',
        'zmq',
        'notebook',
        'qtconsole',
        'sphinx',
        'wheel',
        'twine',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Sightly',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon/sightly.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Sightly',
)
