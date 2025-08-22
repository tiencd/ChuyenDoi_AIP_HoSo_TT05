"""
PDF Probe - Module quet va trich thong tin tu file PDF

Chuc nang chinh:
- Tinh toan SHA-256, size, mtime cho tung PDF
- Doc so trang su dung PyPDF2
- Ho tro duong dan dai Windows voi \\?\
- Extract metadata co ban tu PDF
"""

import hashlib
import os
from pathlib import Path, PurePath
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
from dataclasses import dataclass

try:
    from PyPDF2 import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfFileReader as PdfReader
    except ImportError:
        PdfReader = None
        logging.warning("PyPDF2 khong duoc cai dat. Khong the doc so trang PDF")

logger = logging.getLogger(__name__)


@dataclass
class PDFInfo:
    """Thong tin ve file PDF"""
    filepath: Path
    filename: str
    size: int
    mtime: datetime
    sha256: str
    pages: Optional[int] = None
    pdf_version: Optional[str] = None
    is_encrypted: bool = False
    has_text: bool = False
    error: Optional[str] = None


class PDFProbe:
    """Class quet thong tin file PDF"""
    
    def __init__(self, use_long_path_prefix: bool = True):
        self.use_long_path_prefix = use_long_path_prefix
        self.max_path_length = 240
        
    def probe_file(self, file_path: str | Path) -> PDFInfo:
        """
        Quet thong tin chi tiet tu mot file PDF
        
        Args:
            file_path: Duong dan den file PDF
            
        Returns:
            PDFInfo chua thong tin file
        """
        file_path = Path(file_path)
        
        # Su dung long path prefix neu can thiet (Windows)
        actual_path = self._get_actual_path(file_path)
        
        try:
            # Kiem tra file co ton tai khong
            if not actual_path.exists():
                return PDFInfo(
                    filepath=file_path,
                    filename=file_path.name,
                    size=0,
                    mtime=datetime.now(),
                    sha256="",
                    error=f"File khong ton tai: {file_path}"
                )
            
            # Thong tin co ban tu OS
            stat_info = actual_path.stat()
            size = stat_info.st_size
            mtime = datetime.fromtimestamp(stat_info.st_mtime)
            
            # Tinh SHA-256
            sha256 = self._calculate_sha256(actual_path)
            
            # Khoi tao PDFInfo
            pdf_info = PDFInfo(
                filepath=file_path,
                filename=file_path.name,
                size=size,
                mtime=mtime,
                sha256=sha256
            )
            
            # Doc thong tin PDF neu PyPDF2 co san
            if PdfReader:
                self._extract_pdf_metadata(actual_path, pdf_info)
            else:
                logger.warning("PyPDF2 khong co san, bo qua thong tin PDF")
                pdf_info.error = "PyPDF2 not available"
            
            return pdf_info
            
        except Exception as e:
            logger.error(f"Loi khi quet file {file_path}: {e}")
            return PDFInfo(
                filepath=file_path,
                filename=file_path.name,
                size=0,
                mtime=datetime.now(),
                sha256="",
                error=str(e)
            )
    
    def _get_actual_path(self, file_path: Path) -> Path:
        """Lay duong dan thuc te, su dung long path prefix neu can"""
        if (self.use_long_path_prefix and 
            os.name == 'nt' and  # Windows
            len(str(file_path)) > self.max_path_length):
            
            # Su dung \\?\ prefix cho duong dan dai
            if file_path.is_absolute():
                long_path = f"\\\\?\\{file_path}"
            else:
                long_path = f"\\\\?\\{file_path.resolve()}"
            return Path(long_path)
        
        return file_path
    
    def _calculate_sha256(self, file_path: Path) -> str:
        """Tinh SHA-256 checksum cua file"""
        hash_sha256 = hashlib.sha256()
        
        try:
            with open(file_path, 'rb') as f:
                # Doc file theo chunk de tiet kiem bo nho
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_sha256.update(chunk)
            
            return hash_sha256.hexdigest()
            
        except Exception as e:
            logger.error(f"Loi khi tinh SHA-256 cho {file_path}: {e}")
            return ""
    
    def _extract_pdf_metadata(self, file_path: Path, pdf_info: PDFInfo) -> None:
        """Trich xuat metadata tu PDF su dung PyPDF2"""
        try:
            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
                
                # So trang - Su dung API moi
                pdf_info.pages = len(reader.pages)
                pdf_info.is_encrypted = reader.is_encrypted
                
                # Thu lay metadata
                if hasattr(reader, 'metadata') and reader.metadata:
                    producer = reader.metadata.get('/Producer', '')
                    if producer:
                        pdf_info.pdf_version = str(producer)
                
                # Kiem tra co text khong (doc trang dau tien)
                try:
                    if pdf_info.pages and pdf_info.pages > 0:
                        page = reader.pages[0]
                        text = page.extract_text()
                        pdf_info.has_text = bool(text and text.strip())
                except Exception:
                    pdf_info.has_text = False
                    
        except Exception as e:
            logger.warning(f"Loi khi doc PDF metadata tu {file_path}: {e}")
            pdf_info.error = f"PDF read error: {e}"
    
    def probe_directory(self, directory: str | Path, pattern: str = "*.pdf") -> List[PDFInfo]:
        """
        Quet tat ca file PDF trong thu muc
        
        Args:
            directory: Thu muc can quet
            pattern: Pattern file (mac dinh *.pdf)
            
        Returns:
            List PDFInfo cua tat ca file
        """
        directory = Path(directory)
        
        if not directory.exists():
            logger.error(f"Thu muc khong ton tai: {directory}")
            return []
        
        # Tim tat ca file PDF (bao gom trong sub-directory)
        pdf_files = list(directory.rglob(pattern))
        logger.info(f"Tim thay {len(pdf_files)} file PDF trong {directory}")
        
        results = []
        for pdf_file in pdf_files:
            pdf_info = self.probe_file(pdf_file)
            results.append(pdf_info)
        
        return results
    
    def probe_file_list(self, file_paths: List[str | Path]) -> List[PDFInfo]:
        """
        Quet danh sach file PDF
        
        Args:
            file_paths: Danh sach duong dan file
            
        Returns:
            List PDFInfo tuong ung
        """
        results = []
        for file_path in file_paths:
            pdf_info = self.probe_file(file_path)
            results.append(pdf_info)
        
        return results


