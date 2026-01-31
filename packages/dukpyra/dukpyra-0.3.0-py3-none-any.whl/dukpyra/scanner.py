"""
==============================================================================
ส่วนที่ 1: LEXER (LEXICAL ANALYZER / ตัวแยกคำ)
==============================================================================
ไฟล์นี้เป็น STAGE แรกของ Compiler Pipeline

Pipeline ทั้งหมด:
  ┌─────────┐   ┌────────┐   ┌───────┐   ┌──────────┐   ┌──────────┐
  │ Source  │──▶│ LEXER  │──▶│ Parser│──▶│ Analyzer │──▶│ CodeGen  │──▶ C#
  │ (.py)   │   │ (นี่)  │   │  (AST) │   │ (Errors) │   │(Template)│
  └─────────┘   └────────┘   └───────┘   └──────────┘   └──────────┘

หน้าที่ของ LEXER:
1. อ่านโค้ด Python ทีละตัวอักษร
2. จับกลุ่มเป็น "Token" (คำพื้นฐาน)
3. ส่ง Token stream ให้ Parser

เปรียบเทียบ:
- Lexer = "คนอ่านหนังสือ" ที่แยกตัวอักษรเป็นคำ
- Parser = "คนวิเคราะห์ไวยากรณ์" ที่ต่อคำเป็นประโยค

ตัวอย่าง:
Input:  @app.get("/users")
Tokens: [AT, ID("app"), DOT, GET, LPAREN, STRING("/users"), RPAREN]

ใช้เทคโนโลยี:
- PLY (Python Lex-Yacc): Pure Python implementation ของ lex/yacc
- Regex patterns สำหรับจับคำ
==============================================================================
"""

# ==============================================================================
# ส่วนที่ 1.0: IMPORTS
# ==============================================================================
import ply.lex as lex  # PLY Lexer library


# ==============================================================================
# ส่วนที่ 1.1: คำสงวน (RESERVED WORDS / KEYWORDS)
# ==============================================================================
"""
คำสงวนคือคำที่มีความหมายพิเศษในภาษา ห้ามใช้เป็นชื่อตัวแปร

รูปแบบ Dictionary:
  "คำในโค้ด" : "ชื่อ Token"

ตัวอย่าง:
  "import" → Token ชื่อ IMPORT
  "def" → Token ชื่อ DEF
  
ทำไมต้องมี reserved?
- เพื่อให้ Parser รู้ว่าคำนี้มีความหมายพิเศษ
- ป้องกันไม่ให้ผู้ใช้ตั้งชื่อตัวแปรซ้ำกับคำสงวน
- เพิ่มความชัดเจนในการ parse grammar
"""
reserved = {
    # ========== ส่วนที่ 1.1.1: Python Keywords ==========
    # คำสงวนพื้นฐานของ Python
    "import": "IMPORT",   # สำหรับ import dukpyra
    "def": "DEF",         # สำหรับประกาศ function
    "class": "CLASS",     # สำหรับสร้าง request/response body class
    "return": "RETURN",   # สำหรับ return ค่าจาก function
    
    # ========== ส่วนที่ 1.1.2: Boolean และ None Literals ==========
    # ค่า literal ที่มีความหมายพิเศษ
    "True": "TRUE",       # Boolean true (ต้องเป็นตัวพิมพ์ใหญ่ในขิ้นต้นใน Python)
    "False": "FALSE",     # Boolean false
    "None": "NONE",       # Null value ของ Python
    
    # ========== ส่วนที่ 1.1.3: HTTP Methods ==========
    # คำสำหรับ HTTP method decorators
    # ใช้ใน @app.get(), @app.post() ฯลฯ
    "get": "GET",         # HTTP GET - ดึงข้อมูล
    "post": "POST",       # HTTP POST - สร้างข้อมูลใหม่
    "put": "PUT",         # HTTP PUT - แก้ไขข้อมูลทั้งหมด
    "delete": "DELETE",   # HTTP DELETE - ลบข้อมูล
    "patch": "PATCH",     # HTTP PATCH - แก้ไขข้อมูลบางส่วน
    
    # ========== ส่วนที่ 1.1.4: Type Hints ==========
    # Type hints ที่ Dukpyra รองรับ
    # ใช้สำหรับกำหนด type ของ parameter และ class property
    "int": "TYPE_INT",       # Integer: ตัวเลขจำนวนเต็ม
    "str": "TYPE_STR",       # String: ข้อความ
    "float": "TYPE_FLOAT",   # Float: ตัวเลขทศนิยม
    "bool": "TYPE_BOOL",     # Boolean: true/false
    
    # ========== ส่วนที่ 1.1.5: Control Flow ==========
    # คำสงวนสำหรับ control flow (list comprehension)
    "for": "FOR",         # Loop keyword สำหรับ list comprehension
    "in": "IN",           # Membership operator
    "if": "IF",           # Conditional filter ใน list comprehension
}


