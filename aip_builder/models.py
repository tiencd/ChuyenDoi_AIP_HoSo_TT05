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
    
    # Rep METS specific UUIDs for each TaiLieu
    dmd_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    dmd_ref_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    file_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    metalink_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    
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
    
    # arcFileCode extracted from filename pattern
    arc_file_code: Optional[str] = None
    
    # System generated fields
    id: str = Field(default_factory=lambda: str(uuid4()))
    filename: Optional[str] = None
    file_path: Optional[Path] = None
    file_size: Optional[int] = None
    created_date: datetime = Field(default_factory=datetime.now)
    
    def generate_identifiers(self, stt: int):
        """Generate new design identifiers"""
        self.stt = stt
        self.file_id = str(uuid4())  # Use UUID for docId
        self.ead_doc_filename = f"EAD_doc_File{stt}.xml"  # Keep sequential filename for file system
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
    
    # SimpleeDC properties for TaiLieu
    @property
    def arc_doc_code(self) -> str:
        """Generate arcDocCode from arc_file_code and stt"""
        if self.arc_file_code and self.stt:
            return f"{self.arc_file_code}.{self.stt:07d}"
        return f"{self.arc_file_code or ''}.{self.stt:07d}" if self.stt else ""
    
    @property
    def thoi_han_bao_quan_code(self) -> str:
        """Inherit from parent HoSo - default to '01' (Vĩnh viễn)"""
        return '01'  # Will be set by parent HoSo context
    
    @property
    def loai_tai_lieu_code(self) -> str:
        """Convert loai_tai_lieu to code format"""
        if not self.loai_tai_lieu and not self.ten_loai_van_ban:
            return '32'  # Default: Khác
            
        loai = (self.loai_tai_lieu or self.ten_loai_van_ban or '').lower().strip()
        mapping = {
            'nghị quyết': '01', 'nghi quyet': '01',
            'quyết định': '02', 'quyet dinh': '02',
            'chỉ thị': '03', 'chi thi': '03',
            'quy chế': '04', 'quy che': '04',
            'quy định': '05', 'quy dinh': '05',
            'thông cáo': '06', 'thong cao': '06',
            'thông báo': '07', 'thong bao': '07',
            'hướng dẫn': '08', 'huong dan': '08',
            'chương trình': '09', 'chuong trinh': '09',
            'kế hoạch': '10', 'ke hoach': '10',
            'phương án': '11', 'phuong an': '11',
            'đề án': '12', 'de an': '12',
            'dự án': '13', 'du an': '13',
            'báo cáo': '14', 'bao cao': '14',
            'tờ trình': '15', 'to trinh': '15',
            'giấy ủy quyền': '16', 'giay uy quyen': '16',
            'phiếu gửi': '17', 'phieu gui': '17',
            'phiếu chuyển': '18', 'phieu chuyen': '18',
            'phiếu báo': '19', 'phieu bao': '19',
            'biên bản': '20', 'bien ban': '20',
            'hợp đồng': '21', 'hop dong': '21',
            'công văn': '22', 'cong van': '22',
            'công điện': '23', 'cong dien': '23',
            'bản ghi nhớ': '24', 'ban ghi nho': '24',
            'bản thỏa thuận': '25', 'ban thoa thuan': '25',
            'giấy mời': '26', 'giay moi': '26',
            'giấy giới thiệu': '27', 'giay gioi thieu': '27',
            'giấy nghỉ phép': '28', 'giay nghi phep': '28',
            'thư công': '29', 'thu cong': '29',
            'bản đồ': '30', 'ban do': '30',
            'bản vẽ kỹ thuật': '31', 'ban ve ky thuat': '31'
        }
        return mapping.get(loai, '32')  # Default: Khác
    
    @property
    def ngay_van_ban_formatted(self) -> str:
        """Format date from various sources"""
        if self.ngay_thang_tai_lieu:
            return self.ngay_thang_tai_lieu
            
        # Construct from separate fields
        if self.nam_van_ban:
            date_parts = []
            if self.ngay_van_ban:
                date_parts.append(f"{self.ngay_van_ban:02d}")
            if self.thang_van_ban:
                if not date_parts:
                    date_parts.append("01")  # Default day if only month/year
                date_parts.append(f"{self.thang_van_ban:02d}")
            date_parts.append(str(self.nam_van_ban))
            
            if len(date_parts) == 3:
                return "/".join(date_parts)  # DD/MM/YYYY
            elif len(date_parts) == 2:
                return "/".join(date_parts)  # MM/YYYY
            else:
                return str(self.nam_van_ban)  # YYYY
        return ""
    
    @property
    def ngon_ngu_code(self) -> str:
        """Convert language to code format"""
        ngon_ngu = (self.ngon_ngu_tai_lieu or self.ngon_ngu or '').lower().strip()
        mapping = {
            'việt': '01', 'viet': '01', 'vietnamese': '01', 'vie': '01', 'tiếng việt': '01', 'tieng viet': '01',
            'anh': '02', 'english': '02', 'eng': '02', 'tiếng anh': '02', 'tieng anh': '02',
            'pháp': '03', 'phap': '03', 'french': '03', 'fra': '03', 'tiếng pháp': '03', 'tieng phap': '03',
            'nga': '04', 'russian': '04', 'rus': '04', 'tiếng nga': '04', 'tieng nga': '04',
            'trung': '05', 'chinese': '05', 'chi': '05', 'tiếng trung': '05', 'tieng trung': '05',
            'việt anh': '06', 'viet anh': '06',
            'việt nga': '07', 'viet nga': '07',
            'việt pháp': '08', 'viet phap': '08',
            'hán nôm': '09', 'han nom': '09',
            'việt trung': '10', 'viet trung': '10'
        }
        return mapping.get(ngon_ngu, '01')  # Default: Tiếng Việt
    
    @property
    def che_do_su_dung_code(self) -> str:
        """Convert access mode to code format"""
        if not self.che_do_su_dung:
            return '02'  # Default: Sử dụng có điều kiện
            
        che_do = self.che_do_su_dung.lower().strip()
        mapping = {
            'công khai': '01', 'cong khai': '01',
            'sử dụng có điều kiện': '02', 'su dung co dieu kien': '02',
            'hạn chế': '02', 'han che': '02',
            'mật': '03', 'mat': '03'
        }
        return mapping.get(che_do, '02')
    
    @property
    def muc_do_tin_cay_code(self) -> str:
        """Convert confidence level to code format"""
        if not self.muc_do_tin_cay:
            return '02'  # Default: Số hóa
            
        tin_cay = self.muc_do_tin_cay.lower().strip()
        mapping = {
            'gốc điện tử': '01', 'goc dien tu': '01',
            'số hóa': '02', 'so hoa': '02',
            'hỗn hợp': '03', 'hon hop': '03'
        }
        return mapping.get(tin_cay, '02')
    
    @property
    def tinh_trang_vat_ly_code(self) -> str:
        """Convert physical condition to code format"""
        if not self.tinh_trang_vat_ly:
            return '02'  # Default: Bình thường
            
        tinh_trang = self.tinh_trang_vat_ly.lower().strip()
        mapping = {
            'tốt': '01', 'tot': '01',
            'bình thường': '02', 'binh thuong': '02',
            'hỏng': '03', 'hong': '03'
        }
        return mapping.get(tinh_trang, '02')
    
    @property
    def quy_trinh_xu_ly_code(self) -> str:
        """Convert process flag to code format"""
        if not self.quy_trinh_xu_ly:
            return '0'  # Default: Không có quy trình xử lý
        
        # If it's a boolean-like field
        if str(self.quy_trinh_xu_ly).lower() in ['true', '1', 'có', 'co', 'yes']:
            return '1'
        return '0'
    
    @property
    def che_do_du_phong(self) -> str:
        """Risk recovery mode - default to '0' (Không)"""
        return '0'
    
    @property 
    def tinh_trang_du_phong(self) -> str:
        """Risk recovery status - only set if che_do_du_phong is '1'"""
        if self.che_do_du_phong == '1':
            return '02'  # Default: Chưa dự phòng
        return ''


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
    ma_phong: Optional[str] = None  # Mã phông - dùng cho metsHdr/agent/note với csip:NOTETYPE="IDENTIFICATIONCODE"
    
    # Additional fields for METS generation
    metadata_id: str = Field(default_factory=lambda: f"metadata-{uuid4()}")
    schemas_id: str = Field(default_factory=lambda: f"schemas-{uuid4()}")
    representations_id: str = Field(default_factory=lambda: f"representations-{uuid4()}")
    
    # Rep METS specific UUIDs
    rep_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    dmd_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    dmd_ref_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    amd_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    digiprov_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    premis_ref_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    filesec_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    filegroup_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    structmap_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    main_div_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    metadata_div_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    data_div_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    metalink_div_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    
    # Main METS specific UUIDs  
    main_dmd_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    main_dmd_ref_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    main_amd_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    main_digiprov_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    main_premis_ref_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    main_filesec_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    main_repr_group_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    main_repr_file_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    main_schemas_group_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    main_mets_xsd_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    main_ead_xsd_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    main_premis_xsd_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    main_structmap_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    main_div_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    main_metadata_div_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    main_schemas_div_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())
    main_repr_div_uuid: str = Field(default_factory=lambda: str(uuid4()).upper())

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
    nam_kt: Optional[int] = None
    
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
    
    def generate_objid_with_ma_phong(self) -> str:
        """Generate OBJID with format: urn:Fondcode:uuid:{UUIDs}"""
        uuid_part = str(uuid4()).upper()
        if self.ma_phong:
            return f"urn:{self.ma_phong}:uuid:{uuid_part}"
        else:
            return f"urn:uuid:{uuid_part}"
    
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
        
        # Generate OBJID with ma_phong if available
        if self.ma_phong:
            self.objid = self.generate_objid_with_ma_phong()
        
        # Generate identifiers for tai_lieu
        for i, tai_lieu in enumerate(self.tai_lieu, 1):
            tai_lieu.generate_identifiers(i)
        
        # Initialize metadata, schemas, and representations IDs based on file_id
        if not self.file_id:
            self.file_id = self.id  # Default to system-generated ID if not provided
        if not self.metadata_id:
            self.metadata_id = f"metadata-{self.file_id}"
        if not self.schemas_id:
            self.schemas_id = f"schemas-{self.file_id}"
        if not self.representations_id:
            self.representations_id = f"representations-{self.file_id}"
    
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
    
    # SimpleeDC data conversion methods
    @property
    def thoi_han_bao_quan_code(self) -> str:
        """Convert thoi_han_bao_quan to code format for SimpleeDC"""
        if not self.thoi_han_bao_quan:
            return '01'  # Default: Vĩnh viễn
        
        thoi_han = self.thoi_han_bao_quan.lower().strip()
        mapping = {
            'vĩnh viễn': '01',
            'vinh vien': '01', 
            '70 năm': '02',
            '70 nam': '02',
            '50 năm': '03', 
            '50 nam': '03',
            '30 năm': '04',
            '30 nam': '04',
            '20 năm': '05',
            '20 nam': '05', 
            '10 năm': '06',
            '10 nam': '06'
        }
        return mapping.get(thoi_han, '07')  # Default: Khác
    
    @property
    def che_do_su_dung_code(self) -> str:
        """Convert che_do_su_dung to code format for SimpleeDC"""
        if not self.che_do_su_dung:
            return '02'  # Default: Sử dụng có điều kiện
            
        che_do = self.che_do_su_dung.lower().strip()
        mapping = {
            'công khai': '01',
            'cong khai': '01',
            'sử dụng có điều kiện': '02',
            'su dung co dieu kien': '02',
            'hạn chế': '02',
            'han che': '02',
            'mật': '03',
            'mat': '03'
        }
        return mapping.get(che_do, '02')
    
    @property
    def ngon_ngu_code(self) -> str:
        """Convert ngon_ngu to code format for SimpleeDC"""
        if not self.ngon_ngu:
            return '01'  # Default: Tiếng Việt
            
        ngon_ngu = self.ngon_ngu.lower().strip()
        mapping = {
            'tiếng việt': '01',
            'tieng viet': '01',
            'việt': '01',
            'viet': '01',
            'vi': '01',
            'vie': '01',
            'vietnamese': '01',
            'tiếng anh': '02',
            'tieng anh': '02',
            'anh': '02',
            'english': '02',
            'en': '02',
            'tiếng pháp': '03',
            'tieng phap': '03',
            'pháp': '03',
            'phap': '03',
            'french': '03',
            'fr': '03',
            'tiếng nga': '04',
            'tieng nga': '04',
            'nga': '04',
            'russian': '04',
            'ru': '04',
            'tiếng trung': '05',
            'tieng trung': '05',
            'trung': '05',
            'chinese': '05',
            'zh': '05',
            'việt anh': '06',
            'viet anh': '06',
            'việt nga': '07',
            'viet nga': '07',
            'việt pháp': '08',
            'viet phap': '08',
            'hán nôm': '09',
            'han nom': '09',
            'việt trung': '10',
            'viet trung': '10'
        }
        return mapping.get(ngon_ngu, '11')  # Default: Khác
    
    @property
    def tinh_trang_vat_ly_code(self) -> str:
        """Convert tinh_trang_vat_ly to code format for SimpleeDC"""
        if not self.tinh_trang_vat_ly:
            return '02'  # Default: Bình thường
            
        tinh_trang = self.tinh_trang_vat_ly.lower().strip()
        mapping = {
            'tốt': '01',
            'tot': '01',
            'good': '01',
            'bình thường': '02',
            'binh thuong': '02',
            'normal': '02',
            'hỏng': '03',
            'hong': '03',
            'damaged': '03',
            'bad': '03'
        }
        return mapping.get(tinh_trang, '02')
    
    @property
    def muc_do_tin_cay_code(self) -> str:
        """Convert muc_do_tin_cay to code format for SimpleeDC"""
        if not self.muc_do_tin_cay:
            return '02'  # Default: Số hóa
            
        tin_cay = self.muc_do_tin_cay.lower().strip()
        mapping = {
            'gốc điện tử': '01',
            'goc dien tu': '01',
            'digital original': '01',
            'số hóa': '02',
            'so hoa': '02',
            'digitized': '02',
            'hỗn hợp': '03',
            'hon hop': '03',
            'mixed': '03'
        }
        return mapping.get(tin_cay, '02')
    
    @property
    def start_date_formatted(self) -> str:
        """Get start date in proper format for SimpleeDC"""
        # Try new design fields first
        if self.ngay_bat_dau:
            return self.ngay_bat_dau
            
        # Fallback to legacy fields
        if self.nam_bd:
            date_str = str(self.nam_bd)
            if self.thang_bd:
                date_str += f"/{self.thang_bd:02d}"
                if self.ngay_bd:
                    date_str += f"/{self.ngay_bd:02d}"
            return date_str
        return ""
    
    @property
    def end_date_formatted(self) -> str:
        """Get end date in proper format for SimpleeDC"""
        # Try new design fields first
        if self.ngay_ket_thuc:
            return self.ngay_ket_thuc
            
        # Fallback to legacy fields
        if self.nam_kt:
            date_str = str(self.nam_kt)
            if self.thang_kt:
                date_str += f"/{self.thang_kt:02d}"
                if self.ngay_kt:
                    date_str += f"/{self.ngay_kt:02d}"
            return date_str
        return ""
    
    @property
    def total_pages(self) -> int:
        """Calculate total pages from all tai_lieu"""
        total = 0
        for tai_lieu in self.tai_lieu:
            if tai_lieu.so_trang:
                total += tai_lieu.so_trang
            elif tai_lieu.so_trang_tai_lieu:
                total += tai_lieu.so_trang_tai_lieu
        return total
    
    @property
    def effective_total_pages(self) -> int:
        """Get effective total pages - prefer from metadata, fallback to calculated"""
        # In the future, if metadata.xlsx has a field for total pages of hoso,
        # add it to HoSo model (e.g., so_luong_trang_ho_so) and check it here first
        # For now, always calculate from tai_lieu
        return self.total_pages
    
    @property
    def effective_paper_file_code(self) -> str:
        """Get effective paper file code - use arc_file_code as default"""
        # Use ma_ho_so_giay_goc if available, otherwise use arc_file_code
        if self.ma_ho_so_giay_goc:
            return self.ma_ho_so_giay_goc
        return self.arc_file_code or ""
    
    @property
    def che_do_du_phong(self) -> str:
        """Risk recovery mode - default to '0' (Không)"""
        return '0'  # Default: Không có chế độ dự phòng
    
    @property 
    def tinh_trang_du_phong(self) -> str:
        """Risk recovery status - only set if che_do_du_phong is '1'"""
        if self.che_do_du_phong == '1':
            return '02'  # Default: Chưa dự phòng
        return ''


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
