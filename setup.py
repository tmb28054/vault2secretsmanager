#!/usr/bin/env python
"""
    I provide a package setup for the egg.
"""


from setuptools import setup


def get_changelog() -> str:
    """
        I return the version from changelog.

        Args
        None

        Returns
        str: string form of the current verion.
    """
    with open('CHANGELOG.md', 'r', encoding='utf8') as file_handler:
        for line in file_handler:
            if line.startswith('## ['):
                if 'unreleased' not in line.lower():
                    left = line.split(']')[0]
                    return left.split('[')[1]
    return 'unknown'


def get_readme() -> str:
    """
        Load the readme.
    """
    with open('README.md', 'r', encoding='utf8') as file_handler:
        return file_handler.read()


def get_requirements() -> list:
    """
        I generate a list of requirements from the requirements.txt
    """
    with open('requirements.txt', encoding='utf8') as file_handler:
        return file_handler.read().split("\n")


setup_options = {
    'description': 'A systemd service that syncs vault secrets to secrets manager',
    'long_description': get_readme(),
    'long_description_content_type': 'text/markdown',
    'license': 'Apache License 2.0',
    'url': 'https://github.com/tmb28054/vault2secretsmanager',
    'name': 'vault2secretsmanager',
    'version': get_changelog(),
    'author': 'Topaz M. Bott',
    'author_email': 'topaz@topazhome.net',
    'scripts': [],
    'package_data': {
        'vault2secretsmanager': []
    },
    'packages': ['vault2secretsmanager'],
    'include_package_data': True,
    'install_requires': get_requirements(),
    'classifiers': [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    'entry_points': {
        'console_scripts': [
            'vault2secretsmanager = vault2secretsmanager:main',
        ]
    },
}

setup(**setup_options)