# ==============================================================================
# ส่วนที่ 1.2: รายชื่อ Token ทั้งหมด (TOKEN LIST)
# ==============================================================================
"""
รายการ Token ทั้งหมดที่ Lexer สามารถผลิตได้

Token แบ่งออกเป็น 2 ประเภท:
1. Simple tokens: สัญลักษณ์และตัวดำเนินการ (เช่น (, ), +, -)
2. Complex tokens: ต้องใช้ regex หรือ function จับ (เช่น ID, NUMBER, STRING)

หมายเหตุ:
- Token ที่อยู่ใน reserved จะถูกเพิ่มเข้ามาอัตโนมัติ (บรรทัดสุดท้าย)
- Parser จะใช้รายการนี้เพื่อตรวจสอบว่า Token ถูกต้องหรือไม่
"""
tokens = [
    # ========== ส่วนที่ 1.2.1: Identifiers และ Literals ==========
    "ID",       # Identifier: ชื่อที่ผู้ใช้ตั้งเอง (เช่น app, get_user, CreateUser)
                # Pattern: ต้องขึ้นต้นด้วย a-z, A-Z, _ ตามด้วย a-z, A-Z, 0-9, _
    
    "NUMBER",   # Number literal: ตัวเลข (int หรือ float)
                # ตัวอย่าง: 42, 3.14, 100
    
    "STRING",   # String literal: ข้อความในเครื่องหมาย "" หรือ ''
                # ตัวอย่าง: "hello", '/users/{id}'
    
    # ========== ส่วนที่ 1.2.2: Parentheses และ Brackets ==========
    # ใช้สำหรับจับกลุ่ม expression และ define structures
    "LPAREN",   # Left Parenthesis: ( 
                # ใช้ใน: function call, function definition, grouping
    
    "RPAREN",   # Right Parenthesis: )
    
    "LBRACE",   # Left Brace: {
                # ใช้ใน: dictionary literal, path parameter
    
    "RBRACE",   # Right Brace: }
    
    "LBRACKET", # Left Bracket: [
                # ใช้ใน: list literal, list comprehension
    
    "RBRACKET", # Right Bracket: ]
    
    # ========== ส่วนที่ 1.2.3: Punctuation ==========
    # เครื่องหมายวรรคตอนที่มีความหมายทางไวยากรณ์
    "COLON",    # Colon: :
                # ใช้ใน: type hint (id: int), function definition, class definition
    
    "COMMA",    # Comma: ,
                # ใช้แยก: parameters, list items, dict items
    
    "AT",       # At sign: @
                # ใช้สำหรับ: decorator (@app.get)
    
    "DOT",      # Dot: .
                # ใช้สำหรับ: member access (app.get, body.name)
    
    # ========== ส่วนที่ 1.2.4: Operators ==========
    "EQUALS",   # Assignment: =
                # ใช้สำหรับ: app = dukpyra.app()
    
    "NEWLINE",  # Newline character: \n
                # สำคัญมาก! Python ใช้ newline แทน ; ในภาษาอื่น
    
    "STAR",     # Asterisk: *
                # ใช้ใน: multiplication, unpacking
    
    # ========== ส่วนที่ 1.2.5: Comparison Operators ==========
    # ใช้ใน if conditions ของ list comprehension
    "GT",       # Greater Than: >
    "LT",       # Less Than: <
    "EQ",       # Equal: ==
    "NE",       # Not Equal: !=
    "GE",       # Greater or Equal: >=
    "LE",       # Less or Equal: <=
] + list(reserved.values())  # เพิ่ม reserved words เข้าไปด้วย
# ผลลัพธ์: tokens จะมี IMPORT, DEF, CLASS, GET, POST, PUT, ... เพิ่มเข้ามา


