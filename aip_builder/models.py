"""
Pydantic models for AIP Builder - Updated Design
Dinh nghia cac data models cho he thong AIP voi thiet ke moi
"""
import re
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional, Any, Dict
from uuid import uuid4, UUID

from pydantic import BaseModel, Field, field_validator
from pydantic import ConfigDict


class TaiLieu(BaseModel):
    """
    Model cho tai lieu (document) trong ho so - Updated Design
    Tuong ung voi cac cot Y->AT trong Excel
    Moi tai lieu se co file EAD_doc rieng
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # Thong tin co ban tu Excel Y-AT
    stt: Optional[int] = None  # Số thứ tự văn bản trong hồ sơ  
    ma_tai_lieu: Optional[str] = None  # Y - Mã tài liệu
    tieu_de_tai_lieu: Optional[str] = None  # Z - Tiêu đề tài liệu
    tac_gia_tai_lieu: Optional[str] = None  # AA - Tác giả tài liệu
    ngay_thang_tai_lieu: Optional[str] = None  # AB - Ngày tháng tài liệu
    loai_tai_lieu: Optional[str] = None  # AC - Loại tài liệu
    dinh_dang_tai_lieu: Optional[str] = None  # AD - Định dạng tài liệu
    kich_thuoc_tai_lieu: Optional[str] = None  # AE - Kích thước tài liệu
    so_trang_tai_lieu: Optional[int] = None  # AF - Số trang tài liệu
    ngon_ngu_tai_lieu: Optional[str] = "vie"  # AG - Ngôn ngữ tài liệu
    duong_dan_file: Optional[str] = None  # AH - Đường dẫn file
    ten_file_goc: Optional[str] = None  # AI - Tên file gốc
    kich_thuoc_file: Optional[int] = None  # AJ - Kích thước file (byte)
    loai_file: Optional[str] = "application/pdf"  # AK - Loại file
    dinh_dang_file: Optional[str] = "PDF"  # AL - Định dạng file
    phien_ban_dinh_dang: Optional[str] = "1.7"  # AM - Phiên bản định dạng
    checksum: Optional[str] = None  # AN - Checksum
    thuat_toan_checksum: Optional[str] = "SHA-256"  # AO - Thuật toán checksum
    ngay_tao_file: Optional[str] = None  # AP - Ngày tạo file
    ngay_sua_doi_file: Optional[str] = None  # AQ - Ngày sửa đổi file
    phan_mem_tao: Optional[str] = None  # AR - Phần mềm tạo
    phien_ban_phan_mem: Optional[str] = None  # AS - Phiên bản phần mềm
    ghi_chu_tai_lieu: Optional[str] = None  # AT - Ghi chú tài liệu
    
    # New design identifiers
    file_id: Optional[str] = None  # "file-<stt>" format
    ead_doc_filename: Optional[str] = None  # "EAD_doc_File<stt>.xml"
    dmd_id: Optional[str] = None  # "dmd-doc-<stt>"
    
    # Legacy fields for backward compatibility
    ten_loai_van_ban: Optional[str] = None
    so_van_ban: Optional[str] = None  
    ky_hieu_van_ban: Optional[str] = None
    ngay_van_ban: Optional[int] = None
    thang_van_ban: Optional[int] = None
    nam_van_ban: Optional[int] = None
    trich_yeu: Optional[str] = None
    ngon_ngu: Optional[str] = None
    so_trang: Optional[int] = None
    co_quan_ban_hanh: Optional[str] = None
    tu_khoa: Optional[str] = None
    ghi_chu: Optional[str] = None
    ky_hieu_thong_tin: Optional[str] = None
    che_do_su_dung: Optional[str] = None
    muc_do_tin_cay: Optional[str] = None
    but_tich: Optional[str] = None
    tinh_trang_vat_ly: Optional[str] = None
    quy_trinh_xu_ly: Optional[str] = None
    to_so: Optional[str] = None
    duongDanFile: Optional[str] = None  # Legacy field
    
    # System generated fields
    id: str = Field(default_factory=lambda: str(uuid4()))
    filename: Optional[str] = None
    file_path: Optional[Path] = None
    file_size: Optional[int] = None
    created_date: datetime = Field(default_factory=datetime.now)
    
    def generate_identifiers(self, stt: int):
        """Generate new design identifiers"""
        self.stt = stt
        self.file_id = f"file-{stt}"
        self.ead_doc_filename = f"EAD_doc_File{stt}.xml"  
        self.dmd_id = f"dmd-doc-{stt}"
    
    @property
    def ead_doc_path(self) -> str:
        """Path to EAD_doc file within package"""
        return f"metadata/descriptive/{self.ead_doc_filename}"
    
    @property
    def effective_title(self) -> str:
        """Get effective title from various sources"""
        if self.tieu_de_tai_lieu:
            return self.tieu_de_tai_lieu
        elif self.trich_yeu:
            return self.trich_yeu
        elif self.ten_loai_van_ban:
            return self.ten_loai_van_ban
        else:
            return f"Tài liệu {self.stt}" if self.stt else "Tài liệu"
    
    @property 
    def effective_date(self) -> str:
        """Get effective date in ISO format"""
        if self.ngay_thang_tai_lieu:
            return self.ngay_thang_tai_lieu
        elif self.nam_van_ban:
            date_str = f"{self.nam_van_ban}"
            if self.thang_van_ban:
                date_str += f"-{self.thang_van_ban:02d}"
                if self.ngay_van_ban:
                    date_str += f"-{self.ngay_van_ban:02d}"
            return date_str
        return ""


class HoSo(BaseModel):
    """
    Model cho ho so (record) - Updated Design
    Tuong ung voi cot A->X trong Excel
    Co UUID cho OBJID va paperFileCode = arcFileCode
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # New design fields
    objid: str = Field(default_factory=lambda: f"urn:uuid:{uuid4()}")  # UUID cho package
    paper_file_code: Optional[str] = None  # = arc_file_code theo thiet ke moi
    
    # Thong tin dinh danh tu Excel A-X
    ma_co_quan: Optional[str] = None  # A - Mã cơ quan  
    ten_co_quan: Optional[str] = None  # B - Tên cơ quan
    ma_hop_so: Optional[str] = None  # C - Mã hộp số
    tieu_de_hop_so: Optional[str] = None  # D - Tiêu đề hộp số
    ma_ho_so: Optional[str] = None  # E - Mã hồ sơ
    tieu_de_ho_so: Optional[str] = None  # F - Tiêu đề hồ sơ
    ngay_bat_dau: Optional[str] = None  # G - Ngày bắt đầu
    ngay_ket_thuc: Optional[str] = None  # H - Ngày kết thúc
    so_to: Optional[str] = None  # I - Số tờ
    ghi_chu_ho_so: Optional[str] = None  # J - Ghi chú hồ sơ
    che_do_su_dung: Optional[str] = None  # K - Chế độ sử dụng
    thoi_han_bao_quan: Optional[str] = None  # L - Thời hạn bảo quản
    ngon_ngu: Optional[str] = "vie"  # M - Ngôn ngữ
    chu_viet: Optional[str] = None  # N - Chữ viết
    mat_do_thong_tin: Optional[str] = None  # O - Mật độ thông tin
    tinh_trang_vat_ly: Optional[str] = None  # P - Tình trạng vật lý
    dac_diem_vat_ly: Optional[str] = None  # Q - Đặc điểm vật lý
    tu_khoa: Optional[str] = None  # R - Từ khóa
    nguoi_tao: Optional[str] = None  # S - Người tạo
    lich_su_xu_ly: Optional[str] = None  # T - Lịch sử xử lý
    quy_tac: Optional[str] = None  # U - Quy tắc
    nguon_goc: Optional[str] = None  # V - Nguồn gốc  
    ngay_so_hoa: Optional[str] = None  # W - Ngày số hóa
    nguoi_so_hoa: Optional[str] = None  # X - Người số hóa
    
    # Legacy fields for backward compatibility
    arc_file_code: Optional[str] = None  # Will be derived from ten_co_quan
    title: Optional[str] = None  # Will use tieu_de_ho_so
    phong: Optional[str] = None
    muc_luc: Optional[str] = None
    hop_so: Optional[str] = None
    so_ky_hieu_ho_so: Optional[str] = None
    ngay_bd: Optional[int] = None
    thang_bd: Optional[int] = None
    nam_bd: Optional[int] = None
    ngay_kt: Optional[int] = None
    thang_kt: Optional[int] = None
    
    # Thong tin bo sung (legacy)
    tong_so_van_ban: Optional[int] = None
    chu_giai: Optional[str] = None
    ky_hieu_thong_tin: Optional[str] = None
    so_luong_to: Optional[int] = None
    muc_do_tin_cay: Optional[str] = None
    ma_ho_so_giay_goc: Optional[str] = None
    ghi_chu: Optional[str] = None
    
    # System generated fields
    id: str = Field(default_factory=lambda: str(uuid4()))
    objid: str = Field(default_factory=lambda: f"urn:uuid:{uuid4()}")  # New design UUID
    file_id: Optional[str] = None  # New design identifier
    created_date: datetime = Field(default_factory=datetime.now)
    tai_lieu: List[TaiLieu] = Field(default_factory=list)
    
    # Path information - duong dan tuong doi tu thu muc goc
    original_folder_path: Optional[Path] = None  # Duong dan tuong doi tu PDF_Files, vi du: "Chi cuc an toan ve sinh thuc pham/hopso01/hoso01"
    
    def __post_init__(self):
        """Post initialization to set derived fields"""
        # Set paper_file_code = arc_file_code theo thiet ke moi
        if self.arc_file_code and not self.paper_file_code:
            self.paper_file_code = self.arc_file_code
        
        # Derive arc_file_code from ten_co_quan if not set
        if not self.arc_file_code and self.ten_co_quan:
            self.arc_file_code = self._normalize_filename(self.ten_co_quan)
            self.paper_file_code = self.arc_file_code
            
        # Set title from tieu_de_ho_so if not set
        if not self.title and self.tieu_de_ho_so:
            self.title = self.tieu_de_ho_so
        
        # Generate identifiers for tai_lieu
        for i, tai_lieu in enumerate(self.tai_lieu, 1):
            tai_lieu.generate_identifiers(i)
    
    @property
    def effective_title(self) -> str:
        """Get effective title"""
        return self.tieu_de_ho_so or self.title or f"Hồ sơ {self.ma_ho_so or self.arc_file_code}"
    
    @property
    def effective_language(self) -> str:
        """Get effective language (default to 'vie')"""
        return self.ngon_ngu or "vie"
    
    @property
    def confidence_level(self) -> str:
        """Get confidence level (fixed as 'Số hóa')"""
        return "Số hóa"
    
    @property
    def date_range(self) -> str:
        """Get date range in ISO format"""
        start_date = self.ngay_bat_dau or ""
        end_date = self.ngay_ket_thuc or ""
        
        if start_date and end_date:
            return f"{start_date}/{end_date}"
        elif start_date:
            return start_date
        elif end_date:
            return end_date
        else:
            # Fallback to legacy fields
            if self.nam_bd:
                start = f"{self.nam_bd}"
                if self.thang_bd:
                    start += f"-{self.thang_bd:02d}"
                    if self.ngay_bd:
                        start += f"-{self.ngay_bd:02d}"
                
                if self.nam_kt:
                    end = f"{self.nam_kt}"
                    if self.thang_kt:
                        end += f"-{self.thang_kt:02d}"
                        if self.ngay_kt:
                            end += f"-{self.ngay_kt:02d}"
                    return f"{start}/{end}"
                return start
            return ""
    
    def _normalize_filename(self, name: str) -> str:
        """Chuyen doi ten thanh filename hop le"""
        if not name:
            return ""
        
        # Replace special characters
        normalized = name
        replacements = {
            'ă': 'a', 'â': 'a', 'á': 'a', 'à': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
            'Ă': 'A', 'Â': 'A', 'Á': 'A', 'À': 'A', 'Ả': 'A', 'Ã': 'A', 'Ạ': 'A',
            'đ': 'd', 'Đ': 'D',
            'ê': 'e', 'é': 'e', 'è': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
            'Ê': 'E', 'É': 'E', 'È': 'E', 'Ẻ': 'E', 'Ẽ': 'E', 'Ẹ': 'E',
            'ô': 'o', 'ơ': 'o', 'ó': 'o', 'ò': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
            'ớ': 'o', 'ờ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
            'Ô': 'O', 'Ơ': 'O', 'Ó': 'O', 'Ò': 'O', 'Ỏ': 'O', 'Õ': 'O', 'Ọ': 'O',
            'Ớ': 'O', 'Ờ': 'O', 'Ở': 'O', 'Ỡ': 'O', 'Ợ': 'O',
            'ư': 'u', 'ú': 'u', 'ù': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
            'ứ': 'u', 'ừ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
            'Ư': 'U', 'Ú': 'U', 'Ù': 'U', 'Ủ': 'U', 'Ũ': 'U', 'Ụ': 'U',
            'Ứ': 'U', 'Ừ': 'U', 'Ử': 'U', 'Ữ': 'U', 'Ự': 'U',
            'ý': 'y', 'ỳ': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
            'Ý': 'Y', 'Ỳ': 'Y', 'Ỷ': 'Y', 'Ỹ': 'Y', 'Ỵ': 'Y',
            'í': 'i', 'ì': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
            'Í': 'I', 'Ì': 'I', 'Ỉ': 'I', 'Ĩ': 'I', 'Ị': 'I',
        }
        
        for vn_char, en_char in replacements.items():
            normalized = normalized.replace(vn_char, en_char)
        
        # Remove or replace special characters
        normalized = re.sub(r'[^\w\s-]', '_', normalized)
        # Replace spaces with underscores  
        normalized = re.sub(r'\s+', '_', normalized)
        # Remove multiple underscores
        normalized = re.sub(r'_+', '_', normalized)
        # Remove leading/trailing underscores
        normalized = normalized.strip('_')
        
        return normalized[:100]  # Limit length

    def generate_identifiers(self):
        """Generate new design identifiers for HoSo and its TaiLieu"""
        # Generate HoSo identifiers if not already set
        if not hasattr(self, 'file_id') or not self.file_id:
            self.file_id = f"hoso-{self.arc_file_code}"
        
        # Generate identifiers for tai_lieu
        for i, tai_lieu in enumerate(self.tai_lieu, 1):
            tai_lieu.generate_identifiers(i)


class PackagePlan(BaseModel):
    """Ke hoach xay dung package AIP"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    package_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    hoso_list: List[HoSo] = Field(default_factory=list)
    output_dir: Path
    created_date: datetime = Field(default_factory=datetime.now)
    status: str = "PLANNING"  # PLANNING, BUILDING, COMPLETED, ERROR


class BuildSummary(BaseModel):
    """Tom tat ket qua xay dung"""
    total_hoso: int = 0
    successful_builds: int = 0
    failed_builds: int = 0
    total_files: int = 0
    total_size_mb: float = 0.0
    errors: List[str] = Field(default_factory=list)
    build_time_seconds: float = 0.0
