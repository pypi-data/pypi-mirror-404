# Copyright 2015-2024 The MathWorks, Inc.
import sys
import warnings
from shutil import rmtree
from os.path import exists

use_build_msg = '.*Use build and pip and other standards-based tools.*'
excTxt = ''

if 'bdist_wheel' in sys.argv[1:]:
    # If "python setup.py bdist_wheel" is executed, we need to 
    # import from setuptools.
    warnings.filterwarnings('ignore', message=use_build_msg)
    from setuptools import setup
    from setuptools.command.install import install
    try:
        import wheel
    except Exception as exc:
        excTxt = '{}'.format(exc)

if excTxt:
    print("bdist_wheel requires the 'wheel' module, which can be installed via 'python -m pip install wheel'")
    raise ModuleNotFoundError(excTxt)

firstExceptionMessage = ''
secondExceptionMessage = ''

try:
    from setuptools import setup
    from setuptools.command.install import install
except Exception as firstE:
    firstExceptionMessage = str(firstE)

if firstExceptionMessage:
    try:
        # We suppress warnings about deprecation of distutils. If neither is found,
        # we will only mention setuptools, which is the one that should be used.
        warnings.filterwarnings('ignore', message='.*distutils package is deprecated.*', 
            category=DeprecationWarning)
        from distutils.core import setup
        from distutils.command.install import install
    except Exception as secondE:
        secondExceptionMessage = str(secondE)

if secondExceptionMessage:
    raise EnvironmentError("Installation failed. Install setuptools using 'python -m pip install setuptools', then try again.")

class InstallAndCleanBuildArea(install):
    # Directories with these names are created during installation, but are 
    # not needed afterward (unless bdist_wheel is being executed, in which 
    # case we skip this step).
    clean_dirs = ["./build", "./dist"]

    def clean_up(self):
        for dir in self.clean_dirs:
            if exists(dir):
                rmtree(dir, ignore_errors=True) 

    def run(self):
        install.run(self)
        self.clean_up()
    
if __name__ == '__main__':
    setup_dict = {
        'name': 'hera-matlab',
        'version': '1.2.1',
        'description': 'A Python interface to hera_matlab',
        'author': 'MathWorks',
        'url': 'https://www.mathworks.com/',
        'platforms': ['Linux', 'Windows', 'macOS'],
        'packages': [
            'hera_matlab'
        ],
        'package_data': {'hera_matlab': ['*.ctf']}
    }
    
    if not 'bdist_wheel' in sys.argv[1:]:
        setup_dict['cmdclass'] = {'install': InstallAndCleanBuildArea}
    
    
    # --- INJECTED METADATA START ---
    try:
        import os
        here = os.path.abspath(os.path.dirname(__file__))
        
        # Load Long Description from README.md
        readme_path = os.path.join(here, 'README.md')
        if os.path.exists(readme_path):
            with open(readme_path, 'r', encoding='utf-8') as f:
                setup_dict['long_description'] = f.read()
            setup_dict['long_description_content_type'] = 'text/markdown'
            
    except Exception as e:
        print(f'Warning: Could not inject README: {e}')

    # Enhanced Metadata
    setup_dict['name'] = 'hera-matlab'
    setup_dict['author'] = 'Lukas von Erdmannsdorff'
    setup_dict['license'] = 'MIT'
    
    # Keywords for PyPI discovery
    setup_dict['keywords'] = [
        'ranking', 'benchmarking', 'statistics', 'effect-size', 
        'bootstrapping', 'significance-testing', 'matlab-interface', 
        'hierarchical-compensatory', 'scientific-computing'
    ]

    # Dynamic URL handling based on GitHub Actions environment
    repo_url = 'https://github.com/lerdmann1601/HERA-Matlab' # Fallback
    if 'GITHUB_REPOSITORY' in os.environ:
         repo_url = f"https://github.com/{os.environ['GITHUB_REPOSITORY']}"
    
    setup_dict['url'] = repo_url
    setup_dict['project_urls'] = {
        'Bug Tracker': f"{repo_url}/issues",
        'Source Code': repo_url,
        'Documentation': 'https://lerdmann1601.github.io/HERA-Matlab/',
    }
    
    setup_dict['classifiers'] = [
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Intended Audience :: Science/Research',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]

    # Python Version Constraint
    setup_dict['python_requires'] = '>=3.9, <3.13'
    # --- INJECTED METADATA END ---
    
    setup(**setup_dict)
    


