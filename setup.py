"""
GitHub-Flask
------------

Adds support to authorize users with GitHub to Flask.

"""
import os
import re
from setuptools import setup


def read(*fname):
    path = os.path.join(os.path.dirname(__file__), *fname)
    with open(path) as f:
        return f.read()


def get_version():
    for line in read('flask_github.py').splitlines():
        m = re.match(r"__version__\s*=\s'(.*)'", line)
        if m:
            return m.groups()[0].strip()
    raise Exception('Cannot find version')


setup(
    name='GitHub-Flask',
    version=get_version(),
    url='http://github.com/cenkalti/github-flask',
    license='MIT',
    author='Cenk Alti',
    author_email='cenkalti@gmail.com',
    description='Adds support for authorizing users with GitHub to Flask.',
    long_description=__doc__,
    py_modules=['flask_github'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Flask',
        'requests',
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
