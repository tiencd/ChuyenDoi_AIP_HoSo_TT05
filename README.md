# AIP Builder v2.0 - Hệ thống Chuyển đổi Hồ sơ Điện tử theo TT 05/2025/TT-BNV

## 🎯 Tổng quan

AIP Builder v2.0 là hệ thống hoàn chỉnh để chuyển đổi metadata Excel và file PDF thành các gói AIP (Archival Information Package) tuân thủ đầy đủ chuẩn CSIP 1.2 và quy định Việt Nam TT 05/2025/TT-BNV.

## ✨ Tính năng nổi bật v2.0

### 🆕 **Cấu trúc AIP theo OBJID**
- **Tên thư mục AIP**: Lấy từ METS `@OBJID` (thay `:` → `_`)
- **Ví dụ**: `urn_uuid_a1b2c3d4-e5f6-7890-abcd-ef1234567890`
- **Cấu trúc**: Đặt trong đường dẫn hồ sơ gốc `Chi cuc.../hopso01/hoso01/urn_uuid_xxx/`

### 🤖 **Interactive Mode**
- **Auto-detect**: Tự động kích hoạt khi chạy không có tham số
- **User-friendly**: Prompt nhập từng tham số với giá trị mặc định
- **Validation**: Kiểm tra đường dẫn và tham số realtime
- **Smart defaults**: Sử dụng config và timestamp tự động

### 🗂️ **Bảo toàn Đường dẫn Tương đối**
- **Output structure**: Giữ nguyên cấu trúc từ input `PDF_Files/`
- **Timestamp directory**: Tự động tạo `data/output_YYYYMMDD_HHMMSS/`
- **Ví dụ**: `output_20250823_064121/Chi cuc an toan ve sinh thuc pham/hopso01/hoso01/`

### 🧹 **Cleanup Mode**
- **Option**: `--cleanup/--no-cleanup` (mặc định: không xóa)
- **Chức năng**: Xóa folder AIP sau khi tạo ZIP để tiết kiệm dung lượng
- **Kết quả**: Chỉ giữ lại file ZIP với tên từ OBJID

### 🛡️ **CSIP 1.2 Compliance Hoàn chỉnh**
- **Package-level**: METS.xml, EAD.xml, PREMIS.xml, schemas/
- **Representation-level**: rep1/METS.xml, EAD_doc_*.xml, **PREMIS_rep1.xml** ✨
- **Cấu trúc**: `representations/rep1/metadata/preservation/PREMIS_rep1.xml`

## 🏗️ Kiến trúc Hệ thống

### Các thành phần chính

1. **Data Processing Layer** (`models.py`, `excel_reader.py`, `pdf_probe.py`)
   - Đọc và validate metadata từ file Excel 
   - Phân tích thông tin file PDF
   - Chuyển đổi dữ liệu sang định dạng chuẩn

2. **XML Generation Layer** (`xml_generator.py`, `templates/`)
   - Tạo XML metadata theo chuẩn METS, EAD, PREMIS
   - Template engine với Jinja2
   - Tuân thủ chuẩn CSIP 1.2

3. **Package Building Layer** (`package_builder.py`)
   - Tạo cấu trúc thư mục AIP theo chuẩn CSIP
   - Sao chép file PDF và tạo checksum
   - Quản lý metadata và tham chiếu

4. **Validation Engine** (`validator.py`)
   - Kiểm tra tuân thủ chuẩn CSIP
   - Validate XML schema
   - Kiểm tra tính nhất quán dữ liệu

5. **Batch Processing** (`batch_processor.py`)
   - Xử lý song song nhiều package
   - Progress monitoring
   - Error handling và recovery

6. **Enhanced Error Handling** (`error_handling.py`)
   - Quản lý lỗi nâng cao
   - Logging chi tiết
   - Recovery mechanisms

### Chuẩn tuân thủ

- **OAIS (Open Archival Information System)**
- **CSIP (Common Specification for Information Packages) v1.2**
- **TT 05/2025/TT-BNV** - Quy định về lưu trữ hồ sơ điện tử Việt Nam

