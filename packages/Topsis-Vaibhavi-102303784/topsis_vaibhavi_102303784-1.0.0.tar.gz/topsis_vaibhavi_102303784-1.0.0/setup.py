from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name='Topsis-Vaibhavi-102303784',
    version='1.0.0',
    author='Vaibhavi',
    author_email='vaibhavi@example.com',
    description='A Python package for TOPSIS (Technique for Order Preference by Similarity to Ideal Solution) analysis',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/vaibhavi/Topsis-Vaibhavi-102303784',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Mathematics',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    keywords='topsis, multi-criteria decision making, mcdm, decision analysis, ranking',
    python_requires='>=3.7',
    install_requires=[
        'pandas>=1.0.0',
        'numpy>=1.18.0',
        'openpyxl>=3.0.0',
    ],
    entry_points={
        'console_scripts': [
            'topsis=topsis_vaibhavi_102303784.topsis:main',
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/vaibhavi/Topsis-Vaibhavi-102303784/issues',
        'Source': 'https://github.com/vaibhavi/Topsis-Vaibhavi-102303784',
    },
)
