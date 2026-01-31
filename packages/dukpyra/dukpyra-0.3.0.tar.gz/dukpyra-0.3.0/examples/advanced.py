import dukpyra
app = dukpyra.app()

@app.get("/api/numbers/squares")
def get_squares():
    return {"numbers": [1, 2, 3, 4, 5], "squares": [x * x for x in [1, 2, 3, 4, 5]], "count": 5}

@app.get("/api/numbers/doubled")
def get_doubled():
    return {"original": [1, 2, 3, 4, 5], "doubled": [x * 2 for x in [1, 2, 3, 4, 5]]}

@app.get("/api/data/list")
def get_list_data():
    return {"items": [10, 20, 30, 40, 50], "count": 5}

@app.get("/api/data/dict")
def get_dict_data():
    return {"name": "Test", "value": 42, "active": True}

@app.get("/api/nested/users")
def get_nested_users():
    return {"users": [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}], "total": 2}

@app.get("/api/nested/complex")
def get_nested_complex():
    return {"data": {"count": 100, "active": True}, "meta": {"version": "1.0"}}

@app.get("/api/bool/true")
def get_true():
    return {"value": True, "type": "boolean"}

@app.get("/api/bool/false")
def get_false():
    return {"value": False, "type": "boolean"}

@app.get("/api/bool/mixed")
def get_bool_mixed():
    return {"is_active": True, "is_deleted": False, "is_verified": True}

@app.get("/api/numbers/int")
def get_integers():
    return {"count": 100, "max": 1000, "min": 1}

@app.get("/api/numbers/float")
def get_floats():
    return {"price": 99.99, "tax": 0.07, "total": 106.99}

@app.get("/api/numbers/mixed")
def get_mixed_numbers():
    return {"integer": 42, "float_num": 3.14, "large": 1000000}

@app.get("/api/strings/simple")
def get_simple_string():
    return {"message": "Hello World", "language": "en"}

@app.get("/api/strings/multiple")
def get_multiple_strings():
    return {"first": "Hello", "second": "World", "combined": "Hello World"}

@app.get("/api/empty/list")
def get_empty_list():
    return {"items": [], "count": 0}

@app.get("/api/empty/dict")
def get_empty_dict():
    return {"data": {}, "empty": True}

@app.get("/api/large/numbers")
def get_large_numbers():
    return {"numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "count": 10}

@app.get("/api/large/strings")
def get_large_strings():
    return {"items": ["a", "b", "c", "d", "e", "f", "g", "h"], "count": 8}

@app.get("/api/complex/response")
def complex_response():
    return {"status": "success", "code": 200, "data": {"users": [{"id": 1, "name": "User1"}, {"id": 2, "name": "User2"}], "total": 2}, "meta": {"timestamp": 1735891200, "version": "1.0"}}

@app.get("/api/linq/map")
def linq_map():
    return {"squares": [n * n for n in [1, 2, 3, 4, 5]]}
