"""
Planalytix Airflow Provider

Provides hooks, operators, and sensors for integrating Planalytix
with Apache Airflow workflows.
"""

__version__ = "1.0.0"


def get_provider_info():
    """Return provider metadata for Airflow."""
    return {
        "package-name": "planalytix-airflow",
        "name": "Planalytix",
        "description": "Apache Airflow provider for Planalytix data integration platform",
        "versions": [__version__],
        "connection-types": [
            {
                "connection-type": "planalytix",
                "hook-class-name": "planalytix_provider.hooks.planalytix.PlanalytixHook",
            }
        ],
        "hook-class-names": [
            "planalytix_provider.hooks.planalytix.PlanalytixHook",
        ],
        "extra-links": [
            "planalytix_provider.operators.sync.PlanalytixJobLink",
        ],
    }
