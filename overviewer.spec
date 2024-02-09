# -*- mode: python -*-
# spec file for pyinstaller

block_cipher = None

import sys
sys.modules['FixTk'] = None

def get_overviewer_pkgname():
    from overviewer_core import overviewer_version
    return "overviewer-" + overviewer_version.VERSION

a = Analysis(['overviewer.py'],
             binaries=None,
             datas=[("overviewer_core/data", "overviewer_core/data")],
             hiddenimports=[
                 'overviewer_core.aux_files.genPOI',
                 # https://github.com/pypa/setuptools/issues/1963
                 'pkg_resources.py2_warn',
             ],
             hookspath=[],
             runtime_hooks=[],
             excludes=['FixTk', 'tcl', 'tk', '_tkinter', 'tkinter', 'Tkinter'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='overviewer',
          debug=False,
          strip=False,
          upx=False,
          console=True,
          contents_directory='.' )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='overviewer')