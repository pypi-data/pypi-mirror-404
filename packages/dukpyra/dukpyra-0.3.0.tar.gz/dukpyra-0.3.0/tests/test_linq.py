from dukpyra.parser import parse
from dukpyra.code_generator import generate_csharp

def test_simple_map():
    code = """
import dukpyra
app = dukpyra.app()

@app.get("/test")
def test(items: list):
    return [x * 2 for x in items]
"""
    ast = parse(code)
    csharp = generate_csharp(ast)
    print(csharp)
    assert "items.Select(x => x * 2).ToList()" in csharp

def test_filter():
    code = """
import dukpyra
app = dukpyra.app()

@app.get("/test")
def test(items: list):
    return [x for x in items if x > 5]
"""
    ast = parse(code)
    csharp = generate_csharp(ast)
    print(csharp)
    assert "items.Where(x => x > 5).Select(x => x).ToList()" in csharp

def test_map_and_filter():
    code = """
import dukpyra
app = dukpyra.app()

@app.get("/test")
def test(users: list):
    return [u.name for u in users if u.active]
"""
    ast = parse(code)
    csharp = generate_csharp(ast)
    print(csharp)
    assert "users.Where(u => u.active).Select(u => u.name).ToList()" in csharp
