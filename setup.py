from setuptools import setup, find_packages

setup(
    name="pyBacktest",
    version="1.1.3",
    author="Ben Bell",
    author_email="slow111poke@gmail.com",
    description="A backtesting framework for stock price prediction strategies",
    long_description=open('readme.md').read(),
    long_description_content_type='text/markdown',
    url="https://github.com/slowpoke111/pyBacktest",
    packages=find_packages(include=['pyBacktest', 'pyBacktest.*']),
    install_requires=[
        "pandas",
        "numpy",
        "yfinance"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    license="LGPL",
)
