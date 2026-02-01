#!/usr/bin/env python
"""PystdAPI 打包配置"""

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pystdapi",
    version="0.1.1",
    author="王伟勇",
    author_email="909094426@qq.com",
    description="纯异步 Python Web 框架，仅依赖 Python 标准库",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    url="https://gitee.com/wangweiyong/pystdapi",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    python_requires=">=3.7",
    keywords=["asgi", "web", "framework", "async", "python", "standard-library"],
)