# ==============================================================================
# ส่วนที่ 1.3: กฎการตัดคำแบบง่าย (SIMPLE TOKEN RULES)
# ==============================================================================
#
# Simple tokens ใช้ regex pattern แบบตรงไปตรงมา
# ไม่ต้องใช้ function เพราะไม่มีการประมวลผลพิเศษ
#
# รูปแบบ:
#   t_TOKENNAME = r"regex pattern"
#
# PLY จะ match pattern อัตโนมัติและสร้าง token
#
# หมายเหตุ:
# - ต้องใช้ raw string (r"...") เพื่อป้องกันปัญหา escape characters
# - ต้องใช้ backslash (\) escape สัญลักษณ์พิเศษในregex เช่น \( \) \. \*
#

# ========== ส่วนที่ 1.3.1: Parentheses และ Brackets Rules ==========
t_LPAREN = r"\("        # Match เครื่องหมาย (
t_RPAREN = r"\)"        # Match เครื่องหมาย )
t_LBRACE = r"\{"        # Match เครื่องหมาย {
t_RBRACE = r"\}"        # Match เครื่องหมาย }
t_LBRACKET = r"\["      # Match เครื่องหมาย [
t_RBRACKET = r"\]"      # Match เครื่องหมาย ]

# ========== ส่วนที่ 1.3.2: Punctuation Rules ==========
t_COLON = r":"          # Match เครื่องหมาย :
t_COMMA = r","          # Match เครื่องหมาย ,
t_AT = r"@"             # Match เครื่องหมาย @
t_DOT = r"\."           # Match เครื่องหมาย . (escape เพราะ . หมายถึง any char ใน regex)

# ========== ส่วนที่ 1.3.3: Operator Rules ==========
# หมายเหตุ: ต้อง define == ก่อน = เพราะ PLY match longest pattern first
t_EQUALS = r"="         # Match เครื่องหมาย = (assignment)
t_STAR = r"\*"          # Match เครื่องหมาย * (escape เพราะ * หมายถึง repeat ใน regex)

# ========== ส่วนที่ 1.3.4: Comparison Operators ==========
# ลำดับสำคัญ! ต้อง define operator 2 ตัวอักษรก่อน operator 1 ตัวอักษร
# มิฉะนั้น "==" จะถูก match เป็น "=" 2 ครั้ง
t_EQ = r"=="            # Equal (ต้องมาก่อน t_EQUALS)
t_NE = r"!="            # Not Equal
t_GE = r">="            # Greater or Equal (ต้องมาก่อน t_GT)
t_LE = r"<="            # Less or Equal (ต้องมาก่อน t_LT)
t_GT = r">"             # Greater Than
t_LT = r"<"             # Less Than

