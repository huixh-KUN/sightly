from setuptools import setup, find_packages
import os

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

project_root = os.path.abspath(os.path.dirname(__file__))

voice_files = []
voice_dir = os.path.join(project_root, 'voice')
if os.path.exists(voice_dir):
    for file in os.listdir(voice_dir):
        if file.endswith('.mp3'):
            voice_files.append(os.path.join('voice', file))

setup(
    name='sightly',
    version='1.0.0',
    description='灵眸 Sightly - 屏幕自动化识别系统',
    author='Sightly Team',
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=requirements,
    package_data={
        '': ['*.mp3'],
    },
    data_files=[
        ('voice', [os.path.join('voice', f) for f in os.listdir('voice') if f.endswith('.mp3')]) if os.path.exists('voice') else (),
    ],
    entry_points={
        'console_scripts': [
            'sightly=main:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Microsoft :: Windows',
    ],
    python_requires='>=3.10',
)
