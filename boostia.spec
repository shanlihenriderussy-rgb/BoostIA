# -*- mode: python ; coding: utf-8 -*-
# Spec PyInstaller pour BoostIA - .exe autonome Windows.

block_cipher = None

a = Analysis(
    ['app/launcher.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('web', 'web'),
        ('app', 'app'),
    ],
    hiddenimports=[
        # Core
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        # FastAPI / Starlette / pydantic
        'fastapi',
        'starlette',
        'pydantic',
        'pydantic_settings',
        'pydantic.deprecated.decorator',
        # HTTP client
        'httpx',
        'httpcore',
        'h11',
        'anyio',
        'sniffio',
        # Logging
        'structlog',
        # Modules app
        'app',
        'app.main',
        'app.config',
        'app.history',
        'app.llm_client',
        'app.logging_config',
        'app.templates',
        'app.templates_v5',
        # SQLite (history)
        'sqlite3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'pytest',
    ],
    win_no_prefer_redistribution=False,
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
    name='BoostIA',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
