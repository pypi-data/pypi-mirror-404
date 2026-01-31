"""
==============================================================================
SETUP.PY - Python Package Configuration
==============================================================================
ไฟล์นี้เป็น configuration สำหรับ build และ distribute Python package

หน้าที่หลัก:
1. กำหนด package metadata (ชื่อ, เวอร์ชัน, author)
2. ระบุ dependencies ที่จำเป็น
3. สร้าง CLI command (dukpyra command)
4. กำหนด Python version ที่รองรับ

การใช้งาน:
    # Development install (แก้โค้ดแล้วใช้งานได้ทันที)
    pip install -e .
    
    # Production install
    pip install .
    
    # Build distribution
    python setup.py sdist bdist_wheel

Setup Tools:
    - find_packages(): หา package ทั้งหมดอัตโนมัติ
    - entry_points: สร้าง CLI command
    - classifiers: ข้อมูล metadata สำหรับ PyPI

หมายเหตุ:
    - ข้อมูล author และ URL ควรอัปเดตเป็นของจริง
    - Version ควรตรงกับ __version__ ใน __init__.py
==============================================================================
"""

from setuptools import setup, find_packages

# อ่าน README สำหรับ long_description (แสดงใน PyPI)
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    # ========== Package Identity ==========
    name="dukpyra",
    version="0.3.0",  # Research version (runtime type collection)
    author="Dukpyra Team",
    author_email="dukpyra@example.com",
    
    # ========== Description ==========
    description="Python → C# Backend Framework Compiler with Runtime Type Collection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    
    # ========== URLs ==========
    url="https://github.com/yourusername/dukpyra",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/dukpyra/issues",
        "Documentation": "https://github.com/yourusername/dukpyra",
        "Source Code": "https://github.com/yourusername/dukpyra",
    },
    
    # ========== Package Discovery ==========
    packages=find_packages(),
    
    # ========== Classifiers ==========
    classifiers=[
        "Development Status :: 4 - Beta",  # Active research implementation
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Compilers",
        "Topic :: Software Development :: Code Generators",
        "Framework :: FastAPI",
        "Typing :: Typed",
    ],
    
    # ========== Python Version ==========
    python_requires=">=3.8",
    
    # ========== Dependencies ==========
    install_requires=[
        "ply>=3.11",          # Lexer & Parser
        "jinja2>=3.0.0",      # Template engine for code generation
        "click>=8.0.0",       # CLI framework
        "fastapi>=0.100.0",   # Web framework (required for runtime)
        "uvicorn>=0.20.0",    # ASGI server
    ],
    
    # ========== Optional Dependencies ==========
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "watchdog>=3.0.0",   # Hot reload for development
        ],
    },
    
    # ========== CLI Entry Points ==========
    entry_points={
        "console_scripts": [
            "dukpyra=dukpyra.cli:main",
        ],
    },
    
    # ========== Package Data ==========
    include_package_data=True,
    
    # ========== Keywords ==========
    keywords=[
        "compiler",
        "transpiler", 
        "python",
        "csharp",
        "aspnet",
        "backend",
        "framework",
        "research",
    ],
)
