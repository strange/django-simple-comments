#!/usr/bin/env python
# encoding: utf-8

from distutils.core import setup

setup(name='simple_comments', version='0.1',
      description='Simple reusable Django comments app',
      author='Gustaf Sjöberg', author_email='gs@distrop.com',
      packages=['simple_comments', 'simple_comments.templatetags'])
