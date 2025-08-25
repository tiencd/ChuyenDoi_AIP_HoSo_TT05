"""
Excel Reader - Module doc va phan tich file metadata.xlsx

Chuc nang chinh:
- Doc sheet "HoSo" (cot B->X) va "TaiLieu" (cot Y->AT)
- Xu ly du lieu thieu, chuan hoa dinh dang ngay thang
- Validate cau truc Excel theo dac ta
- Chuyen doi thanh cac model Pydantic
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime, date
import re

from .models import HoSo, TaiLieu
from .config import Config

logger = logging.getLogger(__name__)


class ExcelReader:
    """Class xu ly doc file metadata.xlsx"""
    
    def __init__(self, config: Config):
        self.config = config
        
        # Mapping cot Excel -> field names
        # Khoi Ho So (thuc te bat dau tu A, khong phai B)
        self.hoso_columns = {
            'A': 'stt_ho_so',          # STT
            'B': 'phong',              # Phông  
            'C': 'muc_luc',            # Mục lục
            'D': 'hop_so',             # Hộp số
            'E': 'so_ky_hieu_ho_so',   # Số và ký hiệu hồ sơ
            'F': 'title',              # Tiêu đề hồ sơ
            'G': 'thoi_han_bao_quan',  # Thời hạn bảo quản
            'H': 'che_do_su_dung',     # Chế độ sử dụng
            'I': 'ngon_ngu',           # Ngôn ngữ
            'J': 'ngay_bd',            # Ngày bắt đầu
            'K': 'thang_bd',           # Tháng bắt đầu
            'L': 'nam_bd',             # Năm bắt đầu
            'M': 'ngay_kt',            # Ngày kết thúc
            'N': 'thang_kt',           # Tháng kết thúc
            'O': 'nam_kt',             # Năm kết thúc
            'P': 'tong_so_van_ban',    # Tổng số văn bản trong hồ sơ
            'Q': 'chu_giai',           # Chú giải
            'R': 'ky_hieu_thong_tin',  # Ký hiệu thông tin
            'S': 'tu_khoa',            # Từ khóa
            'T': 'so_luong_to',        # Số lượng tờ
            'U': 'tinh_trang_vat_ly',  # Tình trạng vật lý
            'V': 'muc_do_tin_cay',     # Mức độ tin cậy
            'W': 'ma_ho_so_giay_goc',  # Mã hồ sơ giấy gốc
            'X': 'ghi_chu',            # Ghi chú
        }
        
        # Khoi Tai Lieu (Y->AT) - anh xa theo du lieu thuc te
        self.tailieu_columns = {
            'Y': 'stt',                    # Số thứ tự văn bản trong hồ sơ
            'Z': 'ten_loai_van_ban',       # Tên loại văn bản
            'AA': 'so_van_ban',            # Số của văn bản
            'AB': 'ky_hieu_van_ban',       # Ký hiệu của văn bản
            'AC': 'ngay_van_ban',          # Ngày văn bản
            'AD': 'thang_van_ban',         # Tháng văn bản
            'AE': 'nam_van_ban',           # Năm văn bản
            'AF': 'co_quan_ban_hanh',      # Tên cơ quan, tổ chức ban hành văn bản
            'AG': 'trich_yeu',             # Trích yếu nội dung
            'AH': 'ngon_ngu',              # Ngôn ngữ
            'AI': 'so_trang',              # Số lượng trang của văn bản
            'AJ': 'ghi_chu',               # Ghi chú
            'AK': 'ky_hieu_thong_tin',     # Ký hiệu thông tin
            'AL': 'tu_khoa',               # Từ khóa
            'AM': 'che_do_su_dung',        # Chế độ sử dụng
            'AN': 'muc_do_tin_cay',        # Mức độ tin cậy
            'AO': 'but_tich',              # Bút tích
            'AP': 'tinh_trang_vat_ly',     # Tình trạng vật lý
            'AQ': 'quy_trinh_xu_ly',       # Quy trình xử lý ( nếu có )
            'AR': 'to_so',                 # Tờ số
            'AS': 'loai_tai_lieu',         # Loại tài liệu
            'AT': 'duongDanFile',          # Đường dẫn file
        }
    
    def read_excel(self, excel_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Doc file Excel va tra ve 2 DataFrame: HoSo va TaiLieu
        """
        excel_path = Path(excel_path)
        
        if not excel_path.exists():
            raise FileNotFoundError(f"Khong tim thay file Excel: {excel_path}")
        
        logger.info(f"Dang doc file Excel: {excel_path}")
        
        try:
            # Doc toan bo file Excel
            excel_data = pd.read_excel(
                excel_path, 
                sheet_name=None,  # Doc tat ca sheet
                header=None,      # Khong su dung header tu dong
                engine='openpyxl'
            )
            
            # Kiem tra co sheet nao khong
            if not excel_data:
                raise ValueError("File Excel khong co sheet nao")
            
            # Lay sheet dau tien (gia su la sheet chinh)
            main_sheet_name = list(excel_data.keys())[0]
            df = excel_data[main_sheet_name]
            
            logger.info(f"Doc sheet '{main_sheet_name}' voi {len(df)} hang")
            
            # Tach du lieu HoSo va TaiLieu
            hoso_df = self._extract_hoso_data(df)
            tailieu_df = self._extract_tailieu_data(df)
            
            return hoso_df, tailieu_df
            
        except Exception as e:
            logger.error(f"Loi khi doc file Excel: {e}")
            raise
    
    def _extract_hoso_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Trich xuat du lieu Ho So tu cac cot B->X"""
        hoso_data = []
        
        # Chuyen doi index cot chu thanh so
        col_indices = self._get_column_indices(self.hoso_columns.keys())
        
        # Doc tung hang du lieu (bat dau tu hang 2, index 1)
        for idx, row in df.iterrows():
            if idx == 0:  # Bo qua header row
                continue
                
            # Kiem tra hang co du lieu khong (co it nhat ma_ho_so va title)
            if pd.isna(row.iloc[col_indices['B']]) and pd.isna(row.iloc[col_indices['C']]):
                continue
                
            row_data = {}
            for col_letter, field_name in self.hoso_columns.items():
                col_idx = col_indices[col_letter]
                if col_idx < len(row):
                    value = row.iloc[col_idx]
                    row_data[field_name] = self._clean_value(value)
            
            # Them thong tin row index de debug
            row_data['_row_index'] = idx
            hoso_data.append(row_data)
        
        logger.info(f"Tim thay {len(hoso_data)} ho so")
        return pd.DataFrame(hoso_data)
    
    def _extract_tailieu_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Trich xuat du lieu Tai Lieu tu cac cot Y->AT"""
        tailieu_data = []
        
        # Chuyen doi index cot chu thanh so
        col_indices = self._get_column_indices(self.tailieu_columns.keys())
        
        # Doc tung hang du lieu
        for idx, row in df.iterrows():
            if idx == 0:  # Bo qua header row
                continue
                
            # Kiem tra hang co du lieu khong (co it nhat STT va duong_dan_file)
            stt_col = col_indices.get('Y', -1)
            file_col = col_indices.get('AT', -1)
            
            if (stt_col >= len(row) or pd.isna(row.iloc[stt_col]) or
                file_col >= len(row) or pd.isna(row.iloc[file_col])):
                continue
                
            row_data = {}
            for col_letter, field_name in self.tailieu_columns.items():
                col_idx = col_indices.get(col_letter, -1)
                if col_idx >= 0 and col_idx < len(row):
                    value = row.iloc[col_idx]
                    row_data[field_name] = self._clean_value(value)
            
            # Them thong tin row index de debug
            row_data['_row_index'] = idx
            tailieu_data.append(row_data)
        
        logger.info(f"Tim thay {len(tailieu_data)} tai lieu")
        return pd.DataFrame(tailieu_data)
    
    def _get_column_indices(self, col_letters: List[str]) -> Dict[str, int]:
        """Chuyen doi chu cai cot (A, B, C...) thanh chi so so (0, 1, 2...)"""
        indices = {}
        for letter in col_letters:
            # Chuyen doi chu cai thanh so (A=0, B=1, ..., Z=25, AA=26, AB=27, ...)
            indices[letter] = self._letter_to_index(letter)
        return indices
    
    def _letter_to_index(self, letter: str) -> int:
        """Chuyen doi chu cai cot thanh chi so"""
        result = 0
        for char in letter:
            result = result * 26 + (ord(char.upper()) - ord('A') + 1)
        return result - 1
    
    def _clean_value(self, value: Any) -> Any:
        """Lam sach gia tri du lieu"""
        if pd.isna(value):
            return None
        
        # Neu la string, trim whitespace
        if isinstance(value, str):
            value = value.strip()
            if value == '':
                return None
        
        return value
    
    def convert_to_models(self, hoso_df: pd.DataFrame, tailieu_df: pd.DataFrame) -> List[HoSo]:
        """
        Chuyen doi DataFrame thanh cac model HoSo voi TaiLieu tuong ung
        Logic moi: Group TaiLieu theo folder path, moi folder = 1 HoSo
        """
        import os
        
        hoso_list = []
        
        # Group TaiLieu theo folder path
        if 'duongDanFile' not in tailieu_df.columns:
            logger.error("Khong tim thay cot 'duongDanFile' trong TaiLieu data")
            return []
        
        # Extract folder paths from file paths
        tailieu_with_folders = tailieu_df.copy()
        tailieu_with_folders['folder_path'] = tailieu_with_folders['duongDanFile'].apply(
            lambda x: os.path.dirname(str(x)) if pd.notna(x) else ''
        )
        
        # Group by folder path
        folder_groups = tailieu_with_folders.groupby('folder_path')
        
        logger.info(f"Tim thay {len(folder_groups)} thu muc ho so")
        
        for folder_path, tailieu_group in folder_groups:
            if not folder_path:  # Skip empty folder paths
                continue
                
            try:
                # Tao HoSo cho folder nay
                # Su dung thong tin tu tai lieu dau tien trong folder
                first_tailieu = tailieu_group.iloc[0]
                
                # Tao HoSo data tu folder path va first document
                hoso_data = self._prepare_hoso_data_from_folder(folder_path, tailieu_group, hoso_df)
                hoso = HoSo(**hoso_data)
                
                # Assign tat ca tai lieu trong folder cho ho so nay
                tailieu_models = self._convert_tailieu_models(tailieu_group)
                hoso.tai_lieu = tailieu_models
                
                # Generate identifiers for new design (UUID, file_id, etc.)
                hoso.generate_identifiers()
                
                hoso_list.append(hoso)
                
                logger.info(f"Tao ho so tu folder '{folder_path}' voi {len(tailieu_models)} tai lieu")
                
            except Exception as e:
                logger.error(f"Loi khi tao ho so tu folder '{folder_path}': {e}")
                continue
        
        logger.info(f"Chuyen doi thanh cong {len(hoso_list)} ho so tu {len(folder_groups)} thu muc")
        return hoso_list
    
    def _prepare_hoso_data(self, row: pd.Series) -> Dict[str, Any]:
        """Chuan bi du lieu cho HoSo model - IMPROVED MAPPING"""
        from datetime import datetime
        
        data = {}
        
        # Row already has renamed columns from _extract_hoso_data
        # So we map directly from renamed columns to model fields
        logger.debug(f"Row columns: {list(row.index)}")
        logger.debug(f"Row data: {dict(row)}")
        
        # Direct mapping from renamed columns (from _extract_hoso_data)
        direct_mappings = {
            'stt_ho_so': 'stt_ho_so',
            'phong': 'phong', 
            'muc_luc': 'muc_luc',
            'hop_so': 'hop_so',
            'so_ky_hieu_ho_so': 'so_ky_hieu_ho_so',
            'title': 'title',  # This is already the main title from Excel
            'thoi_han_bao_quan': 'thoi_han_bao_quan',
            'che_do_su_dung': 'che_do_su_dung',
            'ngon_ngu': 'ngon_ngu',
            'ngay_bd': 'ngay_bd',
            'thang_bd': 'thang_bd',
            'nam_bd': 'nam_bd',
            'ngay_kt': 'ngay_kt',
            'thang_kt': 'thang_kt',
            'nam_kt': 'nam_kt',
            'tong_so_van_ban': 'tong_so_van_ban',
            'chu_giai': 'chu_giai',
            'ky_hieu_thong_tin': 'ky_hieu_thong_tin',
            'tu_khoa': 'tu_khoa',
            'so_luong_to': 'so_luong_to',
            'tinh_trang_vat_ly': 'tinh_trang_vat_ly',
            'muc_do_tin_cay': 'muc_do_tin_cay',
            'ma_ho_so_giay_goc': 'ma_ho_so_giay_goc',
            'ghi_chu': 'ghi_chu'
        }
        
        # Apply direct mappings
        for col_name, model_field in direct_mappings.items():
            logger.debug(f"Direct mapping {col_name} -> {model_field}: {col_name in row} ({col_name in row and not pd.isna(row[col_name])})")
            if col_name in row and not pd.isna(row[col_name]):
                value = row[col_name]
                # Handle different data types
                if model_field in ['ngay_bd', 'thang_bd', 'nam_bd', 'ngay_kt', 'thang_kt', 'nam_kt', 'so_luong_to', 'tong_so_van_ban']:
                    try:
                        data[model_field] = int(value) if value != '' else None
                    except (ValueError, TypeError):
                        logger.warning(f"Khong the chuyen doi {model_field}={value} thanh int")
                        data[model_field] = None
                else:
                    data[model_field] = str(value).strip() if value else None
        
        # Legacy field compatibility - map to old field names used in templates
        if 'title' in data:
            # Keep both title and tieu_de_ho_so for compatibility
            data['tieu_de_ho_so'] = data['title']
        
        # NEW: Map to SimpleeDC compatible fields
        # Map legacy fields to new SimpleeDC structure
        if 'phong' in data and data['phong']:
            data['ten_co_quan'] = data['phong']  # Map phong -> ten_co_quan
        
        if 'hop_so' in data and data['hop_so']:
            data['ma_hop_so'] = data['hop_so']  # Map hop_so -> ma_hop_so
            
        if 'title' in data and data['title']:
            data['tieu_de_ho_so'] = data['title']  # Keep title as tieu_de_ho_so
        
        if 'so_ky_hieu_ho_so' in data and data['so_ky_hieu_ho_so']:
            data['ma_ho_so'] = data['so_ky_hieu_ho_so']  # Map so_ky_hieu_ho_so -> ma_ho_so
        
        # Format dates for SimpleeDC
        if data.get('nam_bd') and data.get('thang_bd') and data.get('ngay_bd'):
            data['ngay_bat_dau'] = f"{data['ngay_bd']:02d}/{data['thang_bd']:02d}/{data['nam_bd']}"
        elif data.get('nam_bd') and data.get('thang_bd'):
            data['ngay_bat_dau'] = f"{data['thang_bd']:02d}/{data['nam_bd']}"
        elif data.get('nam_bd'):
            data['ngay_bat_dau'] = str(data['nam_bd'])
            
        if data.get('nam_kt') and data.get('thang_kt') and data.get('ngay_kt'):
            data['ngay_ket_thuc'] = f"{data['ngay_kt']:02d}/{data['thang_kt']:02d}/{data['nam_kt']}"
        elif data.get('nam_kt') and data.get('thang_kt'):
            data['ngay_ket_thuc'] = f"{data['thang_kt']:02d}/{data['nam_kt']}"
        elif data.get('nam_kt'):
            data['ngay_ket_thuc'] = str(data['nam_kt'])
        
        # Map so_luong_to -> so_to for SimpleeDC
        if data.get('so_luong_to'):
            data['so_to'] = str(data['so_luong_to'])
        
        # Map ghi_chu -> ghi_chu_ho_so for SimpleeDC
        if data.get('ghi_chu'):
            data['ghi_chu_ho_so'] = data['ghi_chu']
        
        # Set default values for required SimpleeDC fields
        if 'ngon_ngu' not in data or not data['ngon_ngu']:
            data['ngon_ngu'] = 'vie'  # Default Vietnamese
        
        if 'che_do_su_dung' not in data or not data['che_do_su_dung']:
            data['che_do_su_dung'] = 'Sử dụng có điều kiện'  # Default restricted access
        
        if 'thoi_han_bao_quan' not in data or not data['thoi_han_bao_quan']:
            data['thoi_han_bao_quan'] = 'Vĩnh viễn'  # Default permanent
        
        # Sinh arc_file_code tu so_ky_hieu_ho_so hoac title
        if 'so_ky_hieu_ho_so' in data and data['so_ky_hieu_ho_so']:
            data['ma_ho_so'] = str(data['so_ky_hieu_ho_so'])  # For legacy compatibility
            data['arc_file_code'] = self._normalize_filename(str(data['so_ky_hieu_ho_so']))
        elif 'title' in data:
            # Tao arc_file_code tu title (loai bo ky tu dac biet)
            data['arc_file_code'] = self._normalize_filename(str(data['title']))
        else:
            data['arc_file_code'] = f"UNKNOWN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Dam bao co title
        if 'title' not in data or not data['title']:
            data['title'] = data.get('arc_file_code', 'Untitled')
        
        logger.debug(f"Mapped HoSo data: title='{data.get('title', 'N/A')}', phong='{data.get('phong', 'N/A')}', ngon_ngu='{data.get('ngon_ngu', 'N/A')}'")
        return data

    def _normalize_filename(self, filename: str) -> str:
        """Normalize filename by removing special characters"""
        import re
        # Remove or replace special characters 
        normalized = re.sub(r'[^\w\s-]', '_', filename)
        # Replace spaces with underscores and limit length
        normalized = re.sub(r'\s+', '_', normalized)
        return normalized[:50] if len(normalized) > 50 else normalized

    def _prepare_hoso_data_from_folder(self, folder_path: str, tailieu_group: pd.DataFrame, hoso_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Tao du lieu HoSo tu folder path va nhom tai lieu - IMPROVED LOGIC with arcFileCode from PDF filename
        """
        import os
        import re
        from datetime import datetime
        
        data = {}
        
        # Extract folder name as ho so identifier
        folder_name = os.path.basename(folder_path.rstrip('/\\'))
        
        # CRITICAL: Extract arcFileCode from PDF filename pattern (as per audit requirement)
        # Pattern: [arcFileCode].[STT].pdf
        # Get arcFileCode from first PDF file in the folder
        arc_file_code = None
        filename_pattern = re.compile(r'^(.+)\.(\d+)\.pdf$', re.IGNORECASE)
        
        if not tailieu_group.empty and 'duongDanFile' in tailieu_group.columns:
            first_file_path = str(tailieu_group.iloc[0]['duongDanFile'])
            filename = os.path.basename(first_file_path)
            
            match = filename_pattern.match(filename)
            if match:
                arc_file_code = match.group(1).strip()
                logger.info(f"Extracted arcFileCode from PDF filename: {filename} -> {arc_file_code}")
            else:
                logger.warning(f"Could not extract arcFileCode from filename: {filename}")
                arc_file_code = self._normalize_filename(folder_name)[:50]  # Fallback
        else:
            # Fallback to folder name
            arc_file_code = self._normalize_filename(folder_name)[:50]
        
        # IMPROVED: Try multiple matching strategies
        matching_hoso_row = None
        
        # Strategy 1: Match by folder pattern (hoso01, hoso02, etc.)
        for _, hoso_row in hoso_df.iterrows():
            # Check if folder name matches pattern like "hoso01" -> row index + 1
            if folder_name.startswith('hoso') and folder_name[4:].isdigit():
                folder_num = int(folder_name[4:])  # Extract number from "hoso01" -> 1
                # Match with row index (1-based)
                logger.debug(f"Checking folder {folder_name}: folder_num={folder_num}, row.name={hoso_row.name}")
                if folder_num == hoso_row.name:  # Use DataFrame index 
                    matching_hoso_row = hoso_row
                    logger.debug(f"MATCH FOUND: folder {folder_name} -> row {hoso_row.name}")
                    break
        
        # Strategy 2: If no pattern match, try by co_quan matching
        if matching_hoso_row is None:
            path_parts = folder_path.replace('\\', '/').split('/')
            if len(path_parts) >= 1:
                co_quan_from_path = path_parts[0].strip('\\')  # First part of path
                for _, hoso_row in hoso_df.iterrows():
                    phong_value = str(hoso_row.get('phong', ''))
                    # Normalize for comparison
                    if co_quan_from_path.lower() in phong_value.lower():
                        matching_hoso_row = hoso_row
                        break
        
        # Strategy 3: Use first available row if still no match and limited data
        if matching_hoso_row is None and len(hoso_df) > 0:
            # Use the first row as fallback
            matching_hoso_row = hoso_df.iloc[0]
            logger.warning(f"No exact match for folder {folder_path}, using first HoSo row as fallback")
        
        if matching_hoso_row is not None:
            # Su dung du lieu tu HoSo row da match
            data = self._prepare_hoso_data(matching_hoso_row)
            logger.info(f"Successfully matched folder '{folder_path}' with HoSo row {matching_hoso_row.name}")
            
            # IMPORTANT: Override arc_file_code with extracted value from PDF filename
            data['arc_file_code'] = arc_file_code
            data['original_folder_path'] = folder_path
            logger.info(f"Set arcFileCode from PDF pattern: {arc_file_code}")
            return data
        
        # Neu khong match duoc, tao HoSo data tu folder path
        logger.warning(f"Could not match folder '{folder_path}' with any HoSo data, creating from folder path")
        data['title'] = folder_name
        data['arc_file_code'] = arc_file_code  # Use extracted arcFileCode
        
        # Extract thong tin tu folder path neu co pattern
        path_parts = folder_path.replace('\\', '/').split('/')
        if len(path_parts) >= 2:
            data['phong'] = path_parts[-3] if len(path_parts) >= 3 else path_parts[0]  # Parent folder
            data['don_vi_hinh_thanh'] = path_parts[0] if path_parts[0] else "Unknown"
        
        # Set defaults
        data['ngon_ngu'] = 'vi'
        data['che_do_su_dung'] = 'Hạn chế'
        data['thoi_han_bao_quan'] = 'Vĩnh viễn'
        data['ghi_chu'] = f'Tự động tạo từ folder: {folder_path}'
        
        # Dat original_folder_path de duy tri duong dan tuong doi
        data['original_folder_path'] = folder_path
        
        # Extract date info from first document if available
        if not tailieu_group.empty:
            first_doc = tailieu_group.iloc[0]
            if 'nam_van_ban' in first_doc and pd.notna(first_doc['nam_van_ban']):
                data['nam_bd'] = data['nam_kt'] = int(first_doc['nam_van_ban'])
            if 'thang_van_ban' in first_doc and pd.notna(first_doc['thang_van_ban']):
                data['thang_bd'] = data['thang_kt'] = int(first_doc['thang_van_ban'])
            if 'ngay_van_ban' in first_doc and pd.notna(first_doc['ngay_van_ban']):
                data['ngay_bd'] = data['ngay_kt'] = int(first_doc['ngay_van_ban'])
        
        # Set document count
        data['tong_so_van_ban'] = len(tailieu_group)
        data['so_luong_to'] = len(tailieu_group)
        
        logger.info(f"Tao HoSo data tu folder: {folder_path} -> arcFileCode: {arc_file_code}, title: {data['title']}")
        return data
    
    def _convert_tailieu_models(self, tailieu_df: pd.DataFrame) -> List[TaiLieu]:
        """Chuyen doi DataFrame tai lieu thanh list TaiLieu models"""
        tailieu_list = []
        
        for _, row in tailieu_df.iterrows():
            try:
                tailieu_data = self._prepare_tailieu_data(row)
                tailieu = TaiLieu(**tailieu_data)
                tailieu_list.append(tailieu)
                
            except Exception as e:
                logger.error(f"Loi khi chuyen doi tai lieu o hang {row.get('_row_index', 'unknown')}: {e}")
                continue
        
        return tailieu_list
    
    def _prepare_tailieu_data(self, row: pd.Series) -> Dict[str, Any]:
        """Chuan bi du lieu cho TaiLieu model"""
        data = {}
        
        # Copy cac field string
        for field in ['ten_loai_van_ban', 'so_van_ban', 'ky_hieu_van_ban', 'trich_yeu', 
                     'co_quan_ban_hanh', 'tu_khoa', 'duongDanFile', 'ngon_ngu', 
                     'ghi_chu', 'ky_hieu_thong_tin', 'che_do_su_dung', 'muc_do_tin_cay',
                     'but_tich', 'tinh_trang_vat_ly', 'quy_trinh_xu_ly', 'to_so', 'loai_tai_lieu']:
            if field in row and not pd.isna(row[field]):
                data[field] = str(row[field])
        
        # Xu ly cac field so
        for field in ['stt', 'thang_van_ban', 'nam_van_ban', 'so_trang']:
            if field in row and not pd.isna(row[field]):
                try:
                    data[field] = int(row[field])
                except (ValueError, TypeError):
                    logger.warning(f"Khong the chuyen doi {field}={row[field]} thanh int")
        
        # Xu ly ngay van ban - chuyen date object thanh integer
        if 'ngay_van_ban' in row and not pd.isna(row['ngay_van_ban']):
            try:
                val = row['ngay_van_ban']
                if isinstance(val, (datetime, date)):
                    data['ngay_van_ban'] = val.day
                else:
                    data['ngay_van_ban'] = int(val)
            except (ValueError, TypeError):
                logger.warning(f"Khong the chuyen doi ngay_van_ban={row['ngay_van_ban']} thanh int")
        
        # Trich filename tu duongDanFile va extract arcFileCode
        if 'duongDanFile' in data:
            file_path = Path(data['duongDanFile'])
            filename = file_path.name
            data['filename'] = filename
            data['rel_href'] = f"representations/rep1/data/{filename}"
            
            # Extract arcFileCode from PDF filename pattern (same logic as HoSo)
            import re
            filename_pattern = re.compile(r'^(.+)\.(\d+)\.pdf$', re.IGNORECASE)
            match = filename_pattern.match(filename)
            if match:
                arc_file_code = match.group(1).strip()
                data['arc_file_code'] = arc_file_code
                logger.debug(f"Extracted arcFileCode from TaiLieu filename: {filename} -> {arc_file_code}")
            else:
                logger.debug(f"No arcFileCode pattern found in filename: {filename}")
        else:
            # Fallback neu khong co duong dan
            if 'trich_yeu' in data:
                safe_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', str(data['trich_yeu']))[:50]
                data['filename'] = f"{safe_name}.pdf"
                data['rel_href'] = f"representations/rep1/data/{data['filename']}"
            else:
                data['filename'] = f"document_{data.get('stt', 1):03d}.pdf"
                data['rel_href'] = f"representations/rep1/data/{data['filename']}"
        
        return data


def read_metadata_excel(excel_path: str, config: Optional[Config] = None) -> List[HoSo]:
    """
    Ham tien ich doc file metadata.xlsx va tra ve list HoSo
    
    Args:
        excel_path: Duong dan den file Excel
        config: Config (neu None thi su dung default)
        
    Returns:
        List cac HoSo model
    """
    if config is None:
        from .config import get_config
        config = get_config()
    
    reader = ExcelReader(config)
    hoso_df, tailieu_df = reader.read_excel(excel_path)
    return reader.convert_to_models(hoso_df, tailieu_df)
