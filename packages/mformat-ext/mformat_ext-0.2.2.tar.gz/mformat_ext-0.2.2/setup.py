#! /usr/local/bin/python3
"""Setup file specifying build of .whl."""

from setuptools import setup

setup(
  name='mformat_ext',
  version='0.2.2',
  description='Uniform way to write simple text extended with DOCX and ODT files',
  author='Tom Björkholm',
  author_email='klausuler_linnet0q@icloud.com',
  python_requires='>=3.12',
  packages=['mformat_ext'],
  package_dir={'mformat_ext': 'src/mformat_ext'},
  package_data={'mformat_ext': ['src/py.typed']},
  install_requires=[  # pylint: disable=duplicate-code
    'mformat >= 0.2.2',
    'python-docx >= 1.2.0',
    'odfdo >= 3.19.0',
    'pip >= 25.3',
    'setuptools >= 80.10.2',
    'build >= 1.4.0',
    'wheel>=0.46.3'
  ]
)