# ========== ส่วนที่ 1.3.5: Ignored Characters ==========
#
# ตัวอักษรที่ Lexer ควรข้าม (ไม่สร้าง token)
#
# t_ignore เป็น special variable ของ PLY
# - PLY จะข้ามตัวอักษรเหล่านี้โดยอัตโนมัติ
# - เพิ่มประสิทธิภาพเพราะไม่ต้องสร้าง token
#
# ปัจจุบัน: ข้าม space และ tab
# หมายเหตุ: ไม่ข้าม newline เพราะ Python ใช้ newline เป็นส่วนหนึ่งของ grammar
#
t_ignore = " \t"  # Ignore space และ tab character


# ==============================================================================
# ส่วนที่ 1.4: กฎการตัดคำแบบซับซ้อน (COMPLEX TOKEN RULES)
# ==============================================================================
#
# Complex tokens ต้องใช้ function เพราะ:
# 1. ต้องประมวลผลค่า (เช่น แปลง string เป็น int/float)
# 2. ต้องตรวจสอบ reserved words
# 3. ต้องอัปเดต lexer state (เช่น line number)
# 4. ต้อง skip token (เช่น comments)
#
# รูปแบบ Function:
#   def t_TOKENNAME(t):
#       r'regex pattern'
#       # ประมวลผล t.value
#       return t  # หรือ pass (สำหรับ skip)
#
# Parameters:
#   t: Token object มี attributes:
#      - t.type: ชนิดของ token
#      - t.value: ค่าของ token
#      - t.lineno: บรรทัดที่พบ token
#      - t.lexpos: ตำแหน่งใน input string
#
# หมายเหตุ:
# - PLY จะอ่าน regex จาก docstring (บรรทัดแรกของ function)
# - Function ถูกเรียงลำดับตาม docstring regex length (longest first)
#

# ==============================================================================
# ส่วนที่ 1.4.1: Comment Handler
# ==============================================================================
def t_COMMENT(t):
    r'\#.*'
    """
    จัดการ comment (บรรทัดที่ขึ้นต้นด้วย #)
    
    Regex Breakdown:
      \\#  : Match เครื่องหมาย # (escape เพราะ # เป็น special char)
      .*   : Match ตัวอักษรใดๆ จำนวนเท่าไรก็ได้จนจบบรรทัด
    
    การทำงาน:
      - Pass (ไม่ return token)
      - PLY จะข้าม comment ทั้งบรรทัด
    
    ตัวอย่าง:
      Input:  # This is a comment
      Output: (ไม่มี token, ถูกข้าม)
    
    หมายเหตุ:
      - Comment ใน Python ไม่มีผลต่อโปรแกรม
      - Parser จะไม่เห็น comment เลย
    """
    pass  # ไม่ return token ใดๆ = skip comment


# ==============================================================================
# ส่วนที่ 1.4.2: Identifier Handler
# ==============================================================================
def t_ID(t):
    r"[a-zA-Z_][a-zA-Z_0-9]*"
    """
    จับ Identifier (ชื่อตัวแปร, ชื่อ function, ชื่อ class)
    
    Regex Breakdown:
      [a-zA-Z_]         : ตัวอักษรแรกต้องเป็น a-z, A-Z, หรือ _
      [a-zA-Z_0-9]*     : ตัวถัดไปเป็น a-z, A-Z, 0-9, _ จำนวนเท่าไรก็ได้
    
    การทำงาน:
      1. Match identifier pattern
      2. ตรวจสอบว่าเป็น reserved word หรือไม่
      3. ถ้าเป็น reserved: ใช้ token type จาก reserved dict
      4. ถ้าไม่ใช่: ใช้ token type เป็น "ID"
    
    ตัวอย่าง:
      "app"     → reserved.get("app", "ID") → "ID"
      "get"     → reserved.get("get", "ID") → "GET"
      "import"  → reserved.get("import", "ID") → "IMPORT"
      "my_var"  → reserved.get("my_var", "ID") → "ID"
    
    เทคนิค:
      - ใช้ dict.get(key, default) เพื่อ lookup reserved words
      - ถ้าไม่เจอใน dict จะคืนค่า default เป็น "ID"
    """
    # ตรวจสอบว่าเป็น reserved word หรือไม่
    # ถ้าไม่ใช่ ให้เป็น ID ธรรมดา
    t.type = reserved.get(t.value, "ID")
    return t


