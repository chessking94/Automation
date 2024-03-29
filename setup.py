from setuptools import setup

import src


setup(
    name=src.__name__,
    version=src.__version__,
    author=src.__author__,
    author_email=src.__email__,
    description=src.__doc__.replace("\n", " ").strip(),
    license='GPL-3.0+',
    url='https://github.com/chessking94/Automation',
    python_requires='>=3.10',
    packages=['automation'],
    package_dir={'automation': 'src'},
    test_suite='test',
    install_requires=[
        'pandas>=2.1.4',
        'paramiko>=3.4.0',
        'PGPy>=0.6.0',
        'pykeepass>=4.0.6',
        'pywin32>=306',
        'PyYAML>=6.0.1',
        'sqlalchemy>=2.0.27',
        'XlsxWriter>=3.1.9'
    ]
)
