# coding=utf-8
"""
GitHub-Flask
------------

Adds support to authorize users with GitHub to Flask.

"""
from setuptools import setup


setup(
    name='GitHub-Flask',
    version='0.2.0',
    url='http://github.com/cenkalti/github-flask',
    license='MIT',
    author=u'Cenk Altı',
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
