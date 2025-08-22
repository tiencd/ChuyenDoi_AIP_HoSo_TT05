"""
Grouping - Module nhom ho so va tai lieu theo thu muc

Chuc nang chinh:
- Nhom ho so theo thu muc con (moi thu muc = 1 ho so)
- Doi chieu arcFileCode trich tu ten file
- Validate STT va arcFileCode trong cung thu muc
- Ket hop du lieu Excel voi cau truc file PDF
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict, Counter
import logging

from .models import HoSo, TaiLieu
from .pdf_probe import PDFInfo

logger = logging.getLogger(__name__)


class GroupingError(Exception):
    """Loi trong qua trinh nhom du lieu"""
    pass


class FileGrouper:
    """Class xu ly nhom file va ho so"""
    
    def __init__(self):
        # Pattern de trich arcFileCode va STT tu ten file
        # Format: [arcFileCode].[STT].pdf
        self.filename_pattern = re.compile(r'^(.+)\.(\d+)\.pdf$', re.IGNORECASE)
    
    def group_by_directory(self, pdf_root: str | Path, hoso_list: List[HoSo]) -> Dict[str, 'FolderGroup']:
        """
        Nhom ho so theo thu muc con
        
        Args:
            pdf_root: Thu muc goc chua PDF
            hoso_list: Danh sach ho so tu Excel
            
        Returns:
            Dict[folder_name, FolderGroup] 
        """
        pdf_root = Path(pdf_root)
        
        if not pdf_root.exists():
            raise FileNotFoundError(f"Thu muc PDF khong ton tai: {pdf_root}")
        
        # Tim tat ca thu muc con chua PDF
        folder_groups = {}
        
        # Duyet tat ca thu muc con
        for subfolder in pdf_root.iterdir():
            if not subfolder.is_dir():
                continue
                
            # Tim tat ca PDF trong thu muc
            pdf_files = list(subfolder.rglob("*.pdf"))
            if not pdf_files:
                logger.info(f"Thu muc {subfolder.name} khong co file PDF")
                continue
            
            # Tinh duong dan tuong doi tu pdf_root
            relative_folder_path = subfolder.relative_to(pdf_root)
            
            # Tao folder group
            folder_group = FolderGroup(
                folder_name=subfolder.name,
                folder_path=relative_folder_path,  # Luu duong dan tuong doi
                pdf_files=pdf_files
            )
            
            # Phan tich file names
            folder_group.analyze_files()
            
            folder_groups[subfolder.name] = folder_group
        
        logger.info(f"Tim thay {len(folder_groups)} thu muc chua PDF")
        
        # Gan ho so Excel vao cac thu muc
        self._assign_hoso_to_folders(folder_groups, hoso_list)
        
        return folder_groups
    
    def _assign_hoso_to_folders(self, folder_groups: Dict[str, 'FolderGroup'], hoso_list: List[HoSo]) -> None:
        """Gan ho so Excel vao cac thu muc tuong ung"""
        
        # Thu gan theo arc_file_code
        for hoso in hoso_list:
            assigned = False
            
            for folder_name, folder_group in folder_groups.items():
                # Kiem tra xem ho so co khop voi thu muc khong
                if self._is_hoso_match_folder(hoso, folder_group):
                    folder_group.hoso = hoso
                    assigned = True
                    logger.info(f"Gan ho so '{hoso.arc_file_code}' vao thu muc '{folder_name}'")
                    break
            
            if not assigned:
                logger.warning(f"Khong tim thay thu muc cho ho so '{hoso.arc_file_code}'")
    
    def _is_hoso_match_folder(self, hoso: HoSo, folder_group: 'FolderGroup') -> bool:
        """Kiem tra ho so co khop voi thu muc khong"""
        
        # Kiem tra arc_file_code co trong danh sach arc_codes cua folder
        if hoso.arc_file_code in folder_group.arc_codes:
            return True
        
        # Kiem tra theo folder name (neu khong co arc_code tu filename)
        if (not folder_group.arc_codes and 
            hoso.arc_file_code.lower() == folder_group.folder_name.lower()):
            return True
        
        # Kiem tra theo ma_ho_so
        if (hoso.ma_ho_so and 
            hoso.ma_ho_so in folder_group.arc_codes):
            return True
        
        return False
    
    def extract_arc_and_stt(self, filename: str) -> Tuple[Optional[str], Optional[int]]:
        """
        Trich arcFileCode va STT tu ten file
        
        Args:
            filename: Ten file (khong co duong dan)
            
        Returns:
            Tuple[arcFileCode, STT] hoac (None, None) neu khong match
        """
        match = self.filename_pattern.match(filename)
        if match:
            arc_code = match.group(1).strip()
            try:
                stt = int(match.group(2))
                return arc_code, stt
            except ValueError:
                return arc_code, None
        
        return None, None
    
    def validate_folder_consistency(self, folder_groups: Dict[str, 'FolderGroup']) -> List[str]:
        """
        Validate tinh nhat quan cua cac thu muc
        
        Returns:
            List cac thong bao loi/canh bao
        """
        warnings = []
        
        for folder_name, folder_group in folder_groups.items():
            warnings.extend(folder_group.validate())
        
        return warnings


class FolderGroup:
    """Dai dien cho mot thu muc chua PDF va ho so tuong ung"""
    
    def __init__(self, folder_name: str, folder_path: Path, pdf_files: List[Path]):
        self.folder_name = folder_name
        self.folder_path = folder_path
        self.pdf_files = pdf_files
        self.hoso: Optional[HoSo] = None
        
        # Thong tin phan tich file
        self.arc_codes: Set[str] = set()
        self.stt_list: List[int] = []
        self.file_info: Dict[Path, Tuple[Optional[str], Optional[int]]] = {}
        
        # Thong tin validation
        self.warnings: List[str] = []
        self.errors: List[str] = []
    
    def analyze_files(self) -> None:
        """Phan tich cac file trong thu muc"""
        grouper = FileGrouper()
        
        for pdf_file in self.pdf_files:
            arc_code, stt = grouper.extract_arc_and_stt(pdf_file.name)
            
            self.file_info[pdf_file] = (arc_code, stt)
            
            if arc_code:
                self.arc_codes.add(arc_code)
            
            if stt is not None:
                self.stt_list.append(stt)
        
        logger.info(f"Thu muc {self.folder_name}: {len(self.arc_codes)} arc_codes, {len(self.stt_list)} STT")
    
    def validate(self) -> List[str]:
        """Validate tinh hop le cua thu muc"""
        warnings = []
        
        # Kiem tra co >1 arc_code trong cung thu muc
        if len(self.arc_codes) > 1:
            warnings.append(f"Thu muc {self.folder_name}: Co {len(self.arc_codes)} arc_code khac nhau: {self.arc_codes}")
        
        # Kiem tra STT co lien tuc khong
        if self.stt_list:
            sorted_stt = sorted(self.stt_list)
            expected_stt = list(range(1, len(sorted_stt) + 1))
            
            if sorted_stt != expected_stt:
                warnings.append(f"Thu muc {self.folder_name}: STT khong lien tuc. Co: {sorted_stt}, mong doi: {expected_stt}")
        
        # Kiem tra co file trung STT
        stt_counter = Counter(self.stt_list)
        duplicates = [stt for stt, count in stt_counter.items() if count > 1]
        if duplicates:
            warnings.append(f"Thu muc {self.folder_name}: STT bi trung: {duplicates}")
        
        # Kiem tra co file khong theo pattern
        invalid_files = []
        for pdf_file, (arc_code, stt) in self.file_info.items():
            if arc_code is None and stt is None:
                invalid_files.append(pdf_file.name)
        
        if invalid_files:
            warnings.append(f"Thu muc {self.folder_name}: File khong theo pattern [arcCode].[STT].pdf: {invalid_files}")
        
        self.warnings = warnings
        return warnings
    
    def get_expected_arc_code(self) -> Optional[str]:
        """Lay arc_code chinh cua thu muc"""
        if len(self.arc_codes) == 1:
            return list(self.arc_codes)[0]
        elif len(self.arc_codes) > 1:
            # Chon arc_code xuat hien nhieu nhat
            arc_counter = Counter()
            for pdf_file, (arc_code, stt) in self.file_info.items():
                if arc_code:
                    arc_counter[arc_code] += 1
            
            if arc_counter:
                return arc_counter.most_common(1)[0][0]
        
        return None
    
    def create_tailieu_list(self) -> List[TaiLieu]:
        """Tao danh sach TaiLieu tu cac file PDF trong thu muc"""
        tailieu_list = []
        
        expected_arc_code = self.get_expected_arc_code()
        
        for pdf_file, (arc_code, stt) in self.file_info.items():
            # Tao TaiLieu co ban
            tailieu_data = {
                'stt': stt or len(tailieu_list) + 1,
                'filename': pdf_file.name,
                'duong_dan_file': str(pdf_file),
                'rel_href': f"representations/rep1/data/{pdf_file.name}",
            }
            
            # Neu co thong tin tu ten file
            if arc_code and stt:
                tailieu_data.update({
                    'title': f"Tai lieu {stt}",
                })
            
            try:
                tailieu = TaiLieu(**tailieu_data)
                tailieu_list.append(tailieu)
            except Exception as e:
                logger.error(f"Loi khi tao TaiLieu tu {pdf_file}: {e}")
        
        # Sap xep theo STT
        tailieu_list.sort(key=lambda x: x.stt)
        
        return tailieu_list
    
    def update_hoso_with_folder_info(self) -> None:
        """Cap nhat thong tin ho so tu thong tin thu muc"""
        if not self.hoso:
            return
        
        # Cap nhat arc_file_code neu chua co hoac khong khop
        expected_arc_code = self.get_expected_arc_code()
        if expected_arc_code and not self.hoso.arc_file_code:
            self.hoso.arc_file_code = expected_arc_code
        
        # Cap nhat original_folder_path - duong dan tuong doi tu PDF_Files
        self.hoso.original_folder_path = self.folder_path
        
        # Tao danh sach tai lieu tu file
        if not self.hoso.tai_lieu:
            self.hoso.tai_lieu = self.create_tailieu_list()
        
        logger.info(f"Cap nhat ho so {self.hoso.arc_file_code} voi {len(self.hoso.tai_lieu)} tai lieu")


def group_hoso_by_folder(pdf_root: str | Path, hoso_list: List[HoSo]) -> Dict[str, FolderGroup]:
    """
    Ham tien ich nhom ho so theo thu muc
    
    Args:
        pdf_root: Thu muc goc chua PDF
        hoso_list: Danh sach ho so tu Excel
        
    Returns:
        Dict[folder_name, FolderGroup]
    """
    grouper = FileGrouper()
    folder_groups = grouper.group_by_directory(pdf_root, hoso_list)
    
    # Cap nhat thong tin ho so tu thu muc
    for folder_group in folder_groups.values():
        folder_group.update_hoso_with_folder_info()
    
    # Validate
    warnings = grouper.validate_folder_consistency(folder_groups)
    if warnings:
        logger.warning(f"Co {len(warnings)} canh bao trong qua trinh nhom:")
        for warning in warnings:
            logger.warning(f"  - {warning}")
    
    return folder_groups
