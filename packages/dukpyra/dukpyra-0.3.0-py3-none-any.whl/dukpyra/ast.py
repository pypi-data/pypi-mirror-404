"""
==============================================================================
ส่วนที่ 2: AST (ABSTRACT SYNTAX TREE / ต้นไม้แห่งไวยากรณ์นามธรรม)
==============================================================================
ไฟล์นี้เป็น STAGE กลางของ Compiler Pipeline

Pipeline ทั้งหมด:
  ┌─────────┐   ┌────────┐   ┌───────┐   ┌──────────┐   ┌──────────┐
  │ Source  │──▶│ Lexer  │──▶│ Parser│──▶│ Analyzer │──▶│ CodeGen  │──▶ C#
  │ (.py)   │   │ (Token)│   │ (นี่) │   │ (Errors) │   │(Template)│
  └─────────┘   └────────┘   └───────┘   └──────────┘   └──────────┘

หน้าที่ของ AST:
1. เป็นโครงสร้างข้อมูลแทนโค้ดโปรแกรม
2. Parser สร้าง AST จาก Tokens
3. Analyzer ตรวจสอบความถูกต้องของ AST
4. CodeGen แปลง AST เป็น C# code

ทฤษฎี AST:
- AST เป็น "ต้นไม้" ที่แทนโครงสร้างแห่งโปรแกรม
- แต่ละ Node = ส่วนของโค้ด (statement, expression, declaration)
- เด็กของ Node = ส่วนย่อยของโครงสร้างนั้น

ตัวอย่าง:
  โค้ด:  @app.get("/users")
         def get_users():
             return {"users": []}
  
  AST:   ProgramNode
           ├── endpoints: [GenericEndpointNode]
           │    ├── method: "GET"
           │    ├── path: "/users"
           │    └── handler: FunctionDefNode
           │         ├── name: "get_users"
           │         └── body: DictExpr
           │              └── items: [DictItemNode("users", ListExpr([]))]
           
จำนวน Node Types: 19 nodes
Design Pattern: Composite Pattern (Node เป็น base, อื่นๆ inherit)
==============================================================================
"""

# ==============================================================================
# ส่วนที่ 2.0: IMPORTS
# ==============================================================================
from dataclasses import dataclass, field  # สำหรับสร้าง class ง่ายๆ ที่เก็บข้อมูล
from typing import List, Optional, Union, Any  # Type hints


# ==============================================================================
# ส่วนที่ 2.1: BASE NODE (Node พื้นฐาน)
# ==============================================================================

@dataclass
class Node:
    """
    ส่วนที่ 2.1.1: Base class สำหรับ AST nodes ทั้งหมด
    
    เป็น parent class ที่ Node อื่นๆ ทุกตัวจะ inherit
    
    Attributes:
        lineno: บรรทัดในโค้ด source (สำหรับ error reporting)
    
    Design Pattern:
        - Composite Pattern: Node เป็น Component
        - ทำให้สามารถ traverse AST tree ได้แบบเดียวกันทุก node
    
    การใช้งาน:
        - ทุก node จะมี lineno สำหรับ error reporting
        - ตัวอย่าง: "Error at line 5: Duplicate endpoint"
    
    หมายเหตุ:
        - @dataclass ทำให้ Python สร้าง __init__, __repr__ ให้อัตโนมัติ
        - lineno = 0 เป็นค่า default
    """
    lineno: int = 0  # Line number ในโค้ด source (1-indexed)


# ==============================================================================
# ส่วนที่ 2.2: PROGRAM STRUCTURE (โครงสร้างโปรแกรม)
# ==============================================================================

