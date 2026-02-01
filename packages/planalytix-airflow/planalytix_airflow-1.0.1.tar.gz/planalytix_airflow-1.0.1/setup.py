"""
Planalytix Airflow Provider

Apache Airflow provider package for Planalytix data integration platform.
Enables orchestration of data syncs via Airflow DAGs.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="planalytix-airflow",
    version="1.0.0",
    author="Planalytix",
    author_email="support@planalytix.io",
    description="Apache Airflow provider for Planalytix data integration platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/planalytix/planalytix-airflow",
    project_urls={
        "Documentation": "https://docs.planalytix.io/integrations/airflow",
        "Bug Tracker": "https://github.com/planalytix/planalytix-airflow/issues",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: Apache Airflow",
        "Framework :: Apache Airflow :: Provider",
    ],
    python_requires=">=3.8",
    install_requires=[
        "apache-airflow>=2.5.0",
        "requests>=2.28.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.20.0",
            "responses>=0.22.0",
        ],
    },
    entry_points={
        "apache_airflow_provider": [
            "provider_info=planalytix_provider.__init__:get_provider_info",
        ],
    },
)
