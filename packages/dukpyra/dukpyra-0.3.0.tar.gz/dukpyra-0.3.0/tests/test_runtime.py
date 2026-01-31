import pytest
import shutil
import json
from pathlib import Path
from dukpyra.runtime import DukpyraRuntime
from dukpyra.code_generator import generate_csharp
from dukpyra.parser import parse

def test_runtime_collector():
    # Setup runtime
    runtime = DukpyraRuntime()
    runtime.types_file = Path(".dukpyra/test_types.json")
    
    # Mock function recording
    runtime._collect_type("get_user", "id", 123)
    runtime._collect_type("get_user", "active", True)
    
    # Verify file created
    assert runtime.types_file.exists()
    
    # Verify content
    with open(runtime.types_file) as f:
        data = json.load(f)
        assert data["get_user"]["id"] == "int"
        assert data["get_user"]["active"] == "bool"
    
    # Cleanup
    if runtime.types_file.exists():
        runtime.types_file.unlink()

def test_codegen_uses_collected_types(monkeypatch):
    # Mock file existence and content
    mock_types = {
        "get_user": {
            "id": "int",
            "name": "str"
        }
    }
    
    # Create temp directory structure
    Path(".dukpyra").mkdir(exist_ok=True)
    with open(".dukpyra/types.json", "w") as f:
        json.dump(mock_types, f)
        
    code = """import dukpyra
app = dukpyra.app()

@app.get("/users/{id}")
def get_user(id, name):
    return {"ok": True}
"""
    # Note: id and name have NO type hints above
    
    ast = parse(code)
    # Generate C#
    csharp = generate_csharp(ast)
    
    # Cleanup
    shutil.rmtree(".dukpyra")
    
    # Assertion: Should use collected types instead of dynamic
    assert "int id" in csharp
    assert "string name" in csharp
    assert "dynamic" not in csharp
