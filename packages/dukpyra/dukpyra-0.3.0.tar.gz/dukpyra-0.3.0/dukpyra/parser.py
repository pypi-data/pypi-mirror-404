"""
Dukpyra Parser - Builds AST from Token Stream

This module uses PLY (Python Lex-Yacc) to parse Dukpyra source code
and build an Abstract Syntax Tree (AST).

Architecture:
    Source Code → Lexer → Parser → AST → CodeGen → C# Code
                          ^^^^^^
                          This module
"""

import ply.yacc as yacc

# Import tokens and lexer from lexer module
from .scanner import lexer, tokens

# Import AST node classes
from .ast import (
    ProgramNode,
    ImportNode,
    AppCreationNode,
    ClassDefNode,
    ClassPropertyNode,
    ClassPropertyNode,
    GenericEndpointNode,
    DecoratorNode,
    FunctionDefNode,
    ParameterNode,
    StringExpr,
    NumberExpr,
    BoolExpr,
    NoneExpr,
    DictExpr,
    DictItemNode,
    ListExpr,
    ListCompNode,
    BinaryOpExpr,
    IdentifierExpr,
    MemberAccessExpr,
)


# ==============================================================================
# Section 2: PARSER RULES (Grammar → AST)
# ==============================================================================


# 2.1 Program Structure
# program : preamble class_definitions endpoints
def p_program(p):
    """program : preamble class_definitions endpoints"""
    preamble = p[1] or {}
    imports = preamble.get('imports', [])
    app_creation = preamble.get('app_creation', None)
    classes = p[2] if p[2] else []
    endpoints = p[3] if p[3] else []
    
    p[0] = ProgramNode(
        imports=imports,
        app_creation=app_creation,
        classes=classes,
        endpoints=endpoints,
        lineno=1
    )


# 2.1.1 Preamble: import + app creation (or subsets)
def p_preamble_full(p):
    """preamble : optional_newlines import_stmt app_creation"""
    p[0] = {
        'imports': [p[2]] if p[2] else [],
        'app_creation': p[3]
    }


def p_preamble_with_import(p):
    """preamble : optional_newlines import_stmt"""
    p[0] = {
        'imports': [p[2]] if p[2] else [],
        'app_creation': None
    }


def p_preamble_empty(p):
    """preamble : optional_newlines"""
    p[0] = {
        'imports': [],
        'app_creation': None
    }


# 2.1.2 Import Statement: import dukpyra
def p_import_stmt(p):
    """import_stmt : IMPORT ID NEWLINE optional_newlines"""
    p[0] = ImportNode(module_name=p[2], lineno=p.lineno(1))


# 2.1.3 App Creation: app = dukpyra.app()
def p_app_creation(p):
    """app_creation : ID EQUALS ID DOT ID LPAREN RPAREN NEWLINE optional_newlines"""
    p[0] = AppCreationNode(
        var_name=p[1],
        module_name=p[3],
        func_name=p[5],
        lineno=p.lineno(1)
    )


# 2.1.4 Optional newlines
def p_optional_newlines_empty(p):
    """optional_newlines : """
    pass


def p_optional_newlines_some(p):
    """optional_newlines : NEWLINE optional_newlines"""
    pass


# ==============================================================================
# 2.1.5 Class Definitions (for Request/Response Bodies)
# ==============================================================================

def p_class_definitions_multiple(p):
    """class_definitions : class_definition class_definitions"""
    p[0] = [p[1]] + (p[2] if p[2] else [])


def p_class_definitions_empty(p):
    """class_definitions : """
    p[0] = []


def p_class_definition(p):
    """class_definition : CLASS ID COLON NEWLINE class_properties"""
    p[0] = ClassDefNode(
        name=p[2],
        properties=p[5] if p[5] else [],
        lineno=p.lineno(1)
    )


def p_class_properties_multiple(p):
    """class_properties : class_property class_properties"""
    p[0] = [p[1]] + (p[2] if p[2] else [])


def p_class_properties_single(p):
    """class_properties : class_property"""
    p[0] = [p[1]]


def p_class_property(p):
    """class_property : ID COLON type_hint NEWLINE"""
    p[0] = ClassPropertyNode(
        name=p[1],
        type_hint=p[3],
        lineno=p.lineno(1)
    )


# 2.2 Endpoints: one or more endpoint definitions
def p_endpoints_multiple(p):
    """endpoints : endpoint endpoints"""
    p[0] = [p[1]] + (p[2] if p[2] else [])


