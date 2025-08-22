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
        """Chuan bi du lieu cho HoSo model"""
        data = {}
        
        # Copy cac field co san
        for field in ['ma_ho_so', 'title', 'phong', 'don_vi_hinh_thanh', 
                     'ngon_ngu', 'tu_khoa', 'che_do_su_dung', 
                     'thoi_han_bao_quan', 'ghi_chu']:
            if field in row and not pd.isna(row[field]):
                data[field] = row[field]
        
        # Xu ly cac field so
        for field in ['ngay_bd', 'thang_bd', 'nam_bd', 
                     'ngay_kt', 'thang_kt', 'nam_kt', 'so_luong_to']:
            if field in row and not pd.isna(row[field]):
                try:
                    data[field] = int(row[field])
                except (ValueError, TypeError):
                    logger.warning(f"Khong the chuyen doi {field}={row[field]} thanh int")
        
        # Sinh arc_file_code tu ma_ho_so hoac title
        if 'ma_ho_so' in data and data['ma_ho_so']:
            data['arc_file_code'] = str(data['ma_ho_so'])
        elif 'title' in data:
            # Tao arc_file_code tu title (loai bo ky tu dac biet)
            data['arc_file_code'] = re.sub(r'[^a-zA-Z0-9_.-]', '_', str(data['title']))[:50]
        else:
            data['arc_file_code'] = f"UNKNOWN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Dam bao co title
        if 'title' not in data or not data['title']:
            data['title'] = data['arc_file_code']
        
        return data

    def _prepare_hoso_data_from_folder(self, folder_path: str, tailieu_group: pd.DataFrame, hoso_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Tao du lieu HoSo tu folder path va nhom tai lieu
        """
        import os
        from datetime import datetime
        
        data = {}
        
        # Extract folder name as ho so identifier
        folder_name = os.path.basename(folder_path.rstrip('/\\'))
        
        # Try to match with existing HoSo data if possible
        # Tim HoSo row tuong ung (neu co) dua tren folder pattern
        matching_hoso_row = None
        for _, hoso_row in hoso_df.iterrows():
            # Simple matching logic - co the can tinh chinh
            if folder_name in str(hoso_row.get('title', '')) or folder_name in str(hoso_row.get('ma_ho_so', '')):
                matching_hoso_row = hoso_row
                break
        
        if matching_hoso_row is not None:
            # Su dung du lieu tu HoSo row da match
            return self._prepare_hoso_data(matching_hoso_row)
        
        # Neu khong match duoc, tao HoSo data tu folder path
        data['title'] = folder_name
        data['arc_file_code'] = re.sub(r'[^a-zA-Z0-9_.-]', '_', folder_name)[:50]
        
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
        
        logger.info(f"Tao HoSo data tu folder: {folder_path} -> {data['title']}")
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
        
        # Trich filename tu duongDanFile
        if 'duongDanFile' in data:
            file_path = Path(data['duongDanFile'])
            data['filename'] = file_path.name
            data['rel_href'] = f"representations/rep1/data/{file_path.name}"
        else:
            # Fallback neu khong co duong dan
            if 'trich_yeu' in data:
                safe_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', str(data['trich_yeu']))[:50]
                data['filename'] = f"{safe_name}.pdf"
                data['rel_href'] = f"representations/rep1/data/{data['filename']}"
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
