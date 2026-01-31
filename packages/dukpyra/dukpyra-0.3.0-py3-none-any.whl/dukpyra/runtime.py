"""
==============================================================================
ส่วนที่ 0: DUKPYRA RUNTIME SHIM
==============================================================================
ไฟล์นี้คือ "ตัวกลาง" ที่ทำให้โค้ด Dukpyra สามารถรันได้แบบ Python จริงๆ
ก่อนที่จะถูก Compile เป็น C#

วัตถุประสงค์:
1. ให้โค้ด Dukpyra รันได้บน Python (ใช้ FastAPI)
2. เก็บข้อมูล Type ของ Parameter ขณะรันไทม์ (Runtime Type Collection)
3. รองรับ decorator @raw_csharp สำหรับใส่โค้ด C# แท้

การทำงาน:
- FastAPI เป็น required dependency (บังคับติดตั้ง)
- สร้าง FastAPI app และ wrap endpoints ด้วย type collection
- เก็บ type ของทุก argument ลง .dukpyra/types.json
==============================================================================
"""

# ==============================================================================
# ส่วนที่ 1: IMPORTS และ DEPENDENCIES
# ==============================================================================

import json          # สำหรับบันทึก type ข้อมูลเป็น JSON
import os            # สำหรับจัดการไฟล์และ directory
import inspect       # สำหรับตรวจสอบ function signature
from pathlib import Path          # สำหรับจัดการ path แบบ object-oriented
from functools import wraps       # สำหรับสร้าง decorator ที่เก็บ metadata
from typing import Optional, Any, Callable  # Type hints

# ==============================================================================
# ส่วนที่ 1.1: ตรวจสอบ FastAPI (Required Dependency)
# ==============================================================================
# FastAPI เป็น required dependency สำหรับ Runtime Type Collection
# ถ้าไม่มี FastAPI จะ raise ImportError ทันที
try:
    from fastapi import FastAPI
except ImportError:
    raise ImportError(
        "\n\n"
        "╔══════════════════════════════════════════════════════════════════╗\n"
        "║  ❌ FastAPI is required for Dukpyra Runtime Type Collection     ║\n"
        "╠══════════════════════════════════════════════════════════════════╣\n"
        "║  Please install FastAPI:                                         ║\n"
        "║                                                                  ║\n"
        "║    pip install 'dukpyra[runtime]'                                ║\n"
        "║                                                                  ║\n"
        "║  Or install manually:                                            ║\n"
        "║                                                                  ║\n"
        "║    pip install fastapi uvicorn                                   ║\n"
        "╚══════════════════════════════════════════════════════════════════╝\n"
    )


