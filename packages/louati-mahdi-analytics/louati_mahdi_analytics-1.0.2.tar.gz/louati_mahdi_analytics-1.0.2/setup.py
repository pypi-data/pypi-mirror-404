# setup.py
from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="louati-mahdi-analytics",
    version="1.0.2",
    author="Louati Mahdi",
    author_email="louatimahdi390@gmail.com",
    description="A powerful SQL-like query language for Data, Stats, Causal AI, and Plotly Viz.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/mahdi123-tech",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=requirements,
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'louati-mahdi=louati_mahdi_analytics.cli:run_welcome',
        ],
    },
) # <--- THIS WAS MISSING! THE FIX!