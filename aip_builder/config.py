"""
Config - Cau hinh mac dinh cho AIP Builder

Chua cac cau hinh ve:
- Duong dan mac dinh
- Cau hinh XML/metadata
- Thong tin agent/organization
- Template settings
"""

from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import os
from datetime import datetime


@dataclass
class Config:
    """Lop cau hinh chinh cho AIP Builder"""
    
    # Duong dan mac dinh
    default_meta_path: str = "data/input/metadata.xlsx"
    default_pdf_root: str = "data/input/PDF_Files" 
    default_output_prefix: str = "data/output"
    default_keep_folders: bool = True
    
    # Organization info
    organization_name: str = "Công ty cổ phần công nghệ Lưu trữ - Số hóa HT"
    organization_email: str = "tiencd89@gmail.com"
    agency_code: str = "HTJSC"
    repository_code: str = "NARA"
    
    # Cau hinh XML
    mets_namespace: str = "http://www.loc.gov/METS/"
    csip_namespace: str = "https://DILCIS.eu/XML/METS/CSIPExtensionMETS"
    ead_namespace: str = "urn:isbn:1-931666-22-9"
    premis_namespace: str = "http://www.loc.gov/premis/v3"
    xlink_namespace: str = "http://www.w3.org/1999/xlink"
    xsi_namespace: str = "http://www.w3.org/2001/XMLSchema-instance"
    
    # Thong tin agent/organization
    agent_role: str = "CREATOR"
    agent_type: str = "ORGANIZATION" 
    agent_name: str = "AIP Builder System"
    agent_version: str = "1.0.0"
    organization_code: str = "AIP_BUILDER"
    
    # Cau hinh checksum
    checksum_algorithm: str = "SHA-256"
    
    # Cau hinh file
    max_path_length: int = 240  # Windows path limit
    use_long_path_prefix: bool = True  # Su dung \\?\ prefix
    
    # Template settings
    template_dir: str = "aip_builder/templates"
    schema_dir: str = "aip_builder/schemas"
    
    # Encoding settings
    xml_encoding: str = "utf-8"
    excel_encoding: str = "utf-8"
    
    # Validation settings
    validate_xml_against_xsd: bool = True
    strict_validation: bool = False
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Performance
    max_workers: int = 4  # So thread dong thoi
    chunk_size: int = 1000  # Kich thuoc chunk khi xu ly du lieu lon
    
    @property
    def output_dir_with_timestamp(self) -> str:
        """Tao ten thu muc output voi timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{self.default_output_prefix}_{timestamp}"
    
    @property
    def namespaces(self) -> Dict[str, str]:
        """Dict cac namespace de dung trong XML"""
        return {
            'mets': self.mets_namespace,
            'csip': self.csip_namespace, 
            'ead': self.ead_namespace,
            'premis': self.premis_namespace,
            'xlink': self.xlink_namespace,
            'xsi': self.xsi_namespace,
        }
    
    def get_template_path(self, template_name: str) -> Path:
        """Lay duong dan template"""
        return Path(self.template_dir) / template_name
    
    def get_schema_path(self, schema_name: str) -> Path:
        """Lay duong dan schema"""
        return Path(self.schema_dir) / schema_name
    
    def validate_paths(self) -> bool:
        """Kiem tra cac duong dan co hop le khong"""
        paths_to_check = [
            self.template_dir,
            self.schema_dir,
        ]
        
        for path_str in paths_to_check:
            path = Path(path_str)
            if not path.exists():
                print(f"Warning: Path does not exist: {path}")
                return False
        return True
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Tao config tu environment variables"""
        config = cls()
        
        # Override tu env vars neu co
        if meta_path := os.getenv('AIP_META_PATH'):
            config.default_meta_path = meta_path
        
        if pdf_root := os.getenv('AIP_PDF_ROOT'):
            config.default_pdf_root = pdf_root
            
        if output_prefix := os.getenv('AIP_OUTPUT_PREFIX'):
            config.default_output_prefix = output_prefix
        
        if agent_name := os.getenv('AIP_AGENT_NAME'):
            config.agent_name = agent_name
            
        if org_code := os.getenv('AIP_ORG_CODE'):
            config.organization_code = org_code
            
        if log_level := os.getenv('AIP_LOG_LEVEL'):
            config.log_level = log_level
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Chuyen config thanh dict"""
        return {
            'default_meta_path': self.default_meta_path,
            'default_pdf_root': self.default_pdf_root,
            'default_output_prefix': self.default_output_prefix,
            'default_keep_folders': self.default_keep_folders,
            'agent_name': self.agent_name,
            'organization_code': self.organization_code,
            'checksum_algorithm': self.checksum_algorithm,
            'xml_encoding': self.xml_encoding,
            'validate_xml_against_xsd': self.validate_xml_against_xsd,
            'log_level': self.log_level,
            'max_workers': self.max_workers,
        }


# Instance mac dinh
default_config = Config()

def get_config() -> Config:
    """Lay config mac dinh"""
    return default_config

def set_config(config: Config) -> None:
    """Dat config moi"""
    global default_config
    default_config = config
