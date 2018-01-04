from setuptools import find_packages
from setuptools import setup


install_requires = [
    'confluent-kafka',
    'requests',
]


dependency_links = [

]


setup(
    name='ftrigger',
    version='0.1',
    description='Triggers for FaaS functions',
    author='King Chung Huang',
    author_email='kchuang@ucalgary.ca',
    url='https://github.com/ucalgary/ftrigger',
    packages=find_packages(),
    package_data={
    },
    install_requires=install_requires,
    dependency_links=dependency_links,
    entry_points="""
    [console_scripts]
    kafka-trigger=ftrigger.kafka:main
    """,
    zip_safe=True
)
