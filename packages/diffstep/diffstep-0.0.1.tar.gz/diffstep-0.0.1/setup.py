from setuptools import setup, find_packages

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Education',
    'Operating System :: Microsoft :: Windows :: Windows 10',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3°'
]


setup (
    name='diffstep',
    version='0.0.1',
    description="This is a library for Algorithmic Differentiation.",
    Long_description=open('README.txt').read() + '\n\n' + open('CHANGELOG.txt').read(),
    url='',
    author="Ayo",
    author_email="akoitilo@gmail.com",
    License= 'MIT',
    cLassifiers=classifiers, 
    keywords='differentiation',
    packages=find_packages(),
    install_requires=['']
    )