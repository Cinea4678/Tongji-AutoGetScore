from distutils.core import setup
import py2exe
import sys
 
#this allows to run it with a simple double click.
sys.argv.append('py2exe')
 
py2exe_options = {
        "includes": ["loguru","PyQt5","requests"],
        #"dll_excludes": ["MSVCP90.dll",],
        "compressed": 1,
        "optimize": 2,
        "ascii": 0,
        "bundle_files": 1,
        }
 
setup(
      name = 'Tongji-AutoGetScore',
      version = '0.1',
      windows = [{ "script":'main.py',"icon_resources":[(1,"nmck_bb.ico")]}], 
      #zipfile = None,
      options = {'py2exe': py2exe_options}
      )