## Cài đặt

## 📦 Cài đặt

### Yêu cầu hệ thống

- Python 3.11+
- Windows/Linux/macOS
- RAM: 4GB+ (khuyến nghị 8GB+)
- Disk: 10GB+ free space

### Cài đặt dependencies

```bash
pip install -r requirements.txt
```

## 📁 Cấu trúc Dữ liệu

### Input Structure
```
data/Input/
├── metadata.xlsx              # File metadata Excel
└── PDF_Files/                # Thư mục chứa PDF gốc
    └── Chi cuc an toan ve sinh thuc pham/
        └── hopso01/
            ├── hoso01/
            │   ├── 001.03.08.H30.81.2024.K4.01.01.001.pdf
            │   ├── 002.pdf
            │   └── ...
            ├── hoso02/
            └── hoso03/
```

### Output Structure (v2.0)
```
data/output_20250823_064121/   # Timestamp directory
└── Chi cuc an toan ve sinh thuc pham/  # Giữ nguyên cấu trúc gốc
    └── hopso01/
        ├── hoso01/
        │   ├── urn_uuid_xxx.zip              # ZIP file (tên từ OBJID)
        │   └── urn_uuid_xxx/                 # AIP folder (nếu không --cleanup)
        │       ├── METS.xml
        │       ├── metadata/
        │       │   ├── descriptive/EAD.xml
        │       │   └── preservation/PREMIS.xml
        │       ├── representations/rep1/
        │       │   ├── METS.xml
        │       │   ├── data/*.pdf
        │       │   └── metadata/
        │       │       ├── descriptive/EAD_doc_*.xml
        │       │       └── preservation/PREMIS_rep1.xml  🆕
        │       └── schemas/*.xsd
        ├── hoso02/
        └── hoso03/
```

## 🚀 Sử dụng

### 🤖 Interactive Mode (Mới trong v2.0)

**Cách 1: Gọi trực tiếp**
```bash
python -m aip_builder interactive
```

**Cách 2: Auto-detect (chạy build không tham số)**
```bash
python -m aip_builder build
# → Tự động chuyển sang interactive mode nếu không có tham số
```

**Giao diện Interactive:**
```
🚀 AIP Builder v2.0 - Interactive Mode
============================================================
Vui lòng nhập các thông tin sau (Enter để sử dụng giá trị mặc định):

📊 File metadata Excel:
Đường dẫn file metadata.xlsx (mặc định: data/input/metadata.xlsx): 

📁 Thư mục PDF:
Đường dẫn thư mục chứa PDF (mặc định: data/input/PDF_Files): 

💾 Thư mục output:
Đường dẫn thư mục output (mặc định: data/output_20250823_065902): 

🧹 Tùy chọn cleanup:
Giữ lại thư mục sau khi tạo ZIP? (y/n, mặc định: y): 

⚡ Tùy chọn xử lý song song:
Số worker song song (mặc định: 4): 
```

### 🎯 Lệnh Cơ bản

#### 1. Build AIP Packages (v2.0)

```bash
# Cơ bản - Tự động tạo timestamp output directory
python -m aip_builder build --meta data/Input/metadata.xlsx --pdf-root data/Input/PDF_Files

# Với cleanup mode (xóa folder sau khi tạo ZIP)
python -m aip_builder build --meta data/Input/metadata.xlsx --pdf-root data/Input/PDF_Files --cleanup

# Chỉ định output directory
python -m aip_builder build --meta data/Input/metadata.xlsx --pdf-root data/Input/PDF_Files --output data/custom_output

# Giới hạn số lượng hồ sơ (test)
python -m aip_builder build --meta data/Input/metadata.xlsx --pdf-root data/Input/PDF_Files --limit 5
```

#### 2. Advanced Commands

```bash
# Batch processing song song
python -m aip_builder batch-build \
    --meta data/Input/metadata.xlsx \
    --pdf-root data/Input/PDF_Files \
    --output data/batch_output \
    --max-workers 4

# Validation
python -m aip_builder validate-packages --packages-root data/output_20250823_064121
```

