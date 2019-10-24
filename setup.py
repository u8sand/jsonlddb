from setuptools import setup

setup(
  name='jsonlddb',
  version='0.1',
  description='A jsonld in-memory database for fast framing',
  url='https://github.com/u8sand/jsonlddb',
  author='Daniel J. B. Clarke',
  author_email='u8sand@gmail.com',
  license='MIT',
  packages=['jsonlddb'],
  long_description=open('README.md', 'r').read(),
)
