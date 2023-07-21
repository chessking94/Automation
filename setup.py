from setuptools import setup

setup(
    name='automation',
    version='1.0.0',
    author='Ethan Hunt',
    license='GPL-3.0+',
    url='https://github.com/chessking94/Automation',
    python_requires='>=3.10',
    packages=['automation'],
    package_dir={'automation': 'src'},
    test_suite='test',
    install_requires=[
        'pandas==2.0.2',
        'paramiko==3.2.0',
        'PGPy==0.6.0',
        'pykeepass==4.0.5',
        'pyodbc==4.0.39',
        'pywin32==306',
        'XlsxWriter==3.1.2'
    ]
)
