# -*- mode: python -*-

import fnmatch
import os
import sys

def real_sys_prefix():
    if hasattr(sys, "real_prefix"):  # running in virtualenv
        return sys.real_prefix
    elif hasattr(sys, "base_prefix"):  # running in venv
        return sys.base_prefix
    else:
        return sys.prefix

TOOL_PATH = os.path.join(real_sys_prefix(), "Tools", "i18n")
WBSA_PATH = SPECPATH  # pyinstaller-defined global
ROOT_PATH = os.path.join(WBSA_PATH, "..", "..", "..")
MOPY_PATH = os.path.join(ROOT_PATH, "Mopy")
GAME_PATH = os.path.join(MOPY_PATH, "bash", "game")

block_cipher = None
entry_point = os.path.join(MOPY_PATH, "Wrye Bash Launcher.pyw")
icon_path = os.path.join(WBSA_PATH, "bash.ico")
manifest_path = os.path.join(WBSA_PATH, "manifest.xml")
hiddenimports = ["pygettext", "msgfmt"]

for root, _, filenames in os.walk(GAME_PATH):
    for filename in fnmatch.filter(filenames, '*.py'):
        path = os.path.join(root, filename)
        path = path[:-3]  # remove '.py'
        import_path = os.path.relpath(path, start=MOPY_PATH)
        hiddenimports.append(import_path.replace(os.sep, "."))

a = Analysis([entry_point],
             pathex=[TOOL_PATH, ROOT_PATH],
             binaries=[],
             datas=[],
             hiddenimports=hiddenimports,
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='Wrye Bash',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False,
          icon=icon_path,
          manifest=manifest_path)
