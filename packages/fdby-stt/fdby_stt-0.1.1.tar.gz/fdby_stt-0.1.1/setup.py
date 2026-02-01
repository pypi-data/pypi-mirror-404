from setuptools import setup, find_packages

setup(
    name='fdby_stt',
    version='0.1.1',
    author='Sachin Gadwal',
    author_email='sachingadwal1899@gmail.com',
    description='this is a speech to text package created by Sachin Gadwal',
    packages=find_packages(),
    install_requires=[
        'selenium',
        'webdriver-manager',
    ]
)