@dataclass
class ProgramNode(Node):
    """
    ส่วนที่ 2.2.1: Root Node ของ AST ทั้งต้น
    
    Node นี้คือ "รากของต้นไม้" ที่ครอบคลุมโปรแกรมทั้งหมด
    
    โครงสร้าง Dukpyra Program:
        1. Preamble: import statements และ app creation
        2. Classes: class definitions สำหรับ request/response bodies
        3. Endpoints: API endpoint definitions
    
    Attributes:
        imports: รายการ ImportNode (เช่น import dukpyra)
        app_creation: AppCreationNode (เช่น app = dukpyra.app())
        classes: รายการ ClassDefNode (เช่น class CreateUser)
        endpoints: รายการ GenericEndpointNode (API endpoints)
    
    ตัวอย่าง:
        # Source code:
        import dukpyra
        app = dukpyra.app()
        
        class User:
            name: str
        
        @app.get("/users")
        def get_users():
            return {}
        
        # AST:
        ProgramNode(
            imports=[ImportNode("dukpyra")],
            app_creation=AppCreationNode("app", "dukpyra", "app"),
            classes=[ClassDefNode("User", [...])],
            endpoints=[GenericEndpointNode("GET", "/users", ...)]
        )
    
    หมายเหตุ:
        - field(default_factory=list) ทำให้แต่ละ instance มี list ของตัวเอง
        - app_creation เป็น Optional (อาจไม่มีก็ได้)
    """
    imports: List['ImportNode'] = field(default_factory=list)
    app_creation: Optional['AppCreationNode'] = None
    classes: List['ClassDefNode'] = field(default_factory=list)
    endpoints: List['GenericEndpointNode'] = field(default_factory=list)


@dataclass
class ImportNode(Node):
    """
    ส่วนที่ 2.2.2: Import Statement
    
    แทน: import dukpyra
    
    Attributes:
        module_name: ชื่อ module ที่ import (เช่น "dukpyra")
    
    การทำงานใน CodeGen:
        - โค้ด Python: import dukpyra
        - โค้ด C#: (ไม่ต้องสร้างอะไร, .NET ใช้ implicit usings)
    
    เหตุผลที่มี Node นี้:
        - เพื่อความสมบูรณ์ของ AST
        - เพื่อตรวจสอบว่า user import module ที่ถูกต้อง
        - อนาคตอาจมี import อื่นนอกจาก dukpyra
    """
    module_name: str = ""


@dataclass
class AppCreationNode(Node):
    """
    ส่วนที่ 2.2.3: App Creation Statement
    
    แทน: app = dukpyra.app()
    
    Attributes:
        var_name: ชื่อตัวแปร (เช่น "app")
        module_name: ชื่อ module (เช่น "dukpyra")
        func_name: ชื่อ function (เช่น "app")
    
    ตัวอย่าง:
        โค้ด: my_app = dukpyra.app()
        Node:  AppCreationNode(
                   var_name="my_app",
                   module_name="dukpyra",
                   func_name="app"
               )
    
    การทำงานใน CodeGen:
        - Python: app = dukpyra.app()
        - C#: var builder = WebApplication.CreateBuilder(args);
              var app = builder.Build();
    
    หมายเหตุ:
        - var_name เก็บไว้สำหรับตรวจสอบว่า decorator ใช้ชื่อตัวแปรตรงกันหรือไม่
        - เช่น ถ้า app = ..., decorator ต้องเป็น @app.get() ไม่ใช่ @foo.get()
    """
    var_name: str = ""
    module_name: str = ""
    func_name: str = ""


# ==============================================================================
# ส่วนที่ 2.3: CLASS DEFINITIONS (คำนิยาม Class)
# ==============================================================================

@dataclass
class ClassDefNode(Node):
    """
    ส่วนที่ 2.3.1: Class Definition
    
    แทน class definition สำหรับ request/response bodies
    
    Attributes:
        name: ชื่อ class
        properties: รายการ properties (ClassPropertyNode)
    
    ตัวอย่าง:
        # Python:
        class CreateUserRequest:
            name: str
            email: str
            age: int
        
        # AST:
        ClassDefNode(
            name="CreateUserRequest",
            properties=[
                ClassPropertyNode("name", "str"),
                ClassPropertyNode("email", "str"),
                ClassPropertyNode("age", "int")
            ]
        )
        
        # C# Generated:
        public record CreateUserRequest(
            string Name,
            string Email,
            int Age
        );
    
    การแปลงเป็น C#:
        - Python class → C# record (immutable reference type)
        - Lowercase → PascalCase (name → Name)
        - Type hints → C# types (str → string, int → int)
    
    เหตุผลที่ใช้ record:
        - Immutable (ข้อมูล request ไม่ควรเปลี่ยน)
        - Auto-generates constructor, equality, ToString()
        - Modern C# best practice สำหรับ DTOs
    """
    name: str = ""
    properties: List['ClassPropertyNode'] = field(default_factory=list)


