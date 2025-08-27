# Hướng dẫn sử dụng Mã phông trong AIP Builder

## Tổng quan

Mã phông là yêu cầu theo Phụ lục I Thông tư 05/2025/TT-BNV, được sử dụng trong:
1. **OBJID của METS**: Format `urn:Fondcode:uuid:{UUIDs}` 
2. **Tên thư mục gói AIP**: Lấy từ OBJID (thay `:` → `_`)

**LƯU Ý QUAN TRỌNG**: Cột B "phong" trong Excel là **tên phông**, không phải **mã phông**. Hệ thống chỉ lấy mã phông từ input người dùng.

## Các cách cung cấp mã phông

### 1. Thông qua command line parameter

```bash
python -m aip_builder build --ma-phong "G09" --meta data/input/metadata.xlsx --pdf-root data/input/PDF_Files
```

### 2. Thông qua interactive mode

Khi chạy lệnh build mà không có tham số, hệ thống sẽ vào chế độ tương tác và prompt nhập mã phông:

```bash
python -m aip_builder build
```

Hệ thống sẽ hỏi:
```
📁 Mã phông:
Mã phông (để trống nếu không có):
```

### 3. Thông qua config mặc định

Có thể set mã phông mặc định trong file config:
```python
# Trong aip_builder/config.py
default_ma_phong: str = "G09"
```

## Độ ưu tiên

1. **Command line parameter** (`--ma-phong`) - cao nhất
2. **Interactive input** - khi không có command line parameter
3. **Config default** - fallback cuối cùng

## Định dạng trong METS

### Khi có mã phông:
- **OBJID**: `urn:G09:uuid:7D0D1987-0F1C-47A7-8FD6-CC5C7DE4064F`
- **Tên thư mục**: `urn_G09_uuid_7D0D1987-0F1C-47A7-8FD6-CC5C7DE4064F`

### Khi không có mã phông:
- **OBJID**: `urn:uuid:7D0D1987-0F1C-47A7-8FD6-CC5C7DE4064F`
- **Tên thư mục**: `urn_uuid_7D0D1987-0F1C-47A7-8FD6-CC5C7DE4064F`

## Ví dụ sử dụng

### Build với mã phông cụ thể
```bash
python -m aip_builder build --ma-phong "G09" --meta data/input/metadata.xlsx --pdf-root data/input/PDF_Files --output data/output
```

### Build với interactive mode
```bash
python -m aip_builder build
# Sau đó nhập mã phông khi được hỏi (ví dụ: G09)
```

### Build với giới hạn và mã phông
```bash
python -m aip_builder build --ma-phong "PHONG_ATTP" --limit 1 --meta data/input/metadata.xlsx --pdf-root data/input/PDF_Files
```

## Lưu ý

- Mã phông nên ngắn gọn và không chứa ký tự đặc biệt (ví dụ: G09, PHONG_ATTP)
- UUIDs trong OBJID luôn được viết HOA theo đúng đặc tả
- Mã phông sẽ được áp dụng cho cả METS gốc và METS rep1
- Cột B "phong" trong Excel chỉ là tên phông để tham khảo, không được sử dụng làm mã phông
