from setuptools import setup, find_packages

setup(
    name="pyBacktest",
    version="0.0.1",
    author="Ben Bell",
    author_email="slow111poke@gmail.com",
    description="A backtesting framework for stock price prediction strategies",
    packages=find_packages(include=['pyBacktest', 'pyBacktest.*']),
    install_requires=[
        "pandas",
        "numpy",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)