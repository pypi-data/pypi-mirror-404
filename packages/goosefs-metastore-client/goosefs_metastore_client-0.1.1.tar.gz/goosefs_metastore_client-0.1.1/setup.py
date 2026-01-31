from setuptools import find_packages, setup

__package_name__ = "goosefs_metastore_client"
__version__ = "0.1.1"
__repository_url__ = "https://git.woa.com/tencent-cloud-datalake/goosefs-metastore-client"

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

with open("README.md") as f:
    long_description = f.read()

setup(
    name=__package_name__,
    description="A Python client for connecting to GooseFS Table Master via gRPC",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="goosefs metastore grpc table-master database",
    version=__version__,
    url=__repository_url__,
    packages=find_packages(
        exclude=(
            "docs",
            "tests",
            "tests.*",
            "pipenv",
            "env",
            "examples",
            "htmlcov",
            ".pytest_cache",
        )
    ),
    license="Apache License 2.0",
    author="forwardxu",
    install_requires=requirements,
    extras_require={},
    python_requires=">=3.7, <4",
)
