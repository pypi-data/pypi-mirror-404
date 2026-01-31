"""
Dukpyra Compiler Unit Tests - Analyzer

Tests for the semantic analyzer module.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dukpyra.parser import parse
from dukpyra.semantic_analyzer import analyze


class TestAnalyzerValid:
    """Test valid code passes analysis."""
    
    def test_valid_simple_endpoint(self):
        code = '''import dukpyra
app = dukpyra.app()
@app.get("/")
def home():
    return {"message": "hello"}
'''
        ast = parse(code)
        result = analyze(ast)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_valid_path_parameter(self):
        code = '''import dukpyra
app = dukpyra.app()
@app.get("/users/{id}")
def get_user(id: int):
    return {"id": id}
'''
        ast = parse(code)
        result = analyze(ast)
        assert result.is_valid
    
    def test_valid_request_body(self):
        code = '''import dukpyra
app = dukpyra.app()
class CreateUser:
    name: str
    email: str
@app.post("/users")
def create_user(body: CreateUser):
    return {"name": body.name}
'''
        ast = parse(code)
        result = analyze(ast)
        assert result.is_valid


class TestAnalyzerDuplicates:
    """Test duplicate detection."""
    
    def test_duplicate_class_error(self):
        code = '''import dukpyra
app = dukpyra.app()
class User:
    name: str
class User:
    email: str
@app.get("/")
def home():
    return {"ok": True}
'''
        ast = parse(code)
        result = analyze(ast)
        assert not result.is_valid
        assert any(e.code == "E001" for e in result.errors)
    
    def test_duplicate_endpoint_error(self):
        code = '''import dukpyra
app = dukpyra.app()
@app.get("/")
def home1():
    return {"v": 1}
@app.get("/")
def home2():
    return {"v": 2}
'''
        ast = parse(code)
        result = analyze(ast)
        assert not result.is_valid
        assert any(e.code == "E002" for e in result.errors)


class TestAnalyzerPathParams:
    """Test path parameter validation."""
    
    def test_missing_path_param_error(self):
        code = '''import dukpyra
app = dukpyra.app()
@app.get("/users/{user_id}")
def get_user():
    return {"error": "missing param"}
'''
        ast = parse(code)
        result = analyze(ast)
        assert not result.is_valid
        assert any(e.code == "E010" for e in result.errors)
    
    def test_multiple_path_params(self):
        code = '''import dukpyra
app = dukpyra.app()
@app.get("/users/{user_id}/posts/{post_id}")
def get_post(user_id: int, post_id: int):
    return {"user": user_id, "post": post_id}
'''
        ast = parse(code)
        result = analyze(ast)
        assert result.is_valid


class TestAnalyzerUndefinedVars:
    """Test undefined variable detection."""
    
    def test_undefined_var_in_return(self):
        code = '''import dukpyra
app = dukpyra.app()
@app.get("/")
def home():
    return {"value": undefined_var}
'''
        ast = parse(code)
        result = analyze(ast)
        assert not result.is_valid
        assert any(e.code == "E020" for e in result.errors)


class TestAnalyzerTypeHints:
    """Test type hint validation."""
    
    def test_unknown_type_in_param(self):
        code = '''import dukpyra
app = dukpyra.app()
@app.post("/items")
def create(body: UnknownType):
    return {"ok": True}
'''
        ast = parse(code)
        result = analyze(ast)
        assert not result.is_valid
        assert any(e.code == "E011" for e in result.errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
