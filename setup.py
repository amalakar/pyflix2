try:
        from setuptools import setup
except ImportError:
        from distutils.core import setup

setup(
    name="pyflix2",
    version='0.1.2',
    description="A python module for accessing Netflix REST webservice, both V1 and V2 supports oauth and oob.",
    long_description=open('README.rst').read() + '\n\n' +
                             open('HISTORY.rst').read(),
    author='Arup Malakar',
    author_email='amalakar@gmail.com',
    url="http://pyflix2.readthedocs.org/",
    package_dir={'pyflix2': 'pyflix2'},
    include_package_data=True,
    license=open('LICENSE').read(),
    packages = ['pyflix2'],
    install_requires=['requests', 'requests-oauth']
)
