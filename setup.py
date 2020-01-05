from setuptools import setup, find_packages

setup(
  name='jsonlddb',
  version='0.1',
  description='A jsonld in-memory database for fast framing',
  url='https://github.com/u8sand/jsonlddb',
  author='Daniel J. B. Clarke',
  author_email='u8sand@gmail.com',
  license='MIT',
  packages=find_packages(exclude=['test_*.py']),
  long_description=open('README.md', 'r').read(),
  requires=['sortedcontainers'],
  extras_require={
    'generate': ['nltk'],
    'table': ['pandas'],
  },
  tests_require=['pytest'],
  test_suite='pytest',
)