@dataclass
class ClassPropertyNode(Node):
    """
    ส่วนที่ 2.3.2: Class Property
    
    แทน property ใน class พร้อม type hint
    
    Attributes:
        name: ชื่อ property
        type_hint: type annotation (str, int, float, bool, custom type)
    
    ตัวอย่าง:
        # Python:      name: str
        # AST:         ClassPropertyNode("name", "str")
        # C# output:   string Name
    
    Type mapping:
        Python → C#
        str → string
        int → int
        float → double
        bool → bool
        CustomClass → CustomClass
    
    Semantic Analysis:
        - Analyzer จะตรวจสอบว่า type_hint ถูกต้อง (built-in หรือ defined class)
        - ถ้าไม่ถูกต้อง → Error E004: Unknown type in class property
    """
    name: str = ""
    type_hint: str = ""


# ==============================================================================
# ส่วนที่ 2.4: ENDPOINT DEFINITIONS (คำนิยาม API Endpoints)
# ==============================================================================

@dataclass
class EndpointNode(Node):
    """
    ส่วนที่ 2.4.1: Endpoint Node (Legacy)
    
    แทน API endpoint แบบเก่า (ยังคู่กับ Python decorator syntax)
    
    Attributes:
        decorator: DecoratorNode (@app.get("/path"))
        function: FunctionDefNode (handler function)
        raw_csharp: โค้ด C# ที่ inject เพิ่มเติม (Optional)
    
    หมายเหตุ:
        - Node นี้เป็น legacy design
        - ปัจจุบันใช้ GenericEndpointNode แทน (platform-agnostic)
        - ยังคงไว้เพื่อ backward compatibility
    """
    decorator: 'DecoratorNode' = None
    function: 'FunctionDefNode' = None
    raw_csharp: Optional[str] = None


@dataclass
class GenericEndpointNode(Node):
    """
    ส่วนที่ 2.4.2: Generic Endpoint Node (Modern)
    
    แทน API endpoint แบบ platform-agnostic (ไม่ผูกกับ Python syntax)
    
    Design Philosophy:
        - แยก "ความหมาย" ออกจาก "ไวยากรณ์"
        - Inspired by research [2]: Platform abstraction
        - ทำให้ในอนาคตสามารถ generate code หลาย platform ได้
    
    Attributes:
        method: HTTP method (normalized เป็น uppercase: GET, POST, PUT, DELETE, PATCH)
        path: URL path (เช่น "/users/{id}")
        handler: FunctionDefNode (function ที่จัดการ request)
    
    ตัวอย่าง:
        # Python:
        @app.get("/users/{id}")
        def get_user(id: int):
            return {"id": id}
        
        # AST:
        GenericEndpointNode(
            method="GET",               # Normalized to uppercase
            path="/users/{id}",
            handler=FunctionDefNode(
                name="get_user",
                params=[ParameterNode("id", "int")],
                body=DictExpr(...)
            )
        )
        
        # C# Generated:
        app.MapGet("/users/{id}", (int id) => 
        {
            return new { id = id };
        });
    
    ข้อดีของ Platform-Agnostic:
        1. ไม่ผูกกับ decorator syntax (@app.get)
        2. สามารถ parse จาก syntax อื่นได้ (YAML, JSON)
        3. สามารถ generate ไปหลาย target ได้:
           - ASP.NET Core (C#)
           - FastAPI (Python)
           - Express.js (Node.js)
           - ฯลฯ
    
    Normalization:
        - method เก็บเป็น uppercase เสมอ (consistency)
        - "get" → "GET", "post" → "POST"
    """
    method: str = ""         # "GET", "POST", "PUT", "DELETE", "PATCH"
    path: str = ""           # URL path pattern
    handler: 'FunctionDefNode' = None   # Handler function


@dataclass  
class DecoratorNode(Node):
    """
    ส่วนที่ 2.4.3: Decorator Node
    
    แทน decorator ของ Python (@app.get("/path"))
    
    Attributes:
        app_name: ชื่อตัวแปร app (เช่น "app")
        method: HTTP method (lowercase: "get", "post", ...)
        path: URL path
    
    ตัวอย่าง:
        # Python:     @app.get("/users")
        # AST:        DecoratorNode("app", "get", "/users")
    
    หมายเหตุ:
        - ใช้ใน EndpointNode (legacy)
        - GenericEndpointNode ไม่ต้องใช้ DecoratorNode
    """
    app_name: str = ""
    method: str = ""  # "get", "post", "put", "delete", "patch"
    path: str = ""


