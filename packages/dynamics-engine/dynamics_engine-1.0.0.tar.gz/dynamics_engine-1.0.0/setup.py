"""
Setup script for Dynamics Engine
Dynamics Engine 설치 스크립트

산업용/상업용 독립 모듈
Industrial/Commercial Standalone Module

Author: GNJz (Qquarts)
License: MIT
Version: 1.0.0
"""

from setuptools import setup, find_packages
from pathlib import Path

# README 읽기
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="dynamics-engine",
    version="1.0.0",
    author="GNJz (Qquarts)",
    author_email="",  # 필요시 추가
    description="Cognitive Dynamics Engine - Entropy, Core Strength, Rotational Torque",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gnjz/dynamics-engine",  # 필요시 업데이트
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[],  # 표준 라이브러리만 사용 (Standard library only)
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ],
    },
    keywords=[
        "cognitive",
        "dynamics",
        "entropy",
        "core-strength",
        "torque",
        "ai",
        "edge-ai",
        "neuroscience",
        "cognitive-modeling",
    ],
    project_urls={
        "Documentation": "https://github.com/gnjz/dynamics-engine#readme",
        "Source": "https://github.com/gnjz/dynamics-engine",
        "Tracker": "https://github.com/gnjz/dynamics-engine/issues",
    },
)

