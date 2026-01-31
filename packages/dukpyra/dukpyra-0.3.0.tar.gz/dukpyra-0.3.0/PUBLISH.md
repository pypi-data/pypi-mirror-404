# 📦 วิธี Publish Dukpyra ไป PyPI

คู่มือการ publish package ไปยัง PyPI เพื่อให้ใช้ `pip install dukpyra` ได้

---

## 📋 สิ่งที่ต้องเตรียม

1. ✅ `setup.py` - Package configuration (มีแล้ว)
2. ✅ `pyproject.toml` - Build configuration (มีแล้ว)
3. ✅ `README.md` - Package description (มีแล้ว)
4. ✅ `LICENSE` - MIT License (มีแล้ว)
5. ⏳ PyPI Account - สมัครที่ https://pypi.org

---

## 🚀 ขั้นตอนการ Publish

### Step 1: ติดตั้ง Build Tools

```bash
pip install build twine
```

### Step 2: อัปเดต Version (ถ้าจำเป็น)

แก้ไข version ใน 2 ไฟล์:
- `setup.py` → `version="0.3.0"`
- `dukpyra/__init__.py` → `__version__ = "0.3.0"`

### Step 3: Build Package

```bash
cd /home/rock/Documents/Dukpyra/dukpyra-compiler

# Clean old builds
rm -rf dist/ build/ *.egg-info

# Build new package
python -m build
```

**Output จะได้:**
```
dist/
├── dukpyra-0.3.0.tar.gz          # Source distribution
└── dukpyra-0.3.0-py3-none-any.whl  # Wheel (faster install)
```

### Step 4: ตรวจสอบ Package

```bash
# Check package metadata
twine check dist/*

# List contents (optional)
tar -tzf dist/dukpyra-0.3.0.tar.gz | head -20
```

### Step 5: สมัคร PyPI Account

1. ไป https://pypi.org/account/register/
2. สร้าง Account และ verify email
3. สร้าง **API Token**:
   - ไปที่ https://pypi.org/manage/account/token/
   - กด "Add API token"
   - Scope: Entire account (หรือ project-specific)
   - **เก็บ token ไว้!** (จะโชว์แค่ครั้งเดียว)

### Step 6: ทดสอบกับ TestPyPI (แนะนำ)

```bash
# Upload ไป TestPyPI (sandbox สำหรับทดสอบ)
twine upload --repository testpypi dist/*

# ทดสอบ install จาก TestPyPI
pip install --index-url https://test.pypi.org/simple/ dukpyra
```

> 💡 **TestPyPI** คือ sandbox สำหรับทดสอบก่อน publish จริง
> สมัครแยกที่: https://test.pypi.org/account/register/

### Step 7: Publish ไป PyPI (จริง!)

```bash
twine upload dist/*
```

จะถามหา credentials:
- Username: `__token__`
- Password: `pypi-xxxxxxxxxxxxxxxx` (API token ที่สร้างไว้)

### Step 8: ทดสอบ Install

```bash
# Install จาก PyPI
pip install dukpyra

# ตรวจสอบ
dukpyra --version
python -c "import dukpyra; print(dukpyra.__version__)"
```

---

## 🔧 การตั้งค่า Credentials (Optional)

สร้างไฟล์ `~/.pypirc` เพื่อไม่ต้องใส่ token ทุกครั้ง:

```ini
[distutils]
index-servers = 
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-xxxxxxxxxxxxxxxxxxxxxxxx

[testpypi]
username = __token__
password = pypi-xxxxxxxxxxxxxxxxxxxxxxxx
```

```bash
chmod 600 ~/.pypirc  # ป้องกันคนอื่นอ่าน
```

---

## 📝 Checklist ก่อน Publish

- [ ] Version number ถูกต้อง
- [ ] README.md สมบูรณ์
- [ ] LICENSE มี
- [ ] Tests ผ่านทั้งหมด (`pytest`)
- [ ] ลอง install ในเครื่องแล้ว (`pip install -e .`)
- [ ] ลอง upload ไป TestPyPI แล้ว

---

## 🔄 การอัปเดต Version

เมื่อต้องการ release version ใหม่:

1. อัปเดต version ใน `setup.py` และ `__init__.py`
2. Clean และ build ใหม่
3. Upload ไป PyPI

```bash
# Bump version → rebuild → upload
rm -rf dist/ build/ *.egg-info
python -m build
twine upload dist/*
```

---

## ❓ FAQ

### Q: ชื่อ `dukpyra` ถูกจองแล้ว?
A: ต้องเลือกชื่อใหม่ เช่น `dukpyra-compiler`, `py2csharp`

### Q: Upload แล้ว error "File already exists"?
A: ต้อง bump version ใหม่ (PyPI ไม่ให้ upload version ซ้ำ)

### Q: อยากให้ install ด้วย `pip install dukpyra[dev]`?
A: มีอยู่แล้วใน `setup.py` → `extras_require`

---

## 🎉 เมื่อ Publish สำเร็จ

ผู้ใช้จะสามารถ:

```bash
# Install
pip install dukpyra

# Use CLI
dukpyra init myproject
dukpyra profile  # Start profiler
dukpyra compile  # Compile to C#

# Use in code
import dukpyra
app = dukpyra.app()

@app.get("/hello")
def hello():
    return {"message": "Hello World!"}
```