@dataclass
class FunctionDefNode(Node):
    """
    ส่วนที่ 2.4.4: Function Definition
    
    แทน function definition (endpoint handler)
    
    Attributes:
        name: ชื่อ function
        params: รายการ parameters
        body: Expression ที่ return
    
    ตัวอย่าง:
        # Python:
        def get_user(id: int):
            return {"id": id, "name": "John"}
        
        # AST:
        FunctionDefNode(
            name="get_user",
            params=[ParameterNode("id", "int")],
            body=DictExpr([
                DictItemNode("id", IdentifierExpr("id")),
                DictItemNode("name", StringExpr("John"))
            ])
        )
        
        # C# Generated:
        (int id) => 
        {
            return new { id = id, name = "John" };
        }
    
    ข้อจำกัดปัจจุบัน:
        - รองรับแค่ return expression (ไม่มี complex logic)
        - ไม่รองรับ if/for statements
        - ไม่รองรับ local variables
        - เพียงพอสำหรับ simple API handlers
    """
    name: str = ""
    params: List['ParameterNode'] = field(default_factory=list)
    body: 'ExpressionNode' = None  # Expression ที่ return


@dataclass
class ParameterNode(Node):
    """
    ส่วนที่ 2.4.5: Function Parameter
    
    แทน parameter ของ function
    
    Attributes:
        name: ชื่อ parameter
        type_hint: type annotation (Optional)
        default_value: ค่า default (Optional)
    
    ตัวอย่าง:
        # Python:      id: int
        # AST:         ParameterNode("id", "int", None)
        
        # Python:      limit: int = 10
        # AST:         ParameterNode("limit", "int", NumberExpr(10))
    
    ประเภท Parameters:
        1. Path parameters: จาก URL path (/users/{id})
        2. Query parameters: จาก URL query (?limit=10)
        3. Body parameters: จาก request body (body: CreateUser)
    
    Semantic Analysis:
        - Analyzer ตรวจสอบว่า path parameters มี parameter ตรงกันใน function
        - ตัวอย่าง: /users/{id} แต่ function ไม่มี parameter id → Error E010
    """
    name: str = ""
    type_hint: Optional[str] = None
    default_value: Optional['ExpressionNode'] = None


# ==============================================================================
# ส่วนที่ 2.5: EXPRESSIONS (นิพจน์)
# ==============================================================================

@dataclass
class ExpressionNode(Node):
    """
    ส่วนที่ 2.5.0: Base Expression Node
    
    Base class สำหรับ expression ทุกชนิด
    
    Expression คือ:
        - โค้ดที่ "มีค่า" (คำนวณแล้วได้ผลลัพธ์)
        - ตัวอย่าง: 42, "hello", x + 5, {"key": "value"}
    
    แตกต่างจาก Statement:
        - Statement คือคำสั่ง (ทำอะไรบางอย่าง แต่ไม่ return ค่า)
        - ตัวอย่าง: import, def, class
    
    Expression Types ใน Dukpyra:
        - Literals: String, Number, Bool, None
        - Identifiers: Variable names
        - Member Access: obj.member
        - Collections: Dict, List
        - List Comprehension
        - Binary Operations: +, -, *, /, >, <, ==
    """
    pass


# ========== ส่วนที่ 2.5.1: Literal Expressions (ค่าคงที่) ==========

@dataclass
class StringExpr(ExpressionNode):
    """
    String literal: "hello" หรือ 'world'
    
    Attributes:
        value: ข้อความ (quotes ถูกตัดออกแล้วโดย lexer)
    
    ตัวอย่าง:
        # Python:     "hello"
        # AST:        StringExpr("hello")    # ไม่มี quotes
        # C# output:  "hello"
    
    หมายเหตุ:
        - Lexer ตัด quotes ออกแล้ว
        - CodeGen จะใส่ quotes กลับเมื่อ generate C#
        - รองรับ escape sequences (\n, \t, \", \\)
    """
    value: str = ""


