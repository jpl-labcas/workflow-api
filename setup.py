from setuptools import setup, find_namespace_packages

setup(
    name="labcas.workflow_api",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_namespace_packages(where="src"),
    install_requires=[
        "flask",
        "flask-restx",
        "requests",
    ],
    python_requires=">=3.7",
    author="LABCAS Team",
    description="REST API to list, describe, trigger, and monitor scientific workflows",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
) 