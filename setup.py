from setuptools import find_packages
from setuptools import setup


install_requires = [

]


dependency_links = [

]


setup(
    name='finvoker',
    version='0.1',
    description='Utilities for invoking FaaS functions',
    author='King Chung Huang',
    author_email='kchuang@ucalgary.ca',
    url='https://git.ucalgary.ca/rms/functions/finvoker',
    packages=find_packages(),
    package_data={
    },
    install_requires=install_requires,
    dependency_links=dependency_links,
    entry_points="""
    """,
    zip_safe=True
)
