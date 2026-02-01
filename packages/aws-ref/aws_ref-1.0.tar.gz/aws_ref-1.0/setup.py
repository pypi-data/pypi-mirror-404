from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="aws-ref",
    version="1.0",
    author="Chowdhury Faizal",
    description="A CLI tool to explore AWS IAM actions and their condition key/Resource ARN format support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    py_modules=["aws_ref"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "aws-ref=aws_ref:main"
        ],
    },
    keywords="aws iam cloudformation policy condition-keys tags arn",
    project_urls={
        "Source": "https://github.com/yourusername/aws-iam-explorer",
    },
)
