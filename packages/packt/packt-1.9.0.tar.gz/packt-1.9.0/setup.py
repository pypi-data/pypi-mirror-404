import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as f:
    long_description = f.read()

package_version = '1.9.0'

requirements = [
    'click==8.3.1',
    'google-api-python-client==2.188.0',
    'oauth2client==4.1.3',
    'requests==2.32.5',
    'python-slugify==8.0.4'
]

dev_requirements = [
    'bumpversion==0.6.0',
    'mccabe==0.7.0',
    'pycodestyle==2.14.0',
    'pyflakes==3.4.0',
    'pylama==8.4.1',
    'setuptools; python_version >= \'3.12\''
]

setup(
    name='packt',
    version=package_version,
    packages=find_packages(),
    license='MIT',
    description='Script for grabbing daily Packt Free Learning ebooks',
    author='Łukasz Uszko',
    author_email='lukasz.uszko@gmail.com',
    url='https://gitlab.com/packt-cli/packt-cli',
    long_description=long_description,
    long_description_content_type='text/markdown',
    py_modules=['packt'],
    install_requires=requirements,
    extras_require={'dev': dev_requirements},
    entry_points={
        'console_scripts': [
            'packt-cli = packt.packtPublishingFreeEbook:packt_cli',
        ],
    },
    download_url='https://gitlab.com/packt-cli/packt-cli/-/archive/v1.9.0/packt-cli-v1.9.0.tar.gz',
    classifiers=[
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14'
    ]
)
