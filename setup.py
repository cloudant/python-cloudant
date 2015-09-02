"""
_setup.py_

Python-Cloudant Client Library

"""

from setuptools import setup, find_packages

requirements_file = open('requirements.txt')
requirements = requirements_file.read().strip().split('\n')

setup_args ={
    'description': 'Python-Cloudant Client Library',
    'include_package_data': True,
    'install_requires': requirements,
    'name': 'python-cloudant',
    'version': '0.0.6',
    'packages': find_packages('./src'),
    'provides': find_packages('./src'),
    'package_dir': {'': 'src'}
}

setup(**setup_args)