### ⚙️ Các Options Quan trọng

| Option | Mặc định | Mô tả |
|--------|----------|-------|
| `--interactive` | Auto-detect | Bắt buộc chế độ tương tác (prompt nhập tham số) |
| `--no-interactive` | - | Tắt chế độ tương tác (sử dụng CLI thuần túy) |
| `--cleanup` | `--no-cleanup` | Xóa folder AIP sau khi tạo ZIP (tiết kiệm dung lượng) |
| `--output` | `data/output_[timestamp]` | Thư mục output tùy chỉnh |
| `--limit` | `None` | Giới hạn số hồ sơ xử lý (cho test) |
| `--meta` | `data/input/metadata.xlsx` | Đường dẫn file Excel metadata |
| `--pdf-root` | `data/input/PDF_Files` | Thư mục gốc chứa PDF files |

**💡 Auto-detect Interactive Mode:**
- Tự động kích hoạt khi: `python -m aip_builder build` (không tham số)
- Chỉ hoạt động từ terminal/console (không trong script)
- Có thể force enable/disable bằng `--interactive/--no-interactive`

### 📊 Công cụ Phân tích

```bash
# Phân tích tính đầy đủ dữ liệu CSIP 1.2
python completeness_analysis_enhanced.py data/output_20250823_064121

# Generate error reports  
python -m aip_builder generate-error-report --logs-dir logs --output error_report.json

# Test XML templates
python -m aip_builder test-xml --output test_xmls
```

## 📋 Định dạng Metadata Excel

File Excel metadata cần có cấu trúc 46 cột (A-AT) với các trường sau:

### Thông tin Hồ sơ (A-X)
- **A**: Mã cơ quan
- **B**: Tên cơ quan  
- **C**: Mã hộp số
- **D**: Tiêu đề hộp số
- **E**: Mã hồ sơ
- **F**: Tiêu đề hồ sơ
- **G**: Ngày bắt đầu
- **H**: Ngày kết thúc
- **I**: Số tờ
- **J**: Ghi chú hồ sơ
- **K**: Chế độ sử dụng
- **L**: Thời hạn bảo quản
- **M**: Ngôn ngữ
- **N**: Chữ viết
- **O**: Mật độ thông tin
- **P**: Tình trạng vật lý
- **Q**: Đặc điểm vật lý
- **R**: Từ khóa
- **S**: Người tạo
- **T**: Lịch sử xử lý
- **U**: Quy tắc
- **V**: Nguồn gốc
- **W**: Ngày số hóa
- **X**: Người số hóa

### Thông tin Tài liệu (Y-AT)
- **Y**: Mã tài liệu
- **Z**: Tiêu đề tài liệu
- **AA**: Tác giả tài liệu
- **AB**: Ngày tháng tài liệu
- **AC**: Loại tài liệu  
- **AD**: Định dạng tài liệu
- **AE**: Kích thước tài liệu
- **AF**: Số trang tài liệu
- **AG**: Ngôn ngữ tài liệu
- **AH**: Đường dẫn file
- **AI**: Tên file gốc
- **AJ**: Kích thước file (byte)
- **AK**: Loại file
- **AL**: Định dạng file
- **AM**: Phiên bản định dạng
- **AN**: Checksum
- **AO**: Thuật toán checksum
- **AP**: Ngày tạo file
- **AQ**: Ngày sửa đổi file  
- **AR**: Phần mềm tạo
- **AS**: Phiên bản phần mềm
- **AT**: Ghi chú tài liệu

## Cấu trúc Output AIP Package

```
AIP_[MaHoSo]_[Timestamp]/
├── METS.xml                    # METS manifest
├── representations/
│   └── rep1/
│       ├── data/              # PDF files
│       │   ├── 001.pdf
│       │   └── 002.pdf
│       └── metadata/
└── metadata/
    ├── descriptive/
    │   └── ead.xml           # EAD descriptive metadata
    └── preservation/
        └── premis.xml        # PREMIS preservation metadata
```

## Performance

### Benchmarks (Test data: 14 hồ sơ, 54MB)