# ==============================================================================
# ส่วนที่ 1.4.3: Number Handler
# ==============================================================================
def t_NUMBER(t):
    r"\d+\.?\d*"
    """
    จับตัวเลข (รองรับทั้ง integer และ float)
    
    Regex Breakdown:
      \\d+     : Match digit (0-9) อย่างน้อย 1 ตัว
      \\.?     : Match จุดทศนิยม (optional)
      \\d*     : Match digit หลังจุดทศนิยม (optional)
    
    ตัวอย่าง Pattern:
      42      → Match: \\d+ (no decimal point)
      3.14    → Match: \\d+ \\. \\d+
      .5      → ไม่ Match (ต้องมี digit ก่อนจุด)
      5.      → Match: \\d+ \\. (no digit after)
    
    การประมวลผล:
      1. ตรวจสอบว่ามีจุดทศนิยมหรือไม่
      2. ถ้ามี '.' → แปลงเป็น float
      3. ถ้าไม่มี → แปลงเป็น int
    
    หมายเหตุ:
      - ยังไม่รองรับเลขลบ (เช่น -5)
      - ยังไม่รองรับ scientific notation (เช่น 1e10)
      - TODO: เพิ่ม support ในอนาคต
    """
    # แปลง string เป็น number
    if '.' in t.value:
        t.value = float(t.value)  # มีจุดทศนิยม → float
    else:
        t.value = int(t.value)     # ไม่มีจุดทศนิยม → int
    return t


# ==============================================================================
# ส่วนที่ 1.4.4: String Handler
# ==============================================================================
def t_STRING(t):
    r'''(\"[^\"\\]*(?:\\.[^\"\\]*)*\"|'[^'\\]*(?:\\.[^'\\]*)*')'''
    """
    จับ String literal (รองรับทั้ง double quotes และ single quotes)
    
    Regex Breakdown (สำหรับ double quotes):
      \\"                    : Match เครื่องหมาย " เปิด
      [^\\"\\\\]*            : Match ตัวอักษรที่ไม่ใช่ " และ \\ (จำนวนเท่าไรก็ได้)
      (?:\\\\.              : Match escape sequence (\\n, \\", \\\\ ฯลฯ)
      [^\\"\\\\]*)*          : Match ตัวอักษรหลัง escape (repeat)
      \\"                    : Match เครื่องหมาย " ปิด
    
    ตัวอย่าง:
      "hello"           → Match ✓
      "hello world"     → Match ✓
      'hello'           → Match ✓
      "say \\"hi\\""    → Match ✓ (escaped quotes)
      "line1\\nline2"   → Match ✓ (escape sequence)
    
    การประมวลผล:
      - ตัดเครื่องหมาย quote (ตัวแรกและตัวสุดท้าย) ออก
      - เก็บเฉพาะเนื้อหาข้างใน
    
    เทคนิค:
      - ใช้ [1:-1] เพื่อ slice string (ตัดตัวแรกและตัวสุดท้าย)
      - รองรับทั้ง "" และ '' โดยใช้ regex alternation (|)
    
    หมายเหตุ:
      - Escape sequences (\\n, \\t) จะยังอยู่ใน string
      - Python จะ interpret escape sequences ตอน compile
    """
    # ตัดเครื่องหมาย quote (ตัวแรกและตัวสุดท้าย) ออก
    # [1:-1] หมายถึง: เริ่มจาก index 1 ถึง index -1 (ตัวสุดท้ายไม่รวม)
    t.value = t.value[1:-1]
    return t


