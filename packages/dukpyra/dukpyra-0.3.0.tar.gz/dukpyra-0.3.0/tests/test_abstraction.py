from dukpyra.parser import parse
from dukpyra.code_generator import generate_csharp
from dukpyra.ast import GenericEndpointNode

def test_generic_endpoint_structure():
    code = """
import dukpyra
app = dukpyra.app()

@app.get("/users")
def get_users():
    return {"users": []}
"""
    ast = parse(code)
    endpoint = ast.endpoints[0]
    
    # Verify AST structure is decoupled from Python decorator specifics
    assert isinstance(endpoint, GenericEndpointNode)
    assert endpoint.method == "GET"  # Normalized
    assert endpoint.path == "/users"
    assert endpoint.handler.name == "get_users"

def test_codegen_with_generic_node():
    code = """
import dukpyra
app = dukpyra.app()

@app.post("/create")
def create_thing():
    return {"id": 1}
"""
    ast = parse(code)
    csharp = generate_csharp(ast)
    
    # Verify CodeGen still works
    assert 'app.MapPost("/create"' in csharp
    assert "return Results.Ok" in csharp
