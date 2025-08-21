from setuptools import setup, find_packages
import os

# 读取 README 文件作为长描述
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="mcp-framework",
    version="0.1.1",
    description="一个强大且易用的 MCP (Model Context Protocol) 服务器开发框架",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(include=['mcp_framework', 'mcp_framework.*']),
    python_requires=">=3.8",
    install_requires=[
        "aiohttp>=3.8.0",
        "aiofiles>=23.0.0",
        "pydantic>=2.0.0",
        "click>=8.0.0",
        "colorama>=0.4.6",
        "psutil>=5.9.0",
        "PyInstaller>=5.0.0",  # 用于构建功能
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.991",
        ],
        "web": [
            "jinja2>=3.0.0",
            "aiohttp-jinja2>=1.5.0",
        ],
        "build": [
            "PyInstaller>=5.0.0",
            "wheel>=0.37.0",
            "twine>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mcp-framework=mcp_framework.cli:main",
            "mcp-build=mcp_framework.build:main",
        ],
    },
    include_package_data=True,
    package_data={
        "mcp_framework": [
            "web/templates/*.html",
            "web/static/*.css",
            "web/static/*.js",
            "docs/*.md",
        ],
    },
    author="MCP Framework Team",
    author_email="team@mcpframework.com",
    url="https://github.com/mcpframework/mcp_framework",
    project_urls={
        "Bug Reports": "https://github.com/mcpframework/mcp_framework/issues",
        "Source": "https://github.com/mcpframework/mcp_framework",
        "Documentation": "https://mcp-framework.readthedocs.io/",
    },
    keywords=[
        "mcp", "model-context-protocol", "server", "framework", 
        "ai", "llm", "tools", "streaming", "async", "web-server"
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Framework :: AsyncIO",
        "Operating System :: OS Independent",
    ],
    zip_safe=False,
)