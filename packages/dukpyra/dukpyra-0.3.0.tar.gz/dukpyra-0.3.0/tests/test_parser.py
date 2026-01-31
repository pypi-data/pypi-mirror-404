"""
Dukpyra Compiler Unit Tests - Parser

Tests for the parser module that builds AST from tokens.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dukpyra.parser import parse
from dukpyra.ast import (
    ProgramNode, EndpointNode, ClassDefNode, 
    StringExpr, NumberExpr, DictExpr, ListExpr,
    BoolExpr, NoneExpr, IdentifierExpr, MemberAccessExpr
)


class TestParserBasic:
    """Test basic program parsing."""
    
    def test_empty_program(self):
        ast = parse("")
        assert ast is None or isinstance(ast, ProgramNode)
    
    def test_import_statement(self):
        code = '''import dukpyra
app = dukpyra.app()
@app.get("/")
def x():
    return {"ok": True}
'''
        ast = parse(code)
        assert isinstance(ast, ProgramNode)
        assert len(ast.imports) >= 1


class TestParserEndpoints:
    """Test endpoint parsing."""
    
    def test_get_endpoint(self):
        code = '''import dukpyra
app = dukpyra.app()
@app.get("/")
def home():
    return {"message": "hello"}
'''
        ast = parse(code)
        assert isinstance(ast, ProgramNode)
        assert len(ast.endpoints) == 1
        assert ast.endpoints[0].decorator.method == "get"
        assert ast.endpoints[0].decorator.path == "/"
    
    def test_post_endpoint(self):
        code = '''import dukpyra
app = dukpyra.app()
@app.post("/users")
def create_user():
    return {"created": True}
'''
        ast = parse(code)
        assert ast.endpoints[0].decorator.method == "post"
        assert ast.endpoints[0].decorator.path == "/users"
    
    def test_path_parameter(self):
        code = '''import dukpyra
app = dukpyra.app()
@app.get("/users/{id}")
def get_user(id: int):
    return {"id": id}
'''
        ast = parse(code)
        assert ast.endpoints[0].decorator.path == "/users/{id}"
        assert len(ast.endpoints[0].function.params) == 1
        assert ast.endpoints[0].function.params[0].name == "id"
        assert ast.endpoints[0].function.params[0].type_hint == "int"


class TestParserClasses:
    """Test class definition parsing."""
    
    def test_simple_class(self):
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
        assert isinstance(ast, ProgramNode)
        assert len(ast.classes) == 1
        assert ast.classes[0].name == "User"
        assert len(ast.classes[0].properties) == 2


class TestParserExpressions:
    """Test expression parsing."""
    
    def test_string_expression(self):
        code = '''import dukpyra
app = dukpyra.app()
@app.get("/")
def home():
    return {"msg": "hello"}
'''
        ast = parse(code)
        body = ast.endpoints[0].function.body
        assert isinstance(body, DictExpr)
        assert isinstance(body.items[0].value, StringExpr)
        assert body.items[0].value.value == "hello"
    
    def test_number_expression(self):
        code = '''import dukpyra
app = dukpyra.app()
@app.get("/")
def home():
    return {"count": 42}
'''
        ast = parse(code)
        body = ast.endpoints[0].function.body
        assert isinstance(body.items[0].value, NumberExpr)
        assert body.items[0].value.value == 42
    
    def test_list_expression(self):
        code = '''import dukpyra
app = dukpyra.app()
@app.get("/")
def home():
    return {"items": [1, 2, 3]}
'''
        ast = parse(code)
        body = ast.endpoints[0].function.body
        assert isinstance(body.items[0].value, ListExpr)
        assert len(body.items[0].value.items) == 3
    
    def test_bool_expression(self):
        code = '''import dukpyra
app = dukpyra.app()
@app.get("/")
def home():
    return {"active": True, "deleted": False}
'''
        ast = parse(code)
        body = ast.endpoints[0].function.body
        assert isinstance(body.items[0].value, BoolExpr)
        assert body.items[0].value.value == True
        assert body.items[1].value.value == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
