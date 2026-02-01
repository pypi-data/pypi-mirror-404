import json
import setuptools

kwargs = json.loads(
    """
{
    "name": "cdklabs.deploy-time-build",
    "version": "0.0.4",
    "description": "Run build on CDK deployment time.",
    "license": "Apache-2.0",
    "url": "https://github.com/cdklabs/deploy-time-build.git",
    "long_description_content_type": "text/markdown",
    "author": "Amazon Web Services<aws-cdk-dev@amazon.com>",
    "bdist_wheel": {
        "universal": true
    },
    "project_urls": {
        "Source": "https://github.com/cdklabs/deploy-time-build.git"
    },
    "package_dir": {
        "": "src"
    },
    "packages": [
        "cdklabs.deploy_time_build",
        "cdklabs.deploy_time_build._jsii"
    ],
    "package_data": {
        "cdklabs.deploy_time_build._jsii": [
            "deploy-time-build@0.0.4.jsii.tgz"
        ],
        "cdklabs.deploy_time_build": [
            "py.typed"
        ]
    },
    "python_requires": "~=3.9",
    "install_requires": [
        "aws-cdk-lib>=2.38.0, <3.0.0",
        "constructs>=10.0.5, <11.0.0",
        "jsii>=1.125.0, <2.0.0",
        "publication>=0.0.3",
        "typeguard==2.13.3"
    ],
    "classifiers": [
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Typing :: Typed",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved"
    ],
    "scripts": []
}
"""
)

with open("README.md", encoding="utf8") as fp:
    kwargs["long_description"] = fp.read()


setuptools.setup(**kwargs)
