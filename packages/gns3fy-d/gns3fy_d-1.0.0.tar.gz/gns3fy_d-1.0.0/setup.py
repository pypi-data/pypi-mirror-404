from setuptools import setup, find_packages

setup(
    name="gns3fy-d",  # Your unique name
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "pydantic" 
        # Add other requirements from pyproject.toml if needed
    ],
)
