from setuptools import find_packages, setup
from pygritbx import __version__ as vs

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
    name="pygritbx",
    version=vs,
    description='Python-based Gearbox Reliability and Integrity Tool',
    #package_dir={"": "pygrit"},
    packages=find_packages(),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Rmhuneineh/pygritbx",
    author="Ragheed Huneineh",
    author_email="ragheedmhuneineh@outlook.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Intended Audience :: Education",
        "Natural Language :: English",
        "Topic :: Scientific/Engineering",
    ],
    install_requires=[
        "numpy >= 2.2.4",
        "scipy >= 1.15.2",
        "matplotlib >= 3.10.1"
    ],
    extras_require={
        "dev": ["twine >= 6.1.0"]
    },
    python_requires=">= 3.11.5",
)