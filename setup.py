"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

from setuptools import setup

APP = ['Tongji-AutoGetScore.py']
DATA_FILES = ['sources','tools.py','ui']
OPTIONS = {
    'iconfile':'sources/logo.icns',
    'plist': {
                    'CFBundleName'   : 'Tongji-ScoreAutoGet',     # 应用名
                    'CFBundleDisplayName': '同济成绩自动查询器', # 应用显示名
                    'CFBundleVersion': '0.2.0',      # 应用版本号
                    'CFBundleIdentifier' : 'com.cinea.tjsag', # 应用包名、唯一标识
                    'NSHumanReadableCopyright': 'Copyright © 2022 Cinea Works. Use the GPL license.', # 可读版权
                    'includes': ['loguru', 'PyQt5.QtCore', 'PyQt5.QtWidgets', 'PyQt5.QtGui','requests','PyQt5.QtWebEngineWidgets','PyQt5.QtNetwork']
           }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
