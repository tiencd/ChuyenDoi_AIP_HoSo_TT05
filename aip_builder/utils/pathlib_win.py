"""
Pathlib Win - Utilities ho tro duong dan dai Windows

Chuc nang:
- Xu ly duong dan dai hon 260 ky tu su dung \\?\ prefix
- Chuyen doi duong dan Windows sang Unix format cho XML
- An toan trong viec thao tac file/thu muc
"""

import os
from pathlib import Path, PurePath, WindowsPath
from typing import Union, Optional
import logging

logger = logging.getLogger(__name__)

# Gioi han duong dan Windows mac dinh
DEFAULT_PATH_LIMIT = 260
LONG_PATH_PREFIX = "\\\\?\\"


class LongPath:
    """Wrapper cho Path voi ho tro duong dan dai Windows"""
    
    def __init__(self, path: Union[str, Path], use_long_path: Optional[bool] = None):
        self.original_path = Path(path)
        self.use_long_path = use_long_path
        
        # Tu dong quyet dinh co su dung long path hay khong
        if use_long_path is None:
            self.use_long_path = self._should_use_long_path()
    
    def _should_use_long_path(self) -> bool:
        """Xac dinh co nen su dung long path prefix hay khong"""
        if os.name != 'nt':  # Khong phai Windows
            return False
            
        # Kiem tra do dai duong dan
        path_str = str(self.original_path.resolve())
        return len(path_str) >= DEFAULT_PATH_LIMIT
    
    @property
    def actual_path(self) -> Path:
        """Duong dan thuc te de su dung trong cac thao tac file"""
        if not self.use_long_path:
            return self.original_path
        
        # Su dung long path prefix
        resolved = self.original_path.resolve()
        if not str(resolved).startswith(LONG_PATH_PREFIX):
            long_path_str = LONG_PATH_PREFIX + str(resolved)
            return Path(long_path_str)
        
        return resolved
    
    @property
    def xml_path(self) -> str:
        """Duong dan de su dung trong XML (Unix format, tuong doi neu can)"""
        return str(self.original_path).replace('\\', '/')
    
    def exists(self) -> bool:
        """Kiem tra file/thu muc co ton tai"""
        return self.actual_path.exists()
    
    def is_file(self) -> bool:
        """Kiem tra co phai file"""
        return self.actual_path.is_file()
    
    def is_dir(self) -> bool:
        """Kiem tra co phai thu muc"""
        return self.actual_path.is_dir()
    
    def stat(self):
        """Lay thong tin stat cua file"""
        return self.actual_path.stat()
    
    def open(self, *args, **kwargs):
        """Mo file"""
        return self.actual_path.open(*args, **kwargs)
    
    def read_bytes(self) -> bytes:
        """Doc file duoi dang bytes"""
        return self.actual_path.read_bytes()
    
    def write_bytes(self, data: bytes) -> int:
        """Ghi file duoi dang bytes"""
        return self.actual_path.write_bytes(data)
    
    def read_text(self, encoding: str = 'utf-8') -> str:
        """Doc file duoi dang text"""
        return self.actual_path.read_text(encoding=encoding)
    
    def write_text(self, data: str, encoding: str = 'utf-8') -> int:
        """Ghi file duoi dang text"""
        return self.actual_path.write_text(data, encoding=encoding)
    
    def mkdir(self, parents: bool = True, exist_ok: bool = True):
        """Tao thu muc"""
        return self.actual_path.mkdir(parents=parents, exist_ok=exist_ok)
    
    def iterdir(self):
        """Duyet cac item con trong thu muc"""
        return self.actual_path.iterdir()
    
    def rglob(self, pattern: str):
        """Tim kiem file theo pattern (recursive)"""
        return self.actual_path.rglob(pattern)
    
    def relative_to(self, other) -> Path:
        """Lay duong dan tuong doi"""
        if isinstance(other, LongPath):
            return self.original_path.relative_to(other.original_path)
        return self.original_path.relative_to(other)
    
    def __str__(self) -> str:
        return str(self.original_path)
    
    def __repr__(self) -> str:
        return f"LongPath({self.original_path!r}, use_long_path={self.use_long_path})"


