# -*- mode: python ; coding: utf-8 -*-
# Сборка: pyinstaller --noconfirm --clean build/neimark.spec  (из корня проекта)
import os
import sys

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
NAME = "NeimarkCorrelation"

a = Analysis(
    [os.path.join(ROOT, "main.py")],
    pathex=[ROOT],
    datas=[(os.path.join(ROOT, "assets"), "assets")],
    excludes=["tkinter", "unittest", "pydoc", "typst", "numpy", "pygame.examples", "pygame.tests",
              "pygame.docs"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=NAME,
    console=False,
    icon=os.path.join(ROOT, "build", "icon.ico") if sys.platform == "win32" else None,
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name=NAME, upx=False)
