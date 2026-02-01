from setuptools import setup, find_packages
from pathlib import Path

# Read README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="appxploit",
    version="1.0.1",
    author="LAKSHMIKANTHAN K",
    author_email="",
    description="Professional Android APK security analysis tool for bug bounty hunters",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/letchupkt/AppXploit",
    packages=[
        'appxploit',
        'appxploit.core',
        'appxploit.analysis',
        'appxploit.discovery',
        'appxploit.filtering',
        'appxploit.intelligence',
        'appxploit.reasoning',
        'appxploit.reporting',
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.1.0",
        "colorama>=0.4.6",
        "pyyaml>=6.0",
        "jinja2>=3.1.2",
        "requests>=2.31.0",
        "lxml>=4.9.0",
    ],
    entry_points={
        "console_scripts": [
            "appxploit=appxploit.__main__:main",
        ],
    },
    include_package_data=True,
    package_data={
        "appxploit": [
            "data/*.txt",
            "data/*.yaml",
            "reporting/templates/*.j2",
        ],
    },
    keywords="android apk security analysis bug-bounty penetration-testing reverse-engineering",
    project_urls={
        "Bug Reports": "https://github.com/letchupkt/AppXploit/issues",
        "Source": "https://github.com/letchupkt/AppXploit",
    },
)
