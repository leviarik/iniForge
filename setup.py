import os 
import glob
from setuptools import setup, find_packages

# read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='iniForge',
    description='Bulk Settings Precision: configuration files high-performance bulk editor.',
    long_description=long_description,
    long_description_content_type='text/plain',
    version='3.1.0',
    author=['Arik Levi'],
    author_email=['ariklevi@gmail.com'],
    homepage='TDB',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    python_requires='>=3.9',
    setup_requires=['wheel'],
    include_package_data=True,
    install_requires=[
        "configparser",
        "PySide6==6.2.4",
        "shiboken6==6.2.4",
        "coloredlogs==15.0.1",
        "numpy<2",
        "pyperclip"
    ],
    package_data={
        'iniforge': [
            'images/*.png',
            'images/*.ico',
            'images/help/*.png',
            'config.ini',
            'help_content.html',
            'pkg_info.txt'
        ],
    },
    entry_points={
        'console_scripts': [
            'iniforge = iniforge.gui:main'
        ]
    }
)
