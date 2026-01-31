import pytest
from dukpyra.parser import parse
from dukpyra.code_generator import generate_csharp

def test_raw_csharp_injection():
    code = """import dukpyra
app = dukpyra.app()

@dukpyra.raw_csharp('Console.WriteLine("Hello from C#!"); return Results.Ok();')
@app.get("/raw")
def raw_endpoint():
    return {"ignored": True}
"""
    ast = parse(code)
    csharp = generate_csharp(ast)
    
    assert 'app.MapGet("/raw"' in csharp
    assert 'Console.WriteLine("Hello from C#!");' in csharp
    assert 'return Results.Ok();' in csharp
    assert '"ignored"' not in csharp # Verify python body was ignored