@dataclass
class NumberExpr(ExpressionNode):
    """
    Number literal: 42 หรือ 3.14
    
    Attributes:
        value: ค่าตัวเลข (int หรือ float)
    
    ตัวอย่าง:
        # Python:     42
        # AST:        NumberExpr(42)      # เป็น int
        # C# output:  42
        
        # Python:     3.14
        # AST:        NumberExpr(3.14)    # เป็น float
        # C# output:  3.14
    
    Type Mapping:
        - Python int → C# int
        - Python float → C# double
    
    หมายเหตุ:
        - Lexer แปลง string เป็น int/float แล้ว
        - CodeGen แปลงกลับเป็น string เพื่อใส่ใน code
    """
    value: Union[int, float] = 0


@dataclass
class BoolExpr(ExpressionNode):
    """
    Boolean literal: True หรือ False
    
    Attributes:
        value: ค่า boolean (True/False)
    
    ตัวอย่าง:
        # Python:     True
        # AST:        BoolExpr(True)
        # C# output:  true         # lowercase!
    
    Type Mapping:
        - Python True → C# true
        - Python False → C# false
    
    หมายเหตุ:
        - Python ใช้ uppercase (True/False)
        - C# ใช้ lowercase (true/false)
        - CodeGen ต้อง convert
    """
    value: bool = False


@dataclass
class NoneExpr(ExpressionNode):
    """
    None literal: None
    
    ตัวอย่าง:
        # Python:     None
        # AST:        NoneExpr()
        # C# output:  null
    
    Type Mapping:
        - Python None → C# null
    
    หมายเหตุ:
        - NoneExpr ไม่มี attributes (แค่ Node เปล่าๆ)
        - CodeGen รู้ว่าต้อง output "null"
    """
    pass


# ========== ส่วนที่ 2.5.2: Reference Expressions (การอ้างอิง) ==========

@dataclass
class IdentifierExpr(ExpressionNode):
    """
    Identifier: การอ้างถึงตัวแปร
    
    Attributes:
        name: ชื่อตัวแปร
    
    ตัวอย่าง:
        # Python:     return user_id
        # AST:        IdentifierExpr("user_id")
        # C# output:  user_id
    
    การใช้งาน:
        - อ้างถึง parameter: id, user_id, limit
        - อ้างถึง local variable (future)
    
    Semantic Analysis:
        - Analyzer ตรวจสอบว่าตัวแปรถูก define แล้ว
        - ถ้าไม่มี → Error E020: Undefined variable reference
    """
    name: str = ""


@dataclass
class MemberAccessExpr(ExpressionNode):
    """
    Member Access: object.member
    
    Attributes:
        object_name: ชื่อ object
        member_name: ชื่อ member/property
    
    ตัวอย่าง:
        # Python:     body.name
        # AST:        MemberAccessExpr("body", "name")
        # C# output:  body.Name    # PascalCase!
    
    การใช้งาน:
        - เข้าถึง property ของ request body
        - ตัวอย่าง: body.name, user.email
    
    Type Mapping:
        - Python: lowercase (body.name)
        - C#: PascalCase (body.Name)
        - CodeGen ต้อง capitalize member_name
    """
    object_name: str = ""
    member_name: str = ""


# ========== ส่วนที่ 2.5.3: Collection Expressions (คอลเลกชัน) ==========

@dataclass
class DictExpr(ExpressionNode):
    """
    Dictionary Literal: {"key": "value", "count": 42}
    
    Attributes:
        items: รายการ DictItemNode (key-value pairs)
    
    ตัวอย่าง:
        # Python:
        {"id": 1, "name": "John"}
        
        # AST:
        DictExpr([
            DictItemNode("id", NumberExpr(1)),
            DictItemNode("name", StringExpr("John"))
        ])
        
        # C# Generated:
        new { id = 1, name = "John" }
    
    Type Mapping:
        - Python dict → C# anonymous object
        - Python JSON → C# object initializer
    
    C# Anonymous Object:
        - Immutable
        - Auto-generates properties
        - Perfect for API responses
    
    หมายเหตุ:
        - Key ต้องเป็น string เสมอ (Python ไม่บังคับ)
        - Value สามารถเป็น expression ใดๆ ได้
    """
    items: List['DictItemNode'] = field(default_factory=list)


