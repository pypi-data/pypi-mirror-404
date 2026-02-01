from setuptools import setup, find_packages
import os

this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="nexus_gateway",
    version="3.1.1", # 🚀 BUMPED TO 3.1.0 to match Protocol Standard
    description="High-performance AI infrastructure with semantic caching and sovereign governance.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Sunny Anand",
    author_email="asunny583@gmail.com",
    url="https://nexus-gateway.org", # 🚀 Added official domain
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
    ],
    # ⚡ THE CLI COMMANDS
    entry_points={
        'console_scripts': [
            'nexus=nexus_gateway.cli:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Development Status :: 5 - Production/Stable", # 🚀 Signals this is ready for enterprise
    ],
    python_requires='>=3.7',
)