def safe_path(path: Union[str, Path], use_long_path: Optional[bool] = None) -> LongPath:
    """
    Tao LongPath an toan cho duong dan
    
    Args:
        path: Duong dan goc
        use_long_path: Co su dung long path prefix khong (tu dong neu None)
        
    Returns:
        LongPath object
    """
    return LongPath(path, use_long_path)


def normalize_path_for_xml(path: Union[str, Path]) -> str:
    """
    Chuan hoa duong dan de su dung trong XML
    
    Args:
        path: Duong dan can chuan hoa
        
    Returns:
        Duong dan da chuan hoa (Unix format)
    """
    path_str = str(path)
    
    # Loai bo long path prefix neu co
    if path_str.startswith(LONG_PATH_PREFIX):
        path_str = path_str[len(LONG_PATH_PREFIX):]
    
    # Chuyen thanh Unix format
    return path_str.replace('\\', '/')


def make_relative_path(full_path: Union[str, Path], base_path: Union[str, Path]) -> str:
    """
    Tao duong dan tuong doi tu base_path den full_path
    
    Args:
        full_path: Duong dan day du
        base_path: Duong dan goc
        
    Returns:
        Duong dan tuong doi (Unix format)
    """
    try:
        full_path = Path(full_path).resolve()
        base_path = Path(base_path).resolve()
        
        relative = full_path.relative_to(base_path)
        return normalize_path_for_xml(relative)
        
    except ValueError:
        # Neu khong tao duoc duong dan tuong doi, tra ve duong dan day du
        logger.warning(f"Khong the tao duong dan tuong doi tu {base_path} den {full_path}")
        return normalize_path_for_xml(full_path)


def ensure_directory(path: Union[str, Path, LongPath]) -> LongPath:
    """
    Dam bao thu muc ton tai, tao neu chua co
    
    Args:
        path: Duong dan thu muc
        
    Returns:
        LongPath cua thu muc
    """
    if isinstance(path, LongPath):
        long_path = path
    else:
        long_path = safe_path(path)
    
    if not long_path.exists():
        logger.info(f"Tao thu muc: {long_path}")
        long_path.mkdir()
    
    return long_path


def safe_copy_file(src: Union[str, Path], dst: Union[str, Path]) -> bool:
    """
    Copy file an toan voi ho tro duong dan dai
    
    Args:
        src: File nguon
        dst: File dich
        
    Returns:
        True neu thanh cong, False neu that bai
    """
    try:
        src_path = safe_path(src)
        dst_path = safe_path(dst)
        
        # Dam bao thu muc dich ton tai
        ensure_directory(dst_path.actual_path.parent)
        
        # Copy file
        import shutil
        shutil.copy2(src_path.actual_path, dst_path.actual_path)
        
        logger.debug(f"Copy thanh cong: {src} -> {dst}")
        return True
        
    except Exception as e:
        logger.error(f"Loi copy file {src} -> {dst}: {e}")
        return False


def get_file_size(path: Union[str, Path]) -> int:
    """
    Lay kich thuoc file
    
    Args:
        path: Duong dan file
        
    Returns:
        Kich thuoc file (bytes), 0 neu loi
    """
    try:
        long_path = safe_path(path)
        return long_path.stat().st_size
    except Exception:
        return 0


def is_path_too_long(path: Union[str, Path], limit: int = DEFAULT_PATH_LIMIT) -> bool:
    """
    Kiem tra duong dan co qua dai khong
    
    Args:
        path: Duong dan can kiem tra
        limit: Gioi han do dai
        
    Returns:
        True neu qua dai
    """
    return len(str(Path(path).resolve())) >= limit
