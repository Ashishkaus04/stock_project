# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# Add src directory to Python path
src_path = os.path.abspath(os.path.join(os.path.abspath('.'), 'src'))
sys.path.insert(0, src_path)

a = Analysis(
    ['run.py'],
    pathex=[src_path],  # Add src directory to path
    binaries=[],
    datas=[
        ('src/app', 'app'),
        ('src/app/database', 'app/database'),  # Include entire database directory
        ('static', 'static'),
        ('C:\\Users\\DELL\\AppData\\Local\\Programs\\Python\\Python313\\tcl', 'tcl')
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'tkcalendar',
        'requests',
        'subprocess',
        'sys',
        'os',
        'tempfile',
        'json',
        'shutil',
        'datetime',
        'csv',
        'psycopg',
        'psycopg2',
        'flask',
        'flask_sqlalchemy',
        'flask_migrate',
        'dotenv',
        'python-dotenv',
        'flask_cors',
        'werkzeug.security',
        'sqlalchemy.exc',
        'waitress',
        'app.api.app',
        'app.main',
        'app.ui',
        'app.database',
        'app.database.db',
        'app.database.migrate_data',
        'app.database.upload_to_cloud',
        'bcrypt'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='run',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Set to True temporarily for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='run',
)