def p_endpoints_single(p):
    """endpoints : endpoint"""
    p[0] = [p[1]]


# 2.3 Endpoint: decorator + function
def p_endpoint(p):
    """endpoint : decorator function_def"""
    # Transform decorator + function into a Generic Node immediately
    # This abstracts away the "decorator" concept from the main AST
    decorator = p[1]
    function = p[2]
    
    p[0] = GenericEndpointNode(
        method=decorator.method.upper(),
        path=decorator.path,
        handler=function,
        lineno=decorator.lineno
    )


def p_raw_decorator(p):
    """raw_decorator : AT ID DOT ID LPAREN STRING RPAREN NEWLINE"""
    if p[2] == 'dukpyra' and p[4] == 'raw_csharp':
        p[0] = p[6]
    else:
        p[0] = None


# 2.4 Decorators: @app.method("/path")
def p_decorator_get(p):
    """decorator : AT ID DOT GET LPAREN STRING RPAREN NEWLINE"""
    p[0] = DecoratorNode(app_name=p[2], method="get", path=p[6], lineno=p.lineno(1))


def p_decorator_post(p):
    """decorator : AT ID DOT POST LPAREN STRING RPAREN NEWLINE"""
    p[0] = DecoratorNode(app_name=p[2], method="post", path=p[6], lineno=p.lineno(1))


def p_decorator_put(p):
    """decorator : AT ID DOT PUT LPAREN STRING RPAREN NEWLINE"""
    p[0] = DecoratorNode(app_name=p[2], method="put", path=p[6], lineno=p.lineno(1))


def p_decorator_delete(p):
    """decorator : AT ID DOT DELETE LPAREN STRING RPAREN NEWLINE"""
    p[0] = DecoratorNode(app_name=p[2], method="delete", path=p[6], lineno=p.lineno(1))


def p_decorator_patch(p):
    """decorator : AT ID DOT PATCH LPAREN STRING RPAREN NEWLINE"""
    p[0] = DecoratorNode(app_name=p[2], method="patch", path=p[6], lineno=p.lineno(1))


# 2.5 Function Definition - with or without parameters
def p_function_def_with_params(p):
    """function_def : DEF ID LPAREN params RPAREN COLON NEWLINE RETURN expression NEWLINE"""
    p[0] = FunctionDefNode(
        name=p[2],
        params=p[4],
        body=p[9],
        lineno=p.lineno(1)
    )


def p_function_def_no_params(p):
    """function_def : DEF ID LPAREN RPAREN COLON NEWLINE RETURN expression NEWLINE"""
    p[0] = FunctionDefNode(
        name=p[2],
        params=[],
        body=p[8],
        lineno=p.lineno(1)
    )


# 2.5.1 Parameters: comma-separated list of typed parameters
def p_params_multiple(p):
    """params : param COMMA params"""
    p[0] = [p[1]] + p[3]


def p_params_single(p):
    """params : param"""
    p[0] = [p[1]]


# 2.5.2 Single Parameter: name: type
def p_param_typed(p):
    """param : ID COLON type_hint"""
    p[0] = ParameterNode(
        name=p[1],
        type_hint=p[3],
        lineno=p.lineno(1)
    )


def p_param_untyped(p):
    """param : ID"""
    p[0] = ParameterNode(
        name=p[1],
        type_hint=None,
        lineno=p.lineno(1)
    )


# 2.5.3 Type Hints: int, str, float, bool, or custom ID
def p_type_hint_int(p):
    """type_hint : TYPE_INT"""
    p[0] = "int"


def p_type_hint_str(p):
    """type_hint : TYPE_STR"""
    p[0] = "str"


def p_type_hint_float(p):
    """type_hint : TYPE_FLOAT"""
    p[0] = "float"


def p_type_hint_bool(p):
    """type_hint : TYPE_BOOL"""
    p[0] = "bool"


def p_type_hint_custom(p):
    """type_hint : ID"""
    p[0] = p[1]


# 2.6 Expressions
# ==============================================================================

def p_expression_string(p):
    """expression : STRING"""
    p[0] = StringExpr(value=p[1], lineno=p.lineno(1))


def p_expression_number(p):
    """expression : NUMBER"""
    p[0] = NumberExpr(value=p[1], lineno=p.lineno(1))


def p_expression_dict(p):
    """expression : LBRACE dict_items RBRACE"""
    p[0] = DictExpr(items=p[2], lineno=p.lineno(1))


def p_expression_empty_dict(p):
    """expression : LBRACE RBRACE"""
    p[0] = DictExpr(items=[], lineno=p.lineno(1))


