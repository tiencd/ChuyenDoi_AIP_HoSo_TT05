"""
Validation Engine cho AIP Builder
Kiem tra tinh hop le va chat luong cua AIP packages
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from lxml import etree
import hashlib
import json

from .models import HoSo, TaiLieu, BuildSummary
from .config import Config

logger = logging.getLogger(__name__)


class ValidationResult:
    """Ket qua validation"""
    
    def __init__(self):
        self.is_valid: bool = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        self.validation_time: float = 0.0
        self.checked_files: int = 0
        self.total_size: int = 0
    
    def add_error(self, message: str):
        """Them loi nghiem trong"""
        self.errors.append(message)
        self.is_valid = False
        logger.error(f"Validation Error: {message}")
    
    def add_warning(self, message: str):
        """Them canh bao"""
        self.warnings.append(message)
        logger.warning(f"Validation Warning: {message}")
    
    def add_info(self, message: str):
        """Them thong tin"""
        self.info.append(message)
        logger.info(f"Validation Info: {message}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Lay tom tat ket qua"""
        return {
            'is_valid': self.is_valid,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'info_count': len(self.info),
            'validation_time': self.validation_time,
            'checked_files': self.checked_files,
            'total_size_mb': self.total_size / (1024 * 1024) if self.total_size > 0 else 0
        }


