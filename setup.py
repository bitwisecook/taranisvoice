"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

from setuptools import setup
from version import __version__


APP = ['taranisvoice.py']
APP_NAME = 'Taranis Voice'
DATA_FILES = []
OPTIONS = {
    'force_system_tk'       : True,
    'iconfile'              : 'icon.icns',
    'includes'              : 'pyttsx3.drivers,pyttsx3.engines,objc,pyttsx3,pyttsx3.drivers.nsss',
    'redirect_stdout_to_asl': True,
    'plist': {
        'CFBundleName'              : APP_NAME,
        'CFBundleDisplayName'       : APP_NAME,
        'CFBundleGetInfoString'     : APP_NAME,
        'CFBundleIdentifier'        : "com.taranis.voice",
        'CFBundleVersion'           : __version__,
        'CFBundleShortVersionString': __version__,
        'NSHumanReadableCopyright'  : "Copyright © 2018, James Deucker, All Rights Reserved, Licensed as GPLv3"
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)