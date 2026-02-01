#! /usr/local/bin/python3
"""Setup file specifying build of .whl."""

from setuptools import setup

setup(
  name='mformat',
  version='0.2.2',
  description='Uniform way to write simple text to different file formats',
  author='Tom Björkholm',
  author_email='klausuler_linnet0q@icloud.com',
  python_requires='>=3.12',
  packages=['mformat'],
  package_dir={'mformat': 'src/mformat'},
  package_data={'mformat': ['src/py.typed']},
  install_requires=[  # pylint: disable=duplicate-code
    'pip',
    'setuptools',
    'build',
    'wheel'
  ]
)
