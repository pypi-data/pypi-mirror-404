"""
Dukpyra Compiler Unit Tests - Code Generator

Tests for the C# code generator module.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dukpyra.parser import parse
from dukpyra.code_generator import generate_csharp


class TestCodegenEndpoints:
    """Test endpoint code generation."""
    
    def test_get_endpoint(self):
        code = '''import dukpyra
app = dukpyra.app()
@app.get("/")
def home():
    return {"message": "hello"}
'''
        ast = parse(code)
        csharp = generate_csharp(ast)
        assert 'app.MapGet("/"' in csharp
        assert 'Results.Ok' in csharp
    
    def test_post_endpoint(self):
        code = '''import dukpyra
app = dukpyra.app()
@app.post("/users")
def create():
    return {"created": True}
'''
        ast = parse(code)
        csharp = generate_csharp(ast)
        assert 'app.MapPost("/users"' in csharp
    
    def test_put_endpoint(self):
        code = '''import dukpyra
app = dukpyra.app()
@app.put("/items/{id}")
def update(id: int):
    return {"id": id}
'''
        ast = parse(code)
        csharp = generate_csharp(ast)
        assert 'app.MapPut("/items/{id}"' in csharp


class TestCodegenParameters:
    """Test parameter code generation."""
    
    def test_int_parameter(self):
        code = '''import dukpyra
app = dukpyra.app()
@app.get("/users/{id}")
def get_user(id: int):
    return {"id": id}
'''
        ast = parse(code)
        csharp = generate_csharp(ast)
        assert "(int id)" in csharp
    
    def test_string_parameter(self):
        code = '''import dukpyra
app = dukpyra.app()
@app.get("/search")
def search(q: str):
    return {"query": q}
'''
        ast = parse(code)
        csharp = generate_csharp(ast)
        assert "(string q)" in csharp


class TestCodegenLiterals:
    """Test literal code generation."""
    
    def test_string_literal(self):
        code = '''import dukpyra
app = dukpyra.app()
@app.get("/")
def home():
    return {"msg": "hello"}
'''
        ast = parse(code)
        csharp = generate_csharp(ast)
        assert 'msg = "hello"' in csharp
    
    def test_number_literal(self):
        code = '''import dukpyra
app = dukpyra.app()
@app.get("/")
def home():
    return {"count": 42}
'''
        ast = parse(code)
        csharp = generate_csharp(ast)
        assert "count = 42" in csharp
    
    def test_bool_true(self):
        code = '''import dukpyra
app = dukpyra.app()
@app.get("/")
def home():
    return {"active": True}
'''
        ast = parse(code)
        csharp = generate_csharp(ast)
        assert "active = true" in csharp
    
    def test_bool_false(self):
        code = '''import dukpyra
app = dukpyra.app()
@app.get("/")
def home():
    return {"deleted": False}
'''
        ast = parse(code)
        csharp = generate_csharp(ast)
        assert "deleted = false" in csharp
    
    def test_none_literal(self):
        code = '''import dukpyra
app = dukpyra.app()
@app.get("/")
def home():
    return {"error": None}
'''
        ast = parse(code)
        csharp = generate_csharp(ast)
        assert "(object?)null" in csharp
    
    def test_list_literal(self):
        code = '''import dukpyra
app = dukpyra.app()
@app.get("/")
def home():
    return {"items": [1, 2, 3]}
'''
        ast = parse(code)
        csharp = generate_csharp(ast)
        assert "new[] { 1, 2, 3 }" in csharp


class TestCodegenClasses:
    """Test class/record code generation."""
    
    def test_record_generation(self):
        code = '''import dukpyra
app = dukpyra.app()
class User:
    name: str
    age: int
@app.get("/")
def home():
    return {"ok": True}
'''
        ast = parse(code)
        csharp = generate_csharp(ast)
        assert "public record User(string name, int age);" in csharp


class TestCodegenStructure:
    """Test overall code structure."""
    
    def test_has_builder(self):
        code = '''import dukpyra
app = dukpyra.app()
@app.get("/")
def home():
    return {"ok": True}
'''
        ast = parse(code)
        csharp = generate_csharp(ast)
        assert "WebApplication.CreateBuilder" in csharp
    
    def test_has_app_run(self):
        code = '''import dukpyra
app = dukpyra.app()
@app.get("/")
def home():
    return {"ok": True}
'''
        ast = parse(code)
        csharp = generate_csharp(ast)
        assert "app.Run();" in csharp


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
