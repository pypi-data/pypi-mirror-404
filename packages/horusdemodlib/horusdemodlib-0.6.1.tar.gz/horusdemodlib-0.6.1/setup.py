# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['horusdemodlib']

package_data = \
{'': ['*']}

install_requires = \
['asn1tools>=0.165.0,<0.166.0',
 'cffi>1.14.0',
 'python-dateutil>=2.8,<3.0',
 'requests>=2.25.1,<3.0.0']

extras_require = \
{':python_version >= "3.13" and python_version < "4.0"': ['audioop-lts']}

entry_points = \
{'console_scripts': ['horus_demod = horusdemodlib:demod.main',
                     'horus_uploader = horusdemodlib:uploader.main']}

setup_kwargs = {
    'name': 'horusdemodlib',
    'version': '0.6.1',
    'description': 'Project Horus HAB Telemetry Demodulators',
    'long_description': 'None',
    'author': 'Mark Jessop',
    'author_email': 'None',
    'maintainer': 'None',
    'maintainer_email': 'None',
    'url': 'None',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'extras_require': extras_require,
    'entry_points': entry_points,
    'python_requires': '>=3.9,<4.0',
}
from build_lib import *
build(setup_kwargs)

setup(**setup_kwargs)
