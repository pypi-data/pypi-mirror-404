"""
==============================================================================
ส่วนที่ 0: DUKPYRA PACKAGE INITIALIZATION
==============================================================================
ไฟล์นี้คือ Entry Point ของ Python package "dukpyra"

หน้าที่หลัก:
1. กำหนด metadata ของ package (version, author)
2. Import และ export API สำหรับผู้ใช้
3. จัดระเบียบ namespace

การใช้งาน:
    # User code (โค้ดของผู้ใช้)
    import dukpyra
    app = dukpyra.app()  # ใช้ runtime
    
    # Compiler code (โค้ดของ compiler)
    from dukpyra import parse, analyze, generate_csharp
    
Python Package Structure:
    dukpyra/
        __init__.py           ← ไฟล์นี้ (จุดเริ่มต้น)
        scanner.py            ← Lexical Analysis (Scanner)
        parser.py             ← Syntax Analysis (Parser)
        ast.py                ← AST node definitions
        semantic_analyzer.py  ← Semantic Analysis
        code_generator.py     ← Target Code Generation
        cli.py                ← Command-line interface
        runtime.py            ← Runtime shim for profiling

API Design:
- Runtime API: สำหรับผู้ใช้เขียนโค้ด Dukpyra (app, raw_csharp)
- Compiler API: สำหรับ CLI และ testing (parse, analyze, generate_csharp)
==============================================================================
"""

# ==============================================================================
# ส่วนที่ 0.1: PACKAGE METADATA
# ==============================================================================
"""
Version: Semantic Versioning (MAJOR.MINOR.PATCH)
    - 0.3.0: Research build ที่รองรับ LINQ transformation
    - 0.2.x: รองรับ semantic analysis
    - 0.1.x: Basic transpilation

Author: ผู้พัฒนาโปรเจกต์วิจัย
"""
__version__ = "0.3.0"  # Current version
__author__ = "Rock"    # Project author


# ==============================================================================
# ส่วนที่ 0.2: IMPORTS - Compiler Components
# ==============================================================================
"""
Import components ที่จำเป็นสำหรับ package API

โครงสร้าง: แต่ละ module มีหน้าที่เฉพาะตาม compiler pipeline
"""

# ========== ส่วนที่ 0.2.1: Scanner (Tokenization) ==========
from .scanner import lexer
"""
lexer object สำหรับแยกโค้ดเป็น tokens
ใช้โดย: parser, debugging, testing
"""

# ========== ส่วนที่ 0.2.2: Parser (AST Construction) ==========
from .parser import parse
"""
parse(source_code) → ProgramNode
แปลง source code เป็น Abstract Syntax Tree
"""

# ========== ส่วนที่ 0.2.3: AST Node Definitions ==========
from .ast import ProgramNode, EndpointNode, FunctionDefNode, ClassDefNode
"""
Export AST node types ที่สำคัญ
ใช้โดย: testing, analysis tools, code generators
"""

# ========== ส่วนที่ 0.2.4: Semantic Analyzer ==========
from .semantic_analyzer import analyze, SemanticAnalyzer, SemanticError, SemanticWarning
"""
analyze(ast) → AnalysisResult
ตรวจสอบความถูกต้องของ AST ก่อน codegen

SemanticError: ข้อผิดพลาดที่ต้องแก้ไข
SemanticWarning: คำเตือนที่ไม่ block compilation
"""

# ========== ส่วนที่ 0.2.5: Code Generator ==========
from .code_generator import generate_csharp, CSharpCodeGenerator
"""
generate_csharp(ast) → C# source code string
แปลง AST เป็นโค้ด C# ASP.NET Core
"""


# ==============================================================================
# ส่วนที่ 0.3: IMPORTS - Runtime Components
# ==============================================================================
"""
Export runtime components สำหรับผู้ใช้

ส่วนนี้ทำให้ผู้ใช้สามารถเขียนโค้ดแบบนี้ได้:
    import dukpyra
    app = dukpyra.app()
    @app.get("/")
    def home():
        return {"message": "Hello"}
"""
from .runtime import app, raw_csharp, _runtime
"""
app(): Factory function ที่ return DukpyraRuntime instance
raw_csharp(code): Decorator สำหรับ inject C# code
_runtime: Global runtime instance (internal use)
"""


# ==============================================================================
# ส่วนที่ 0.4: PUBLIC API (__all__)
# ==============================================================================
"""
__all__ กำหนดว่า symbols ใดจะถูก export เมื่อใช้ "from dukpyra import *"

Best Practice:
    - ระบุ __all__ ชัดเจนเพื่อควบคุม namespace
    - แยกหมวดหมู่ตาม functionality
    - เรียงลำดับตาม importance (runtime → compiler)

หมายเหตุ:
    - ไม่แนะนำให้ใช้ "import *" ในโค้ดจริง
    - แต่ __all__ ยังมีประโยชน์สำหรับ documentation และ IDE autocomplete
"""
__all__ = [
    # ========== Metadata ==========
    '__version__',     # "0.3.0"
    
    # ========== Runtime API (สำหรับ User Code) ==========
    # API ที่ผู้ใช้เห็นและใช้งานตอนเขียนโค้ด Dukpyra
    'app',             # dukpyra.app() - สร้าง app instance
    'raw_csharp',      # @dukpyra.raw_csharp() - inject C# code
    '_runtime',        # Internal runtime instance (advanced use)
    
    # ========== Compiler API (สำหรับ CLI และ Testing) ==========
    
    # Lexer
    'lexer',           # Tokenizer object
    
    # Parser
    'parse',           # parse(source) → AST
    
    # AST Nodes (สำหรับ type checking และ testing)
    'ProgramNode',     # Root AST node
    'EndpointNode',    # Legacy endpoint node
    'FunctionDefNode', # Function definition node
    'ClassDefNode',    # Class definition node
    
    # Analyzer
    'analyze',         # analyze(ast) → AnalysisResult
    'SemanticAnalyzer',# Analyzer class
    'SemanticError',   # Error type
    'SemanticWarning', # Warning type
    
    # Code Generation
    'generate_csharp',      # generate_csharp(ast) → C# code
    'CSharpCodeGenerator',  # Generator class
]

# ==============================================================================
# ส่วนที่ 0.5: ตัวอย่างการใช้งาน
# ==============================================================================
"""
========== Runtime Usage (ผู้ใช้งาน Dukpyra) ==========

import dukpyra

app = dukpyra.app()

class CreateUser:
    name: str
    email: str

@app.post("/users")
def create_user(body: CreateUser):
    return {"created": True, "name": body.name}

if __name__ == "__main__":
    # Run with: dukpyra run
    pass


========== Compiler Usage (พัฒนา Compiler) ==========

from dukpyra import parse, analyze, generate_csharp

# Read source code
with open("main.py") as f:
    source = f.read()

# Parse
ast = parse(source)

# Analyze
result = analyze(ast)
if result.has_errors:
    for error in result.errors:
        print(error)
    exit(1)

# Generate C#
csharp_code = generate_csharp(ast)
print(csharp_code)


========== Testing ==========

from dukpyra import lexer, parse, SemanticAnalyzer

def test_parsing():
    code = '''
    import dukpyra
    app = dukpyra.app()
    
    @app.get("/")
    def home():
        return {"message": "Hello"}
    '''
    
    ast = parse(code)
    assert ast is not None
    assert len(ast.endpoints) == 1
    assert ast.endpoints[0].method == "GET"
"""
