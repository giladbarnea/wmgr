
# -*- coding: utf-8 -*-
from setuptools import setup

long_description = None
EXTRAS_REQUIRE = {
    'optional': [
        'rich~=10.11',
        'twine~=3.4',
        'semver~=2.13',
    ],
}

setup_kwargs = {
    'name': 'wmgr',
    'version': '0.1.0',
    'description': 'Yet another tool for tiling, resizing, and managing windows',
    'long_description': long_description,
    'license': 'MIT',
    'author': '',
    'author_email': 'Gilad Barnea <giladbrn@gmail.com>',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/giladbarnea/wmgr',
    'packages': [
        'wmgr',
    ],
    'package_data': {'': ['*']},
    'classifiers': [
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
    ],
    'extras_require': EXTRAS_REQUIRE,
    'python_requires': '>=3.9',

}


setup(**setup_kwargs)

