# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['architectonics',
 'architectonics.common',
 'architectonics.common.utils',
 'architectonics.core',
 'architectonics.core.config',
 'architectonics.core.factory',
 'architectonics.core.models',
 'architectonics.core.result',
 'architectonics.core.services',
 'architectonics.core.validation',
 'architectonics.infrastructure',
 'architectonics.infrastructure.config',
 'architectonics.infrastructure.entities',
 'architectonics.infrastructure.repositories']

package_data = \
{'': ['*']}

install_requires = \
['SQLAlchemy==2.0.46',
 'aio-pika==9.5.8',
 'alembic==1.18.1',
 'asyncpg==0.31.0',
 'dotenv==0.9.9',
 'fastapi==0.128.0',
 'pydantic==2.12.5',
 'uvicorn==0.40.0']

setup_kwargs = {
    'name': 'architectonics',
    'version': '0.0.28',
    'description': '',
    'long_description': None,
    'author': 'Your Name',
    'author_email': 'you@example.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.14,<4.0',
}


setup(**setup_kwargs)
