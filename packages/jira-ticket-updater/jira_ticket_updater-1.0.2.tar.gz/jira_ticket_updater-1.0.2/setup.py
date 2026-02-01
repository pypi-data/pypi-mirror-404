"""Setup script for jira-status-updater."""

from setuptools import setup

# Read the contents of README.md
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="jira-ticket-updater",
    version="1.0.2",
    description="A command-line tool for updating Jira ticket status",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Pandiyaraj Karuppasamy",
    author_email="pandiyarajk@live.com",
    url="https://github.com/Pandiyarajk/jira-ticket-updater",
    packages=["jira_ticket_updater"],
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        "requests>=2.25.0",
    ],
    entry_points={
        "console_scripts": [
            "jira-ticket-updater=jira_ticket_updater.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development",
        "Topic :: Utilities",
    ],
    python_requires=">=3.7",
    keywords="jira status-update automation devops workflow",
)