def probe_pdf(file_path: str | Path) -> PDFInfo:
    """
    Ham tien ich quet 1 file PDF
    
    Args:
        file_path: Duong dan file PDF
        
    Returns:
        PDFInfo chua thong tin file
    """
    probe = PDFProbe()
    return probe.probe_file(file_path)


def probe_pdf_directory(directory: str | Path, pattern: str = "*.pdf") -> List[PDFInfo]:
    """
    Ham tien ich quet tat ca PDF trong thu muc
    
    Args:
        directory: Thu muc can quet
        pattern: Pattern file
        
    Returns:
        List PDFInfo
    """
    probe = PDFProbe()
    return probe.probe_directory(directory, pattern)


def update_tailieu_with_pdf_info(tailieu_list: List, pdf_root: str | Path) -> List:
    """
    Cap nhat thong tin PDF vao danh sach TaiLieu model
    
    Args:
        tailieu_list: List TaiLieu model
        pdf_root: Thu muc goc chua PDF
        
    Returns:
        List TaiLieu da cap nhat
    """
    pdf_root = Path(pdf_root)
    probe = PDFProbe()
    
    updated_list = []
    for tailieu in tailieu_list:
        # Tim file PDF tuong ung
        pdf_path = pdf_root / tailieu.duong_dan_file.replace('\\', '/')
        
        if not pdf_path.exists():
            # Thu tim theo filename
            pdf_files = list(pdf_root.rglob(tailieu.filename))
            if pdf_files:
                pdf_path = pdf_files[0]
            else:
                logger.warning(f"Khong tim thay file PDF: {tailieu.filename}")
                updated_list.append(tailieu)
                continue
        
        # Quet thong tin PDF
        pdf_info = probe.probe_file(pdf_path)
        
        # Cap nhat vao TaiLieu model
        tailieu.size = pdf_info.size
        tailieu.mtime = pdf_info.mtime
        tailieu.sha256 = pdf_info.sha256
        tailieu.pages = pdf_info.pages
        
        # Cap nhat rel_href dua tren duong dan thuc te
        rel_path = pdf_path.relative_to(pdf_root)
        tailieu.rel_href = f"representations/rep1/data/{rel_path.as_posix()}"
        
        updated_list.append(tailieu)
    
    logger.info(f"Cap nhat thong tin PDF cho {len(updated_list)} tai lieu")
    return updated_list
