from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="open-source-hlr-hss",
    version="1.0.0",
    author="Open Source Community",
    description="Open Source HLR/HSS for 2G-5G Networks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Kaimeliax/Open-Source-HLR-HSS",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Telecommunications Industry",
        "Topic :: Communications :: Telephony",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pyyaml>=6.0",
        "pymongo>=4.0.0",
        "redis>=4.0.0",
        "sqlalchemy>=2.0.0",
        "cryptography>=41.0.0",
        "pycryptodome>=3.19.0",
        "flask>=3.0.0",
        "flask-restful>=0.3.10",
        "aiohttp>=3.9.0",
    ],
    entry_points={
        'console_scripts': [
            'hlr-hss=hlr_hss.main:main',
            'dra=hlr_hss.dra.main:main',
        ],
    },
)
