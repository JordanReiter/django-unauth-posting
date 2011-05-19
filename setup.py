#!/usr/bin/env python

from distutils.core import setup

setup(name='django-unauth-posting',
      version='1.0',
      description='Allows unauthenticated users to post a form, and *then* authenticate',
      author='Jordan Reiter',
      author_email='jordanreiter@gmail.com',
      url='https://github.com/JordanReiter/django-unauth-posting',
      packages=['unauth_posting'],
     )