class CSIPValidator:
    """Validator cho AIP packages theo chuan CSIP"""
    
    def __init__(self, config: Config):
        self.config = config
        self.schema_cache: Dict[str, etree.XMLSchema] = {}
    
    def validate_package(self, package_dir: Path) -> ValidationResult:
        """
        Validation tong the cho 1 AIP package
        
        Args:
            package_dir: Thu muc chua AIP package
            
        Returns:
            ValidationResult: Ket qua validation
        """
        start_time = datetime.now()
        result = ValidationResult()
        
        logger.info(f"Bat dau validation package: {package_dir.name}")
        
        try:
            # 1. Kiem tra cau truc thu muc
            self._validate_directory_structure(package_dir, result)
            
            # 2. Kiem tra file METS.xml
            mets_path = package_dir / "METS.xml"
            if mets_path.exists():
                self._validate_mets_xml(mets_path, result)
            else:
                result.add_error("File METS.xml khong ton tai")
            
            # 3. Kiem tra metadata files
            self._validate_metadata_files(package_dir, result)
            
            # 4. Kiem tra representation files
            self._validate_representation_files(package_dir, result)
            
            # 5. Kiem tra tinh nhat quan
            self._validate_consistency(package_dir, result)
            
            # 6. Tinh toan thong ke
            result.total_size = self._calculate_total_size(package_dir)
            result.checked_files = self._count_files(package_dir)
            
        except Exception as e:
            result.add_error(f"Loi validation: {e}")
        
        # Tinh thoi gian
        end_time = datetime.now()
        result.validation_time = (end_time - start_time).total_seconds()
        
        logger.info(f"Hoan thanh validation trong {result.validation_time:.2f}s")
        return result
    
    def _validate_directory_structure(self, package_dir: Path, result: ValidationResult):
        """Kiem tra cau truc thu muc CSIP"""
        logger.debug("Kiem tra cau truc thu muc...")
        
        required_dirs = [
            "representations",
            "representations/rep1", 
            "representations/rep1/data",
            "metadata",
            "metadata/descriptive",
            "metadata/preservation"
        ]
        
        for dir_path in required_dirs:
            full_path = package_dir / dir_path
            if not full_path.exists():
                result.add_error(f"Thu muc bat buoc khong ton tai: {dir_path}")
            elif not full_path.is_dir():
                result.add_error(f"Duong dan khong phai thu muc: {dir_path}")
        
        result.add_info("Kiem tra cau truc thu muc hoan tat")
    
    def _validate_mets_xml(self, mets_path: Path, result: ValidationResult):
        """Kiem tra file METS.xml"""
        logger.debug("Kiem tra METS.xml...")
        
        try:
            # Doc XML
            with open(mets_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            # Parse XML
            try:
                doc = etree.fromstring(xml_content.encode('utf-8'))
            except etree.XMLSyntaxError as e:
                result.add_error(f"METS.xml khong hop le XML: {e}")
                return
            
            # Kiem tra namespace
            namespaces = doc.nsmap
            if 'http://www.loc.gov/METS/' not in namespaces.values():
                result.add_error("METS namespace khong dung")
            
            # Kiem tra cac element bat buoc
            required_elements = [
                ".//mets:metsHdr",
                ".//mets:dmdSec", 
                ".//mets:fileSec",
                ".//mets:structMap"
            ]
            
            ns = {'mets': 'http://www.loc.gov/METS/'}
            for xpath in required_elements:
                if doc.xpath(xpath, namespaces=ns) == []:
                    result.add_error(f"Element METS bat buoc khong co: {xpath}")
            
            # Kiem tra CSIP profile
            profile = doc.get('PROFILE')
            if not profile or 'csip' not in profile.lower():
                result.add_warning("METS khong co CSIP profile")
            
            result.add_info("METS.xml hop le")
            
        except Exception as e:
            result.add_error(f"Loi doc METS.xml: {e}")
    
    def _validate_metadata_files(self, package_dir: Path, result: ValidationResult):
        """Kiem tra cac file metadata"""
        logger.debug("Kiem tra metadata files...")
        
        # Kiem tra EAD
        ead_path = package_dir / "metadata" / "descriptive" / "ead.xml"
        if ead_path.exists():
            self._validate_ead_xml(ead_path, result)
        else:
            result.add_warning("File EAD.xml khong ton tai")
        
        # Kiem tra PREMIS
        premis_path = package_dir / "metadata" / "preservation" / "premis.xml"
        if premis_path.exists():
            self._validate_premis_xml(premis_path, result)
        else:
            result.add_warning("File PREMIS.xml khong ton tai")
    
    def _validate_ead_xml(self, ead_path: Path, result: ValidationResult):
        """Kiem tra file EAD.xml"""
        try:
            with open(ead_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            doc = etree.fromstring(xml_content.encode('utf-8'))
            
            # Kiem tra EAD namespace
            if doc.nsmap.get(None) != 'urn:isbn:1-931666-22-9':
                result.add_error("EAD namespace khong dung")
            
            # Kiem tra cac element chinh
            required = ['eadheader', 'archdesc']
            for elem in required:
                if doc.find(f".//{{{doc.nsmap[None]}}}{elem}") is None:
                    result.add_error(f"EAD thieu element: {elem}")
            
            result.add_info("EAD.xml hop le")
            
        except Exception as e:
            result.add_error(f"Loi kiem tra EAD: {e}")
    
    def _validate_premis_xml(self, premis_path: Path, result: ValidationResult):
        """Kiem tra file PREMIS.xml"""
        try:
            with open(premis_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            doc = etree.fromstring(xml_content.encode('utf-8'))
            
            # Kiem tra PREMIS namespace  
            premis_ns = 'http://www.loc.gov/premis/v3'
            if premis_ns not in doc.nsmap.values():
                result.add_error("PREMIS namespace khong dung")
            
            # Kiem tra version
            version = doc.get('version')
            if version != '3.0':
                result.add_warning(f"PREMIS version: {version}, nen la 3.0")
            
            result.add_info("PREMIS.xml hop le")
            
        except Exception as e:
            result.add_error(f"Loi kiem tra PREMIS: {e}")
    
    def _validate_representation_files(self, package_dir: Path, result: ValidationResult):
        """Kiem tra cac file trong representation"""
        logger.debug("Kiem tra representation files...")
        
        data_dir = package_dir / "representations" / "rep1" / "data"
        if not data_dir.exists():
            result.add_error("Thu muc data khong ton tai")
            return
        
        # Dem file
        pdf_files = list(data_dir.glob("*.pdf"))
        if len(pdf_files) == 0:
            result.add_warning("Khong co file PDF nao trong data")
        else:
            result.add_info(f"Tim thay {len(pdf_files)} file PDF")
        
        # Kiem tra file corrupted
        corrupted_count = 0
        for pdf_file in pdf_files:
            if not self._validate_pdf_file(pdf_file, result):
                corrupted_count += 1
        
        if corrupted_count > 0:
            result.add_warning(f"{corrupted_count} file PDF co van de")
    
    def _validate_pdf_file(self, pdf_path: Path, result: ValidationResult) -> bool:
        """Kiem tra 1 file PDF"""
        try:
            # Kiem tra kich thuoc
            if pdf_path.stat().st_size == 0:
                result.add_error(f"File PDF rong: {pdf_path.name}")
                return False
            
            # Kiem tra header PDF
            with open(pdf_path, 'rb') as f:
                header = f.read(8)
                if not header.startswith(b'%PDF-'):
                    result.add_error(f"File khong phai PDF: {pdf_path.name}")
                    return False
            
            return True
            
        except Exception as e:
            result.add_error(f"Loi kiem tra file {pdf_path.name}: {e}")
            return False
    
    def _validate_consistency(self, package_dir: Path, result: ValidationResult):
        """Kiem tra tinh nhat quan giua cac file"""
        logger.debug("Kiem tra tinh nhat quan...")
        
        try:
            # Doc METS de lay danh sach file
            mets_path = package_dir / "METS.xml"
            if not mets_path.exists():
                return
            
            with open(mets_path, 'r', encoding='utf-8') as f:
                mets_content = f.read()
            
            doc = etree.fromstring(mets_content.encode('utf-8'))
            ns = {'mets': 'http://www.loc.gov/METS/', 'xlink': 'http://www.w3.org/1999/xlink'}
            
            # Lay danh sach file tu METS
            file_elements = doc.xpath('.//mets:file', namespaces=ns)
            mets_files = set()
            
            for file_elem in file_elements:
                flocat = file_elem.find('.//mets:FLocat', namespaces=ns)
                if flocat is not None:
                    href = flocat.get('{http://www.w3.org/1999/xlink}href')
                    if href and href.startswith('representations/rep1/data/'):
                        filename = href.split('/')[-1]
                        mets_files.add(filename)
            
            # Lay danh sach file thuc te
            data_dir = package_dir / "representations" / "rep1" / "data"
            actual_files = set()
            if data_dir.exists():
                for file_path in data_dir.iterdir():
                    if file_path.is_file():
                        actual_files.add(file_path.name)
            
            # So sanh
            missing_in_mets = actual_files - mets_files
            missing_in_data = mets_files - actual_files
            
            for filename in missing_in_mets:
                result.add_warning(f"File ton tai nhung khong co trong METS: {filename}")
            
            for filename in missing_in_data:
                result.add_error(f"File trong METS nhung khong ton tai: {filename}")
            
            if len(missing_in_mets) == 0 and len(missing_in_data) == 0:
                result.add_info("Tinh nhat quan giua METS va file data: OK")
            
        except Exception as e:
            result.add_error(f"Loi kiem tra tinh nhat quan: {e}")
    
    def _calculate_total_size(self, package_dir: Path) -> int:
        """Tinh tong kich thuoc package"""
        total_size = 0
        try:
            for file_path in package_dir.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception:
            pass
        return total_size
    
    def _count_files(self, package_dir: Path) -> int:
        """Dem so file trong package"""
        count = 0
        try:
            for file_path in package_dir.rglob('*'):
                if file_path.is_file():
                    count += 1
        except Exception:
            pass
        return count
    
    def validate_multiple_packages(self, packages_dir: Path) -> Dict[str, ValidationResult]:
        """Validation nhieu packages"""
        logger.info(f"Bat dau validation tat ca packages trong: {packages_dir}")
        
        results = {}
        
        for package_dir in packages_dir.iterdir():
            if package_dir.is_dir() and package_dir.name.startswith('AIP_'):
                logger.info(f"Validation package: {package_dir.name}")
                results[package_dir.name] = self.validate_package(package_dir)
        
        logger.info(f"Hoan thanh validation {len(results)} packages")
        return results


class IntegrityChecker:
    """Kiem tra tinh toan ven cua file"""
    
    @staticmethod
    def verify_checksums(package_dir: Path) -> Tuple[bool, List[str]]:
        """
        Kiem tra checksum cac file trong package
        
        Returns:
            Tuple[bool, List[str]]: (is_valid, errors)
        """
        errors = []
        
        try:
            # Doc PREMIS de lay checksum
            premis_path = package_dir / "metadata" / "preservation" / "premis.xml"
            if not premis_path.exists():
                errors.append("Khong tim thay PREMIS.xml de kiem tra checksum")
                return False, errors
            
            # Parse PREMIS
            with open(premis_path, 'r', encoding='utf-8') as f:
                premis_content = f.read()
            
            doc = etree.fromstring(premis_content.encode('utf-8'))
            ns = {'premis': 'http://www.loc.gov/premis/v3'}
            
            # Lay thong tin checksum
            file_objects = doc.xpath('.//premis:object[@xsi:type="premis:file"]', 
                                   namespaces={**ns, 'xsi': 'http://www.w3.org/2001/XMLSchema-instance'})
            
            data_dir = package_dir / "representations" / "rep1" / "data"
            
            for file_obj in file_objects:
                # Lay ten file
                location = file_obj.find('.//premis:contentLocationValue', namespaces=ns)
                if location is None:
                    continue
                    
                file_path = location.text
                if not file_path or not file_path.startswith('representations/rep1/data/'):
                    continue
                
                filename = file_path.split('/')[-1]
                actual_file = data_dir / filename
                
                if not actual_file.exists():
                    errors.append(f"File khong ton tai: {filename}")
                    continue
                
                # Lay checksum tu PREMIS
                checksum_elem = file_obj.find('.//premis:messageDigest', namespaces=ns)
                if checksum_elem is None:
                    errors.append(f"Khong co checksum trong PREMIS cho file: {filename}")
                    continue
                
                expected_checksum = checksum_elem.text
                if expected_checksum == '[TO_BE_CALCULATED]':
                    continue  # Skip files chua tinh checksum
                
                # Tinh checksum thuc te
                actual_checksum = IntegrityChecker.calculate_sha256(actual_file)
                
                if actual_checksum.upper() != expected_checksum.upper():
                    errors.append(f"Checksum khong khop cho file {filename}: "
                                f"expected {expected_checksum}, got {actual_checksum}")
            
        except Exception as e:
            errors.append(f"Loi kiem tra checksum: {e}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def calculate_sha256(file_path: Path) -> str:
        """Tinh SHA-256 checksum"""
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Loi tinh checksum cho {file_path}: {e}")
            return ""