def p_expression_binary_op(p):
    """expression : expression STAR expression
                  | expression GT expression
                  | expression LT expression
                  | expression EQ expression
                  | expression NE expression
                  | expression GE expression
                  | expression LE expression"""
    p[0] = BinaryOpExpr(
        left=p[1],
        op=p[2],
        right=p[3],
        lineno=p.lineno(1)
    )


# 2.6.2 List Expressions: [1, 2, 3] or ["a", "b", "c"]
def p_expression_list_comp(p):
    """expression : LBRACKET expression FOR ID IN expression optional_if RBRACKET"""
    p[0] = ListCompNode(
        expression=p[2],
        target=p[4],
        iterable=p[6],
        condition=p[7],
        lineno=p.lineno(1)
    )

def p_optional_if_present(p):
    """optional_if : IF expression"""
    p[0] = p[2]

def p_optional_if_empty(p):
    """optional_if : """
    p[0] = None

def p_expression_list(p):
    """expression : LBRACKET list_items RBRACKET"""
    p[0] = ListExpr(items=p[2], lineno=p.lineno(1))


def p_expression_empty_list(p):
    """expression : LBRACKET RBRACKET"""
    p[0] = ListExpr(items=[], lineno=p.lineno(1))


def p_list_items_multiple(p):
    """list_items : expression COMMA list_items"""
    p[0] = [p[1]] + p[3]


def p_list_items_single(p):
    """list_items : expression"""
    p[0] = [p[1]]


def p_expression_identifier(p):
    """expression : ID"""
    p[0] = IdentifierExpr(name=p[1], lineno=p.lineno(1))


# Member access: body.name, user.email
def p_expression_member_access(p):
    """expression : ID DOT ID"""
    p[0] = MemberAccessExpr(
        object_name=p[1],
        member_name=p[3],
        lineno=p.lineno(1)
    )


def p_expression_true(p):
    """expression : TRUE"""
    p[0] = BoolExpr(value=True, lineno=p.lineno(1))


def p_expression_false(p):
    """expression : FALSE"""
    p[0] = BoolExpr(value=False, lineno=p.lineno(1))


def p_expression_none(p):
    """expression : NONE"""
    p[0] = NoneExpr(lineno=p.lineno(1))


# 2.6.1 Dictionary Items
def p_dict_items_multiple(p):
    """dict_items : dict_item COMMA dict_items"""
    p[0] = [p[1]] + p[3]


def p_dict_items_single(p):
    """dict_items : dict_item"""
    p[0] = [p[1]]


def p_dict_item(p):
    """dict_item : STRING COLON expression"""
    p[0] = DictItemNode(key=p[1], value=p[3], lineno=p.lineno(1))


# ==============================================================================
# Error Handling
# ==============================================================================

def p_error(p):
    # Silent mode - errors handled at analyzer level
    pass
    # if p:
    #     print(f"Parser Error: Syntax error at '{p.value}' on line {p.lineno}")
    # else:
    #     print("Parser Error: Unexpected end of file (EOF)")


# ==============================================================================
# Create Parser
# ==============================================================================

# ==============================================================================
# Create Parser
# ==============================================================================

# Precedence rules
precedence = (
    ('left', 'EQ', 'NE', 'GT', 'LT', 'GE', 'LE'),
    ('left', 'STAR'),
)

parser = yacc.yacc()


# ==============================================================================
# Convenience Functions
# ==============================================================================

def parse(source_code: str) -> ProgramNode:
    """
    Parse Dukpyra source code and return AST.
    
    Usage:
        from dukpyra.parser import parse
        ast = parse(source_code)
    """
    # Ensure source ends with newline
    if not source_code.endswith('\n'):
        source_code += '\n'
    
    return parser.parse(source_code, lexer=lexer)


# ==============================================================================
# Testing
# ==============================================================================

if __name__ == "__main__":
    from .ast import print_ast
    from .codegen import generate_csharp
    
    test_code = """
import dukpyra

app = dukpyra.app()

@app.get("/")
def home():
    return {"message": "Hello from Dukpyra!", "version": "1.0"}

@app.get("/health")
def health_check():
    return {"status": "ok", "uptime": 9999}

@app.post("/api/users")
def create_user():
    return {"id": 1, "name": "John Doe"}
"""

    print("=== Source Code ===")
    print(test_code)
    
    print("\n=== AST ===")
    ast = parse(test_code)
    print_ast(ast)
    
    print("\n=== Generated C# ===")
    csharp = generate_csharp(ast)
    print(csharp)