- **Single build**: ~0.6s per package
- **Batch processing (4 workers)**: ~0.05s per package average  
- **Validation**: ~0.5s per package
- **Memory usage**: <500MB for typical workload

### Tối ưu hóa

- Sử dụng `--max-workers` để tăng tốc batch processing
- Điều chỉnh `--chunk-size` phù hợp với RAM
- Sử dụng `--no-validate` để bỏ qua validation khi test

## Troubleshooting

### Lỗi thường gặp

1. **File not found**
   - Kiểm tra đường dẫn metadata Excel
   - Kiểm tra cấu trúc thư mục PDF_Files

2. **Permission denied**
   - Chạy với quyền administrator
   - Kiểm tra quyền ghi thư mục output

3. **Memory errors** 
   - Giảm số workers (`--max-workers`)
   - Giảm chunk size (`--chunk-size`)

4. **XML validation errors**
   - Kiểm tra template XML
   - Validate dữ liệu metadata Excel

### Debug mode

```bash
export PYTHONPATH=.
python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
python -m aip_builder build
```

## API Documentation

### Core Classes

#### `HoSo` (models.py)
```python
class HoSo(BaseModel):
    """Hồ sơ model với validation"""
    ma_co_quan: str
    ten_co_quan: str
    ma_hop_so: str
    # ... 46 fields total
```

#### `PackageBuilder` (package_builder.py)
```python
class PackageBuilder:
    def build_single_package(self, hoso: HoSo, pdf_root: Path, output_dir: Path) -> BuildSummary
    def build_multiple_packages(self, hoso_list: List[HoSo], pdf_root: Path, output_dir: Path) -> BuildSummary
```

#### `CSIPValidator` (validator.py) 
```python
class CSIPValidator:
    def validate_package(self, package_dir: Path) -> ValidationResult
    def validate_directory_structure(self, package_dir: Path) -> bool
    def validate_xml_files(self, package_dir: Path) -> List[ValidationResult]
```

#### `BatchProcessor` (batch_processor.py)
```python
class BatchProcessor:
    def build_packages_parallel(self, ho_so_list: List[HoSo], output_dir: Path, pdf_root: Path) -> BatchResult
```

### Configuration

Tạo file `config.json`:

```json
{
    "organization_name": "Tổ chức ABC",
    "agent_name": "AIP Builder v2.0",
    "agent_version": "2.0.0",
    "default_meta_path": "data/Input/metadata.xlsx",
    "default_pdf_root": "data/Input/PDF_Files",
    "output_base": "data/output",
    "max_workers": 4,
    "chunk_size": 5,
    "validate_after_build": true,
    "cleanup_after_zip": false
}
```

## Testing

### Unit Tests

```bash
python -m pytest tests/ -v
```

### Integration Tests

```bash
python -m pytest tests/integration/ -v
```

### Performance Tests

```bash
python -m pytest tests/performance/ -v --benchmark-only
```

## Contributing

### Code Style
- Follow PEP 8
- Use type hints
- Document functions with docstrings
- Use Vietnamese comments for business logic

### Commit Convention
- `feat:` new features
- `fix:` bug fixes  
- `docs:` documentation
- `test:` tests
- `refactor:` code refactoring

## Changelog

### v2.0.0 (2024-01-15)
- ✨ **NEW**: OBJID-based folder naming từ `mets/@OBJID`
- ✨ **NEW**: Cleanup mode với option `--cleanup`/`--no-cleanup`  
- ✨ **NEW**: Timestamp-based output directories
- ✨ **NEW**: Enhanced ZIP file naming using OBJID
- 🔧 **IMPROVED**: Better relative path preservation
- 🔧 **IMPROVED**: More robust error handling
- 📚 **DOCS**: Complete README rewrite with examples

### v1.0.0 (2023-12-01)
- 🚀 Initial release
- ✅ Basic CSIP 1.2 compliance
- ✅ Excel metadata processing
- ✅ Batch processing with parallel execution

## License

Proprietary - All rights reserved

## Support

For technical support, contact: [Your contact info]

---

*Generated by AIP Builder v2.0.0*
