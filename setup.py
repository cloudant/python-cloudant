"""
_setup.py_

Python-Cloudant Client Library

"""

from setuptools import setup, find_packages

setup_args ={
    'description': 'Python-Cloudant Client Library',
    'include_package_data': True,
    'install_requires': ['requests==2.7.0'],
    'name': 'python-cloudant',
    'version': '0.0.6',
    'packages': find_packages('./src'),
    'provides': find_packages('./src'),
    'package_dir': {'': 'src'}
}

setup(**setup_args)