@dataclass
class DictItemNode(Node):
    """
    Dictionary Item: key-value pair
    
    Attributes:
        key: ชื่อ key (string)
        value: Expression สำหรับ value
    
    ตัวอย่าง:
        # Python:     "name": "John"
        # AST:        DictItemNode("name", StringExpr("John"))
        # C# output:  name = "John"
    
    C# Output Format:
        - Python: "key": value
        - C#: key = value    # ไม่มี quotes รอบ key
    """
    key: str = ""              # Key (always string)
    value: ExpressionNode = None    # Value (any expression)


@dataclass
class ListExpr(ExpressionNode):
    """
    List Literal: [1, 2, 3] หรือ ["a", "b"]
    
    Attributes:
        items: รายการ elements (ExpressionNode)
    
    ตัวอย่าง:
        # Python:     [1, 2, 3]
        # AST:        ListExpr([NumberExpr(1), NumberExpr(2), NumberExpr(3)])
        # C# output:  new[] { 1, 2, 3 }
    
    Type Mapping:
        - Python list → C# array (new[] { ... })
        - C# จะ infer type จาก elements
    
    หมายเหตุ:
        - ปัจจุบันใช้น้อย (ส่วนใหญ่ใช้ list comprehension)
        - เตรียมไว้สำหรับ future features
    """
    items: List[ExpressionNode] = field(default_factory=list)


# ========== ส่วนที่ 2.5.4: Advanced Expressions ==========

@dataclass
class ListCompNode(ExpressionNode):
    """
    List Comprehension: [expr for target in iterable if condition]
    
    Attributes:
        expression: Expression ที่ output (เช่น x * 2)
        target: ชื่อตัวแปร loop (เช่น "x")
        iterable: Collection ที่วนลูป (เช่น "items")
        condition: Filter condition (Optional, เช่น x > 5)
    
    ตัวอย่าง:
        # Python:
        [u.name for u in users if u.active]
        
        # AST:
        ListCompNode(
            expression=MemberAccessExpr("u", "name"),
            target="u",
            iterable=IdentifierExpr("users"),
            condition=MemberAccessExpr("u", "active")
        )
        
        # C# Generated (LINQ):
        users.Where(u => u.Active).Select(u => u.Name).ToList()
    
    LINQ Transformation:
        1. ถ้ามี condition: .Where(target => condition)
        2. แปลง expression: .Select(target => expression)
        3. เพิ่ม .ToList() สำหรับ materialize
    
    ข้อดีของ LINQ:
        - Deferred execution (lazy evaluation)
        - Optimized โดย compiler
        - อ่านได้ง่าย (declarative)
        - รองรับ parallel execution (.AsParallel())
    
    เทคนิคสำคัญ:
        - ตรวจสอบว่า condition เป็น null หรือไม่
        - ถ้า null = ไม่มี filter
        - ตัวอย่าง: [x for x in items] → items.Select(x => x).ToList()
    """
    expression: ExpressionNode = None      # Output expression
    target: str = ""                       # Loop variable name
    iterable: ExpressionNode = None        # Source collection
    condition: Optional[ExpressionNode] = None  # Optional filter


@dataclass
class BinaryOpExpr(ExpressionNode):
    """
    Binary Operation: left op right
    
    Attributes:
        left: Expression ซ้าย
        op: Operator (+, -, *, /, >, <, ==, !=, >=, <=)
        right: Expression ขวา
    
    ตัวอย่าง:
        # Python:     x * 2
        # AST:        BinaryOpExpr(IdentifierExpr("x"), "*", NumberExpr(2))
        # C# output:  x * 2
        
        # Python:     age > 18
        # AST:        BinaryOpExpr(IdentifierExpr("age"), ">", NumberExpr(18))
        # C# output:  age > 18
    
    Supported Operators:
        - Arithmetic: +, -, *, /
        - Comparison: >, <, ==, !=, >=, <=
        - (ยังไม่รองรับ: %, //, **, and, or, not)
    
    Type Mapping:
        - ส่วนใหญ่เหมือนกัน Python และ C#
        - ยกเว้น:
            Python "//" (integer division) → C# "/" (ต้องระวัง)
            Python "**" (power) → C# "Math.Pow()" (ต้องแปลง)
    
    Order of Operations:
        - C# และ Python มี precedence เหมือนกัน
        - แต่ Parser ต้องสร้าง AST tree ให้ถูกต้อง
    """
    left: ExpressionNode = None     # Left operand
    op: str = ""                    # Operator symbol
    right: ExpressionNode = None    # Right operand


