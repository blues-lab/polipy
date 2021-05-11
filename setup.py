import os
from setuptools import setup, find_packages

# The directory containing this file.
WORK_DIR = os.path.dirname(os.path.abspath(__file__))

# The text of the README file.
README = os.path.join(WORK_DIR, 'README.md')
with open(README, 'r') as f:
    long_description = f.read()

setup(
    name='polipy',
    version='0.1.2',
    description='Library for scraping, parsing, and analyzing privacy policies.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/blues-lab/polipy',
    license='GNU General Public License v3.0 (GPLv3)',
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9'
    ],
    packages=find_packages(),
    include_package_data=False,
    install_requires=[
        'beautifulsoup4',
        'certifi',
        'cffi',
        'chardet',
        'cryptography',
        'filelock',
        'idna',
        'pdfminer.six',
        'pycparser',
        'requests',
        'requests-file',
        'selenium',
        'six',
        'sortedcontainers',
        'soupsieve',
        'tqdm',
        'urllib3'
    ],
    entry_points={
        'console_scripts': [
            'polipy=polipy.__main__:main',
        ]
    },
)
