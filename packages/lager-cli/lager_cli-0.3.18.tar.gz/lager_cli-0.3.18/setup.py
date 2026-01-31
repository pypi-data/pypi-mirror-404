import os
import setuptools

import sys
sys.path.insert(0, os.path.dirname(__file__))
from __init__ import __version__ as lager_version

def readme():
    path = os.path.dirname(__file__)
    with open(os.path.join(path, 'README.md')) as f:
        return f.read()

name = 'lager-cli'
description = 'Lager CLI - Box and Docker connectivity'
author = 'Lager Data LLC'
email = 'hello@lagerdata.com'
classifiers = [
    'Development Status :: 3 - Alpha',
    'License :: OSI Approved :: Apache Software License',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.10',
    'Programming Language :: Python :: 3.11',
    'Programming Language :: Python :: 3.12',
    'Programming Language :: Python :: 3.13',
    'Programming Language :: Python :: 3.14',
    'Topic :: Software Development',
]

if __name__ == "__main__":
    setuptools.setup(
        name=name,
        version=lager_version,
        description=description,
        long_description=readme(),
        long_description_content_type='text/markdown',
        classifiers=classifiers,
        url='https://github.com/lagerdata/lager-mono',
        author=author,
        author_email=email,
        maintainer=author,
        maintainer_email=email,
        license='Apache-2.0',
        python_requires=">=3.10",
        packages=['cli'] + ['cli.' + p for p in setuptools.find_packages(where='.')],
        package_dir={'cli': '.'},
        package_data={
            'cli.deployment.scripts': ['*.sh'],
            'cli.deployment.security': ['*.sh'],
        },
        include_package_data=True,
        install_requires='''
            async-generator >= 1.10
            pymongo >= 4.0
            certifi >= 2020.6.20
            chardet >= 5.2.0
            click >= 8.1.2
            colorama >= 0.4.3
            h11 >= 0.16
            idna >= 3.4
            ipaddress >= 1.0.23
            Jinja2 >= 3.1.2
            multidict >= 6.0.2
            outcome >= 1.0.1
            pigpio >= 1.78
            python-dateutil >= 2.8.1
            PyYAML >= 6.0.1
            requests >= 2.31.0
            requests-toolbelt >= 1.0.0
            six >= 1.16.0
            sniffio >= 1.3.1
            sortedcontainers >= 2.2.2
            tenacity >= 6.2.0
            texttable >= 1.6.2
            trio >= 0.27.0
            lager-trio-websocket >= 0.9.0.dev0
            urllib3 >= 1.26.20, < 3.0.0
            wsproto >= 0.14.1
            yarl >= 1.8.1
            boto3
            textual >= 3.2.0
            python-socketio >= 5.10.0
            websocket-client >= 1.0.0
        ''',
        entry_points={
            'console_scripts': [
                'lager=cli.main:cli',
            ],
        }
    )