# ==============================================================================
# ส่วนที่ 1.4.5: Newline Handler
# ==============================================================================
def t_NEWLINE(t):
    r"\n+"
    """
    จับ newline characters (\\n)
    
    Regex Breakdown:
      \\n+    : Match newline อย่างน้อย 1 ตัวขึ้นไป
    
    การทำงาน:
      1. นับจำนวน newline ที่พบ
      2. อัปเดต line counter (t.lexer.lineno)
      3. Return token NEWLINE
    
    ความสำคัญ:
      - Python ใช้ newline เป็นส่วนหนึ่งของ grammar (แทน semicolon)
      - Line number ใช้สำหรับ error reporting
      - Parser ใช้ NEWLINE เพื่อจบ statement
    
    ตัวอย่าง:
      def foo():\\n    → NEWLINE token (และ lineno เพิ่ม 1)
      \\n\\n\\n          → NEWLINE token (และ lineno เพิ่ม 3)
    
    เทคนิค:
      - len(t.value) = จำนวน \\n ที่พบ
      - t.lexer.lineno เป็น global line counter
    """
    # นับจำนวน newline และอัปเดต line number
    # len(t.value) = จำนวน \\n ที่ติดกัน (เช่น "\\n\\n" = 2)
    t.lexer.lineno += len(t.value)
    return t  # ต้อง return เพราะ Python ใช้ NEWLINE ใน grammar


# ==============================================================================
# ส่วนที่ 1.4.6: Error Handler
# ==============================================================================
def t_error(t):
    """
    จัดการตัวอักษรที่ไม่รู้จัก (Lexical Error)
    
    เรียกใช้เมื่อ:
      - PLY พบตัวอักษรที่ไม่ match กับ rule ใดๆ
      - เช่น: $, %, ^, &, ~ (ใน Python ปกติใช้ แต่ Dukpyra ไม่รองรับ)
    
    การทำงาน:
      1. แสดง error message พร้อมตัวอักษรที่ผิดและบรรทัด
      2. Skip ตัวอักษรนั้น (t.lexer.skip(1))
      3. ดำเนินการต่อกับตัวอักษรถัดไป
    
    ตัวอย่าง Error:
      Input:  app = $dukpyra  ($ ไม่ valid)
      Output: Lexer Error: Unknown character '$' at line 1
    
    Parameters:
      t.value[0] : ตัวอักษรแรกที่ผิด
      t.lexer.lineno : บรรทัดปัจจุบัน
      t.lexer.skip(1) : ข้ามไป 1 ตัวอักษร
    
    หมายเหตุ:
      - ไม่ใช่ fatal error (ยัง parse ต่อได้)
      - แต่อาจทำให้ Parser error ในภายหลัง
      - อาจปรับเป็น raise exception ในอนาคต
    """
    # แสดง error message
    print(f"Lexer Error: Unknown character '{t.value[0]}' at line {t.lexer.lineno}")
    
    # ข้ามตัวอักษรที่ผิดและ parse ต่อ
    t.lexer.skip(1)


# ==============================================================================
# ส่วนที่ 1.5: สร้าง Lexer Instance
# ==============================================================================
"""
สร้าง Lexer object จาก PLY

lex.lex() จะ:
1. Scan module นี้เพื่อหา token rules (t_* และ reserved)
2. Compile regex patterns
3. สร้าง lexer state machine
4. Return lexer object พร้อมใช้งาน

การใช้งาน Lexer:
  lexer.input(source_code)  # ป้อน source code
  while True:
      tok = lexer.token()    # ดึง token ทีละตัว
      if not tok:
          break              # หมด token แล้ว
      print(tok)             # ประมวลผล token

หมายเหตุ:
  - Lexer instance นี้จะถูก import ใน parser.py
  - Parser จะใช้ lexer นี้อัตโนมัติ
  - สามารถใช้ lexer แยกเพื่อ debug ได้

Optimization:
  - อาจเพิ่ม optimize=1 สำหรับ production
  - อาจเพิ่ม debuglog สำหรับ debugging
"""
lexer = lex.lex()  # สร้าง Lexer object พร้อมใช้งาน