# ==============================================================================
# ส่วนที่ 2: CLASS DukpyraRuntime (หัวใจหลักของ Runtime)
# ==============================================================================
class DukpyraRuntime:
    """
    ส่วนที่ 2.1: คำอธิบาย Class
    
    DukpyraRuntime เป็น class ที่ทำหน้าที่เป็น "ตัวกลาง" ระหว่าง
    โค้ด Dukpyra กับ FastAPI runtime
    
    หน้าที่หลัก:
    1. สร้าง FastAPI app instance (ถ้ามี FastAPI)
    2. Wrap ทุก endpoint function เพื่อเก็บข้อมูล type
    3. บันทึก type ที่เก็บได้ลง .dukpyra/types.json
    
    ตัวอย่างการใช้งาน:
        import dukpyra
        app = dukpyra.app()  # สร้าง DukpyraRuntime instance
        
        @app.get("/users/{id}")
        def get_user(id: int):
            return {"id": id}
    """
    
    # ==========================================================================
    # ส่วนที่ 2.2: Constructor (__init__)
    # ==========================================================================
    def __init__(self):
        """
        สร้าง DukpyraRuntime instance ใหม่
        
        การทำงาน:
        1. สร้าง FastAPI() instance ถ้ามี FastAPI installed
        2. เตรียม dictionary สำหรับเก็บ type ข้อมูล
        3. กำหนด path ของไฟล์ที่จะบันทึก type
        """
        # สร้าง FastAPI app (บังคับมี)
        self.app = FastAPI()
        
        # Dictionary สำหรับเก็บ type ข้อมูล
        # รูปแบบ: {
        #   "function_name": {
        #     "param_name": "type_name",
        #     ...
        #   },
        #   ...
        # }
        self.collected_types = {}
        
        # Path ของไฟล์ที่จะบันทึก type ข้อมูล
        self.types_file = Path(".dukpyra/types.json")

    # ==========================================================================
    # ส่วนที่ 2.3: เก็บข้อมูล Type (_collect_type)
    # ==========================================================================
    # ==========================================================================
    # ส่วนที่ 2.3: เก็บข้อมูล Type (Runtime Type Collection)
    # ==========================================================================
    # ตามงานวิจัย [6] Krivanek & Uttner: "Runtime type collecting and 
    # transpilation to a static language"
    # 
    # แนวทาง: เก็บ type ที่สังเกตได้จริงขณะรันไทม์ เพื่อแปลง dynamic Python
    # เป็น static C# ได้อย่างแม่นยำ
    # ==========================================================================
    
    def _infer_type(self, value: Any) -> str:
        """
        ส่วนที่ 2.3.1: Infer Type จากค่าจริง (Core Type Inference)
        
        แปลง Python value → Type name string ด้วย runtime introspection
        รองรับ nested types ตามงานวิจัย [6]
        
        พารามิเตอร์:
            value: ค่าที่ต้องการ infer type
        
        Returns:
            Type name string (เช่น "int", "List[str]", "Dict[str, int]", "User")
        
        Priority Order (สำคัญ!):
            1. bool (ก่อน int เพราะ bool เป็น subclass ของ int)
            2. Primitive types (int, float, str)
            3. Collections (list, dict) → Infer element types
            4. Custom classes → ใช้ class name
            5. None → "None"
            6. Unknown → "dynamic"
        """
        # Check None first
        if value is None:
            return "None"
        
        # Bool must be checked before int (bool is subclass of int)
        if isinstance(value, bool):
            return "bool"
        
        # Primitive types
        if isinstance(value, int):
            return "int"
        if isinstance(value, float):
            return "float"
        if isinstance(value, str):
            return "str"
        
        # Collection types - Nested inference (งานวิจัย [6])
        if isinstance(value, list):
            return self._infer_list_type(value)
        
        if isinstance(value, dict):
            return self._infer_dict_type(value)
        
        # Custom class detection
        if hasattr(value, '__class__'):
            class_module = value.__class__.__module__
            # ถ้าไม่ใช่ builtin class = custom class
            if class_module not in ('builtins', '__builtin__'):
                return value.__class__.__name__  # "CreateUser", "Product"
        
        # Fallback to dynamic (unknown type)
        return "dynamic"
    
    def _infer_list_type(self, lst: list) -> str:
        """
        ส่วนที่ 2.3.2: Infer List Element Type
        
        ตามงานวิจัย [6]: Sample elements เพื่อ infer type ของ collection
        
        Strategy:
            - ถ้า list ว่าง → "List[dynamic]"
            - ถ้ามี elements → sample ตัวแรกเพื่อ infer element type
            - Future: อาจ sample หลายตัวเพื่อ detect type conflicts
        
        Returns:
            "List[element_type]" เช่น "List[int]", "List[User]"
        """
        if len(lst) == 0:
            return "List[dynamic]"  # Empty list - ไม่รู้ element type
        
        # Sample first element to infer type
        first_elem = lst[0]
        elem_type = self._infer_type(first_elem)
        
        return f"List[{elem_type}]"
    
    def _infer_dict_type(self, dct: dict) -> str:
        """
        ส่วนที่ 2.3.3: Infer Dictionary Key/Value Types
        
        ตามงานวิจัย [6]: Infer types ของ key และ value
        
        Strategy:
            - ถ้า dict ว่าง → "Dict[dynamic, dynamic]"
            - ถ้ามี items → sample คู่แรกเพื่อ infer types
        
        Returns:
            "Dict[key_type, value_type]" เช่น "Dict[str, int]"
        """
        if len(dct) == 0:
            return "Dict[dynamic, dynamic]"
        
        # Sample first key-value pair
        first_key = next(iter(dct.keys()))
        first_val = dct[first_key]
        
        key_type = self._infer_type(first_key)
        val_type = self._infer_type(first_val)
        
        return f"Dict[{key_type}, {val_type}]"
    
    def _collect_type(self, func_name: str, arg_name: str, value: Any):
        """
        ส่วนที่ 2.3.4: บันทึก Type Observation
        
        บันทึก type ที่สังเกตได้จริงขณะรันไทม์ (Runtime Type Collection)
        ตามวิธีการของงานวิจัย [6] Krivanek & Uttner
        
        พารามิเตอร์:
            func_name: ชื่อของ function (เช่น "get_user")
            arg_name: ชื่อของ parameter (เช่น "id", "users")
            value: ค่าที่ส่งเข้ามาจริง (ใช้สำหรับ infer type)
        
        การทำงาน:
        1. Infer type จากค่าจริงด้วย _infer_type() (รองรับ nested types)
        2. Track type observations (สำหรับ detect conflicts)
        3. บันทึกลง self.collected_types
        4. เขียนลงไฟล์ .dukpyra/types.json
        
        Type Conflict Handling:
        - ถ้า function ถูกเรียกหลายครั้งด้วย types ต่างกัน
        - จะเก็บทุก type ที่สังเกตได้ไว้
        - CodeGen จะ resolve conflict ภายหลัง (ใช้ dynamic หรือ union type)
        
        ตัวอย่าง:
            _collect_type("get_user", "id", 42)
            → types.json: {"get_user": {"id": "int"}}
            
            _collect_type("filter_users", "users", [User(), User()])
            → types.json: {"filter_users": {"users": "List[User]"}}
        """
        # ============== ส่วนที่ 2.3.4.1: Infer Type ==============
        # ใช้ enhanced type inference (รองรับ nested types และ custom classes)
        type_name = self._infer_type(value)
        
        # ============== ส่วนที่ 2.3.4.2: Track Observations ==============
        # Initialize type observations tracking (สำหรับ detect conflicts)
        if not hasattr(self, 'type_observations'):
            self.type_observations = {}
        
        if func_name not in self.type_observations:
            self.type_observations[func_name] = {}
        
        if arg_name not in self.type_observations[func_name]:
            self.type_observations[func_name][arg_name] = []
        
        # เก็บ type ถ้ายังไม่เคยเห็น
        if type_name not in self.type_observations[func_name][arg_name]:
            self.type_observations[func_name][arg_name].append(type_name)
        
        # ============== ส่วนที่ 2.3.4.3: บันทึก Resolved Type ==============
        # สร้าง nested dictionary ถ้ายังไม่มี
        if func_name not in self.collected_types:
            self.collected_types[func_name] = {}
        
        # บันทึก type (ใช้วิธี "last observed" - อาจปรับเป็น conflict resolution)
        # TODO: ในอนาคตอาจใช้ voting หรือ most common type
        self.collected_types[func_name][arg_name] = type_name
        
        # ============== ส่วนที่ 2.3.4.4: บันทึกลงไฟล์ ==============
        # บันทึกลงไฟล์ทันที (สำหรับ real-time profiling)
        # งานวิจัย [6]: Runtime data ต้อง persist สำหรับ transpilation
        self._save_types()

    # ==========================================================================
    # ส่วนที่ 2.4: บันทึกลงไฟล์ (_save_types)
    # ==========================================================================
    def _save_types(self):
        """
        ส่วนที่ 2.4.1: บันทึก Runtime Type Data
        
        บันทึก type data ลงไฟล์ .dukpyra/types.json
        ตามงานวิจัย [6]: Runtime data ต้อง persist สำหรับการ transpile
        
        การทำงาน:
        1. สร้าง directory .dukpyra/ ถ้ายังไม่มี
        2. เขียน collected types และ observations เป็น JSON
        3. Format แบบ pretty-print เพื่อ human-readable
        
        รูปแบบไฟล์ (Enhanced):
        {
          "types": {
            "get_user": {
              "id": "int"
            },
            "filter_users": {
              "users": "List[User]"
            }
          },
          "observations": {
            "get_user": {
              "id": ["int"]
            },
            "filter_users": {
              "users": ["List[User]"]
            }
          },
          "metadata": {
            "version": "0.3.0",
            "method": "runtime_profiling"
          }
        }
        
        หมายเหตุ:
        - types: Final resolved types (ใช้โดย CodeGen)
        - observations: Raw type observations (สำหรับ debug/analysis)
        - metadata: Version และ method information
        """
        # สร้าง directory .dukpyra/ ถ้ายังไม่มี
        self.types_file.parent.mkdir(exist_ok=True, parents=True)
        
        # Prepare data structure (Enhanced format)
        data = {
            "types": self.collected_types,
            "observations": getattr(self, 'type_observations', {}),
            "metadata": {
                "version": "0.3.0",
                "method": "runtime_profiling",
                "research_ref": "[6] Krivanek & Uttner - Runtime type collecting"
            }
        }
        
        # เขียน JSON file แบบ pretty-print (indent=2)
        with open(self.types_file, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # ==========================================================================
    # ส่วนที่ 2.5: Wrap Handler Function (_wrap_handler)
    # ==========================================================================
    def _wrap_handler(self, func):
        """
        Wrap endpoint function เพื่อเก็บ type ข้อมูลก่อนเรียก
        
        พารามิเตอร์:
            func: endpoint function ที่จะ wrap
        
        Return:
            wrapper function ที่เก็บ type ก่อนเรียก func()
        
        การทำงาน:
        1. ใช้ inspect.signature() ดึง parameter names
        2. ใช้ sig.bind() แปลง args/kwargs เป็น named arguments
        3. เก็บ type ของแต่ละ argument
        4. เรียก function จริง (รองรับทั้ง sync และ async)
        
        หมายเหตุ:
        - ใช้ @wraps(func) เพื่อเก็บ metadata ของ function เดิม
        - รองรับทั้ง async และ sync functions
        """
        # ใช้ @wraps เพื่อเก็บ __name__, __doc__ ของ function เดิม
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # ============== ส่วนที่ 2.5.1: Inspect Signature ==============
            # ดึง function signature (parameter names และ types)
            sig = inspect.signature(func)
            
            # Bind args และ kwargs เข้ากับ parameter names
            # ทำให้เราได้ชื่อของแต่ละ parameter
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()  # ใส่ค่า default ถ้ามี
            
            # ============== ส่วนที่ 2.5.2: Collect Types ==============
            # วนลูปเก็บ type ของแต่ละ argument
            for name, value in bound.arguments.items():
                self._collect_type(func.__name__, name, value)
            
            # ============== ส่วนที่ 2.5.3: Call Original Function ==============
            # เรียก function จริง (รองรับทั้ง async และ sync)
            if inspect.iscoroutinefunction(func):
                # ถ้าเป็น async function ใช้ await
                return await func(*args, **kwargs)
            else:
                # ถ้าเป็น sync function เรียกตรงๆ
                return func(*args, **kwargs)
        
        return wrapper

    # ==========================================================================
    # ส่วนที่ 2.6: HTTP Method Decorators
    # ==========================================================================
    # Decorators สำหรับแต่ละ HTTP method (GET, POST, PUT, DELETE, PATCH)
    # รูปแบบเหมือนกันหมด แค่เปลี่ยน method ที่เรียก
    
    # ============== ส่วนที่ 2.6.1: GET Method ==============
    def get(self, path: str):
        """
        Decorator สำหรับ HTTP GET endpoint
        
        พารามิเตอร์:
            path: URL path (เช่น "/users/{id}")
        
        ตัวอย่าง:
            @app.get("/users/{id}")
            def get_user(id: int):
                return {"id": id}
        
        การทำงาน:
        1. สร้าง decorator function
        2. Register endpoint กับ FastAPI app.get()
        3. Wrap function ด้วย _wrap_handler() เพื่อเก็บ type
        4. Return function เดิม (สำหรับใช้งานต่อ)
        """
        def decorator(func):
            # Register endpoint กับ FastAPI app
            # และ wrap ด้วย _wrap_handler เพื่อเก็บ type
            self.app.get(path)(self._wrap_handler(func))
            return func  # Return function เดิมเพื่อให้สามารถเรียกใช้ได้
        return decorator

    # ============== ส่วนที่ 2.6.2: POST Method ==============
    def post(self, path: str):
        """
        Decorator สำหรับ HTTP POST endpoint
        
        ใช้สำหรับสร้างข้อมูลใหม่ (Create)
        """
        def decorator(func):
            self.app.post(path)(self._wrap_handler(func))
            return func
        return decorator

    # ============== ส่วนที่ 2.6.3: PUT Method ==============
    def put(self, path: str):
        """
        Decorator สำหรับ HTTP PUT endpoint
        
        ใช้สำหรับอัปเดตข้อมูลทั้งหมด (Full Update)
        """
        def decorator(func):
            self.app.put(path)(self._wrap_handler(func))
            return func
        return decorator
    
    # ============== ส่วนที่ 2.6.4: DELETE Method ==============
    def delete(self, path: str):
        """
        Decorator สำหรับ HTTP DELETE endpoint
        
        ใช้สำหรับลบข้อมูล
        """
        def decorator(func):
            self.app.delete(path)(self._wrap_handler(func))
            return func
        return decorator

    # ============== ส่วนที่ 2.6.5: PATCH Method ==============
    def patch(self, path: str):
        """
        Decorator สำหรับ HTTP PATCH endpoint
        
        ใช้สำหรับอัปเดตข้อมูลบางส่วน (Partial Update)
        """
        def decorator(func):
            self.app.patch(path)(self._wrap_handler(func))
            return func
        return decorator


# ==============================================================================
# ส่วนที่ 3: GLOBAL INSTANCE และ FACTORY FUNCTION
# ==============================================================================

# ============== ส่วนที่ 3.1: Global Runtime Instance ==============
# สร้าง DukpyraRuntime instance ตัวเดียว (Singleton pattern)
# ใช้ underscore prefix เพื่อบอกว่าเป็น internal variable
_runtime = DukpyraRuntime()


# ============== ส่วนที่ 3.2: Factory Function ==============
def app():
    """
    Factory function สำหรับดึง DukpyraRuntime instance
    
    การทำงาน:
        Return global _runtime instance
    
    ตัวอย่างการใช้งาน:
        import dukpyra
        app = dukpyra.app()  # ดึง runtime instance
        
        @app.get("/")
        def home():
            return {"message": "Hello"}
    
    หมายเหตุ:
        - ใช้ Singleton pattern (instance เดียวต่อโปรแกรม)
        - ทำให้การเรียกใช้ดูเหมือน FastAPI
        - แต่จริงๆ คือ DukpyraRuntime ที่มี type collection
    """
    return _runtime


# ==============================================================================
# ส่วนที่ 4: RAW C# DECORATOR
# ==============================================================================
def raw_csharp(code: str):
    """
    Decorator สำหรับใส่โค้ด C# แท้ลงใน Dukpyra
    
    พารามิเตอร์:
        code: โค้ด C# ที่ต้องการใส่ (string)
    
    การทำงาน:
        - ใน Runtime (Python): ทำเป็น pass-through (ไม่ทำอะไร)
        - ตอน Compile: Compiler จะดึง code string ไปใส่ในโค้ด C# จริง
    
    ตัวอย่างการใช้งาน:
        @app.get("/advanced")
        @dukpyra.raw_csharp('''
            // Custom C# code
            logger.LogInformation("Custom logging");
        ''')
        def advanced_endpoint():
            return {"status": "ok"}
    
    หมายเหตุ:
        - เป็นฟีเจอร์ "User-guided Last Mile" ตามงานวิจัย [4]
        - ใช้เมื่อ Dukpyra transpile ไม่ได้ หรือต้องการควบคุม C# เอง
        - ต้องระวังเรื่อง type safety และ compatibility
    """
    def decorator(func):
        # ใน runtime แค่ return function เดิม (ไม่ทำอะไร)
        # Compiler จะใช้ code string ตอน codegen
        return func
    return decorator
