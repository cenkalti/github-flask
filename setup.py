"""
GitHub-Flask
------------

Adds support to authorize users with GitHub and make API requests with Flask.

Links
`````

* `documentation <http://github-flask.readthedocs.org>`_
* `development version
  <http://github.com/cenkalti/github-flask/zipball/master#egg=GitHub-Flask-dev>`_

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
    description='GitHub extension for Flask microframework',
    long_description=__doc__,
    py_modules=['flask_github'],
    test_suite='test_flask_github',
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Flask',
        'requests',
    ],
    tests_require=['mock'],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
