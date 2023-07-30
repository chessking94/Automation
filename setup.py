from setuptools import setup

import src

with open('requirements.txt', 'r') as req_file:
    lines = req_file.readlines()
    req_list = [line.strip() for line in lines]

setup(
    name=src.__name__,
    version=src.__version__,
    author=src.__author__,
    description=src.__doc__.replace("\n", " ").strip(),
    license='GPL-3.0+',
    url='https://github.com/chessking94/Automation',
    python_requires='>=3.10',
    packages=['automation'],
    package_dir={'automation': 'src'},
    test_suite='test',
    install_requires=req_list
)
