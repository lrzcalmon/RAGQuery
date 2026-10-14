# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec para RAGQuery.
Gera executável standalone que empacota Flask + parser + query engine.
"""
import os
import sys
from pathlib import Path

block_cipher = None

PROJECT_ROOT = os.path.abspath(os.path.join(SPECPATH, '..'))

import importlib.util

# Localizar llama_cpp DLLs automaticamente
llama_binaries = []
llama_datas = []
_llama_spec = importlib.util.find_spec('llama_cpp')
if _llama_spec and _llama_spec.origin:
    _llama_dir = os.path.dirname(_llama_spec.origin)
    _lib_dir = os.path.join(_llama_dir, 'lib')
    if os.path.isdir(_lib_dir):
        for f in os.listdir(_lib_dir):
            if f.endswith(('.dll', '.so', '.dylib')):
                llama_binaries.append((os.path.join(_lib_dir, f), os.path.join('llama_cpp', 'lib')))
        llama_datas.append((_lib_dir, os.path.join('llama_cpp', 'lib')))

a = Analysis(
    [os.path.join(PROJECT_ROOT, 'launcher.py')],
    pathex=[PROJECT_ROOT],
    binaries=llama_binaries,
    datas=[
        # Templates e static files do Flask
        (os.path.join(PROJECT_ROOT, 'src', 'web', 'templates'), os.path.join('src', 'web', 'templates')),
        (os.path.join(PROJECT_ROOT, 'src', 'web', 'static'), os.path.join('src', 'web', 'static')),
        # Scripts (ingest é usado pelo launcher)
        (os.path.join(PROJECT_ROOT, 'scripts'), 'scripts'),
    ] + llama_datas,
    hiddenimports=[
        'src',
        'src.config',
        'src.ddl_parser',
        'src.ddl_parser.models',
        'src.ddl_parser.ddl_splitter',
        'src.ddl_parser.oracle_parser',
        'src.metadata_store',
        'src.metadata_store.schema',
        'src.metadata_store.db_manager',
        'src.metadata_store.queries',
        'src.query_engine',
        'src.query_engine.intent_classifier',
        'src.query_engine.sql_generator',
        'src.query_engine.response_builder',
        'src.llm',
        'src.llm.llm_manager',
        'src.llm.prompts',
        'src.web',
        'src.web.app',
        'src.web.routes',
        'scripts.ingest',
        'llama_cpp',
        'llama_cpp.llama',
        'llama_cpp.llama_types',
        'llama_cpp.llama_grammar',
        'llama_cpp.llama_chat_format',
        'numpy',
        'flask',
        'flask_cors',
        'jinja2',
        'markupsafe',
        'werkzeug',
        'chardet',
        'pydantic',
        'pydantic_core',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'pandas',
        'scipy',
        'torch',
        'sentence_transformers',
        'chromadb',
        'PySide6',
        'PyQt5',
        'PyQt6',
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
    [],
    exclude_binaries=True,
    name='RAGQuery',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Console visível para logs
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(PROJECT_ROOT, 'installer', 'ragquery.ico') if os.path.exists(os.path.join(PROJECT_ROOT, 'installer', 'ragquery.ico')) else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RAGQuery',
)
