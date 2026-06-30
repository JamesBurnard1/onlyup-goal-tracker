from setuptools import setup

APP = ['main_menu_gui.py']
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'onlyup.icns',
    'packages': ['tkinter'],
}

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
