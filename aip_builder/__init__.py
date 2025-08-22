"""
AIP Builder - Chương trình chuyển đổi metadata.xlsx + PDF thành gói AIP_hoso
theo Thông tư 05/2025/TT-BNV

Mô-đun này cung cấp các công cụ để:
- Đọc và phân tích file metadata.xlsx
- Quét và trích thông tin từ các file PDF
- Tạo các file XML metadata (EAD, PREMIS, METS)
- Đóng gói thành các gói AIP_hoso chuẩn OAIS/CSIP
"""

__version__ = "1.0.0"
__author__ = "AIP Builder Team"
__email__ = "contact@example.com"

from .models import HoSo, TaiLieu, PackagePlan
from .config import Config

__all__ = ["HoSo", "TaiLieu", "PackagePlan", "Config"]