# ==============================================================================
# ส่วนที่ 2.6: HELPER FUNCTIONS (ฟังก์ชันช่วยเหลือ)
# ==============================================================================

def ast_to_dict(node: Node) -> dict:
    """
    ส่วนที่ 2.6.1: แปลง AST เป็น Dictionary
    
    ใช้สำหรับ:
        - Debugging: print(ast_to_dict(ast))
        - Testing: เปรียบเทียบ AST ที่ได้กับที่คาดหวัง
        - Serialization: บันทึก AST เป็น JSON
    
    Parameters:
        node: AST Node ที่ต้องการแปลง
    
    Returns:
        Dictionary representation ของ AST
    
    การทำงาน:
        1. ตรวจสอบว่าเป็น Node, list, หรือ primitive value
        2. ถ้าเป็น Node: แปลง attributes เป็น dict
        3. ถ้าเป็น list: แปลง each element
        4. ถ้าเป็น primitive: return ค่าตรงๆ
    
    ตัวอย่าง:
        ast = ProgramNode(
            imports=[ImportNode("dukpyra")],
            endpoints=[]
        )
        
        result = ast_to_dict(ast)
        # {
        #     "_type": "ProgramNode",
        #     "imports": [
        #         {"_type": "ImportNode", "module_name": "dukpyra", "lineno": 0}
        #     ],
        #     "endpoints": [],
        #     "lineno": 0
        # }
    
    เทคนิค:
        - ใช้ recursion สำหรับ nested nodes
        - เพิ่ม "_type" เพื่อระบุชนิดของ node
        - Skip attributes ที่ขึ้นต้นด้วย "_" (internal use)
    """
    # Base cases
    if node is None:
        return None
    
    if isinstance(node, list):
        # แปลง list ของ nodes
        return [ast_to_dict(item) for item in node]
    
    if not isinstance(node, Node):
        # Primitive value (str, int, etc.)
        return node
    
    # สร้าง dict representation
    result = {"_type": type(node).__name__}  # เริ่มด้วย type name
    
    # วนลูป attributes
    for field_name, field_value in node.__dict__.items():
        # Skip internal fields
        if field_name.startswith("_"):
            continue
        
        # แปลง nested nodes
        if isinstance(field_value, Node):
            result[field_name] = ast_to_dict(field_value)
        elif isinstance(field_value, list):
            result[field_name] = [ast_to_dict(item) for item in field_value]
        else:
            result[field_name] = field_value
    
    return result


def print_ast(node: Node, indent: int = 0) -> None:
    """
    ส่วนที่ 2.6.2: Pretty-print AST Tree
    
    ใช้สำหรับ:
        - Debugging: ดู AST structure อย่างสวยงาม
        - Development: ตรวจสอบว่า Parser สร้าง AST ถูกต้อง
        - Documentation: สร้างตัวอย่าง AST
    
    Parameters:
        node: AST Node ที่ต้องการ print
        indent: ระดับ indentation (ไม่ต้องระบุ, ใช้ internal)
    
    การทำงาน:
        1. แปลง AST เป็น dict ด้วย ast_to_dict()
        2. แปลง dict เป็น JSON string
        3. Print แบบ pretty-print (indent=2)
    
    Format Output:
        {
          "_type": "ProgramNode",
          "imports": [
            {
              "_type": "ImportNode",
              "module_name": "dukpyra",
              "lineno": 0
            }
          ],
          "classes": [],
          "endpoints": [],
          "lineno": 0
        }
    
    ตัวอย่างการใช้งาน:
        from dukpyra.parser import parser
        from dukpyra.ast import print_ast
        
        code = '''
        import dukpyra
        app = dukpyra.app()
        '''
        
        ast = parser.parse(code)
        print_ast(ast)
    
    หมายเหตุ:
        - indent parameter ไม่ถูกใช้ในการ implement ปัจจุบัน
        - อาจจะ refactor ในอนาคต
        - ensure_ascii=False เพื่อแสดง Thai characters ได้
    """
    import json
    # แปลง AST เป็น JSON string แบบ pretty-print
    print(json.dumps(ast_to_dict(node), indent=2, ensure_ascii=False))
