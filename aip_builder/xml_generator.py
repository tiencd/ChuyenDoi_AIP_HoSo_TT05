"""
XML Template Generator cho AIP Builder
Sinh ra cac XML template theo chuan CSIP
"""
import logging
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, Template

from .models import HoSo, TaiLieu
from .config import Config

logger = logging.getLogger(__name__)


class XMLTemplateGenerator:
    """Sinh cac XML template cho AIP package"""
    
    def __init__(self, config: Config):
        self.config = config
        self.template_dir = Path(__file__).parent / 'templates'
        
        # Khoi tao Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=False
        )
        
        # Dang ky cac filter
        self._register_filters()
    
    def _calculate_sha256(self, file_path: str) -> str:
        """Tinh SHA-256 checksum cho file"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            logger.warning(f"Khong the tinh SHA-256 cho {file_path}: {e}")
            return ""
    
    def _get_file_size(self, file_path: str) -> int:
        """Lay kich thuoc file"""
        try:
            return os.path.getsize(file_path)
        except Exception as e:
            logger.warning(f"Khong the lay kich thuoc file {file_path}: {e}")
            return 0
    
    def _register_filters(self):
        """Dang ky cac custom filter cho Jinja2"""
        
        def format_date(value, format='%Y-%m-%dT%H:%M:%S'):
            """Format datetime object"""
            if isinstance(value, datetime):
                return value.strftime(format)
            return str(value)
        
        def escape_xml(value):
            """Escape XML characters"""
            if not value:
                return ''
            return str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')
        
        def safe_filename(value):
            """Tao filename an toan"""
            import re
            if not value:
                return 'unknown'
            return re.sub(r'[^a-zA-Z0-9_.-]', '_', str(value))
        
        def basename(value):
            """Lay ten file tu duong dan"""
            from pathlib import Path
            if not value:
                return 'unknown.pdf'
            return Path(str(value)).name
        
        def random_uuid():
            """Tao UUID ngau nhien"""
            from uuid import uuid4
            return str(uuid4()).replace('-', '')
        
        def uuid4(value=None):
            """Tao UUID4"""
            from uuid import uuid4 as _uuid4
            return str(_uuid4())
        
        # Dang ky filter
        self.env.filters['format_date'] = format_date
        self.env.filters['escape_xml'] = escape_xml
        self.env.filters['safe_filename'] = safe_filename
        self.env.filters['basename'] = basename
        self.env.filters['random_uuid'] = random_uuid
        self.env.filters['uuid4'] = uuid4
    
    def generate_mets(self, hoso: HoSo, package_id: str) -> str:
        """
        Sinh METS XML cho ho so
        """
        logger.info(f"Sinh METS cho ho so: {hoso.arc_file_code}")
        
        template = self.env.get_template('mets_template.xml')
        
        # Chuan bi du lieu
        context = {
            'package_id': package_id,
            'hoso': hoso,
            'config': self.config,
            'created_time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S+07:00'),
            'agent_name': self.config.agent_name,
            'agent_version': self.config.agent_version
        }
        
        return template.render(context)
    
    def generate_ead(self, hoso: HoSo, package_id: str) -> str:
        """
        Sinh EAD XML cho ho so - mo ta archive
        """
        logger.info(f"Sinh EAD cho ho so: {hoso.arc_file_code}")
        
        template = self.env.get_template('ead_template.xml')
        
        context = {
            'package_id': package_id,
            'hoso': hoso,
            'config': self.config,
            'created_time': datetime.now()
        }
        
        return template.render(context)
    
    def generate_premis(self, hoso: HoSo, package_id: str) -> str:
        """
        Sinh PREMIS XML cho ho so - thong tin bao quan
        """
        logger.info(f"Sinh PREMIS cho ho so: {hoso.arc_file_code}")
        
        template = self.env.get_template('premis_template.xml')
        
        context = {
            'package_id': package_id,
            'hoso': hoso,
            'config': self.config,
            'created_time': datetime.now()
        }
        
        return template.render(context)
    
    def generate_premis_rep(self, hoso: HoSo, package_id: str) -> str:
        """
        Sinh PREMIS_rep1.xml cho representation level - thong tin bao quan cap dai dien
        """
        logger.info(f"Sinh PREMIS_rep1 cho ho so: {hoso.arc_file_code}")
        
        template = self.env.get_template('premis_rep_template.xml')
        
        context = {
            'package_id': package_id,
            'hoso': hoso,
            'config': self.config,
            'created_time': datetime.now()
        }
        
        return template.render(context)
    
    def generate_ead_document(self, tai_lieu: TaiLieu, hoso: HoSo, package_id: str) -> str:
        """
        Sinh file EAD cho 1 tai lieu cu the theo thiet ke moi
        
        Args:
            tai_lieu: Doi tuong TaiLieu can sinh EAD
            hoso: Ho so chua tai lieu
            package_id: ID cua package
            
        Returns:
            Noi dung XML EAD cho tai lieu
        """
        logger.debug(f"Sinh EAD cho tai lieu: {tai_lieu.effective_title}")
        
        try:
            template = self.env.get_template('ead_document.xml')
            
            context = {
                'tai_lieu': tai_lieu,
                'hoso': hoso, 
                'package_id': package_id,
                'created_time': datetime.now(),
                'config': self.config
            }
            
            return template.render(context)
            
        except Exception as e:
            logger.error(f"Loi sinh EAD cho tai lieu {tai_lieu.effective_title}: {e}")
            raise

    def generate_rep_mets(self, hoso: HoSo, package_id: str) -> str:
        """
        Sinh file METS cho representation level (rep1/METS.xml)
        
        Args:
            hoso: Ho so can xu ly
            package_id: ID cua package
            
        Returns:
            Noi dung XML METS cho representation
        """
        logger.debug(f"Sinh rep1/METS.xml cho ho so: {hoso.arc_file_code}")
        
        try:
            template = self.env.get_template('rep_mets.xml')
            
            context = {
                'hoso': hoso,
                'package_id': package_id,
                'created_time': datetime.now(),
                'config': self.config
            }
            
            return template.render(context)
            
        except Exception as e:
            logger.error(f"Loi sinh rep METS cho {hoso.arc_file_code}: {e}")
            raise

    def generate_all_xml(self, hoso: HoSo, package_id: str) -> Dict[str, Any]:
        """
        Sinh tat ca cac XML can thiet cho 1 ho so theo thiet ke moi
        
        Returns:
            Dict voi cac key: 
            - 'mets': METS goc 
            - 'rep_mets': METS representation
            - 'ead': EAD tong hop (neu can)
            - 'ead_docs': Dict cac EAD rieng theo file_id
            - 'premis': PREMIS
        """
        logger.info(f"Sinh tat ca XML cho ho so: {hoso.arc_file_code}")
        
        try:
            results = {
                'mets': self.generate_mets(hoso, package_id),
                'rep_mets': self.generate_rep_mets(hoso, package_id),
                'ead': self.generate_ead(hoso, package_id), 
                'premis': self.generate_premis(hoso, package_id),
                'premis_rep': self.generate_premis_rep(hoso, package_id),  # New: PREMIS for representation level
                'ead_docs': {}
            }
            
            # Sinh EAD rieng cho tung tai lieu
            for tai_lieu in hoso.tai_lieu:
                if hasattr(tai_lieu, 'file_id') and tai_lieu.file_id:
                    file_id = tai_lieu.file_id
                    results['ead_docs'][file_id] = self.generate_ead_document(tai_lieu, hoso, package_id)
                    logger.debug(f"Sinh EAD_doc_{file_id}.xml cho tai lieu: {tai_lieu.effective_title}")
            
            logger.info(f"Sinh thanh cong {len(results)} XML types cho {hoso.arc_file_code}")
            logger.info(f"Sinh {len(results['ead_docs'])} EAD documents rieng")
            return results
            
        except Exception as e:
            logger.error(f"Loi khi sinh XML cho {hoso.arc_file_code}: {e}")
            raise
    
    def update_mets_with_metadata_files(self, mets_content: str, ead_file_path: str, premis_file_path: str) -> str:
        """
        Cap nhat METS voi thong tin thuc te cua cac file metadata
        
        Args:
            mets_content: Noi dung METS hien tai
            ead_file_path: Duong dan toi file EAD.xml
            premis_file_path: Duong dan toi file PREMIS.xml
            
        Returns:
            Noi dung METS da cap nhat
        """
        logger.debug("Cap nhat METS voi thong tin metadata files")
        
        try:
            # Tinh toan thong tin thuc te cho EAD
            ead_size = self._get_file_size(ead_file_path) if os.path.exists(ead_file_path) else 0
            ead_checksum = self._calculate_sha256(ead_file_path) if os.path.exists(ead_file_path) else ""
            
            # Tinh toan thong tin thuc te cho PREMIS  
            premis_size = self._get_file_size(premis_file_path) if os.path.exists(premis_file_path) else 0
            premis_checksum = self._calculate_sha256(premis_file_path) if os.path.exists(premis_file_path) else ""
            
            # Cap nhat noi dung METS bang cach thay the placeholders
            updated_content = mets_content
            
            # Thay the placeholders EAD
            updated_content = updated_content.replace("PLACEHOLDER_EAD_SIZE", str(ead_size))
            updated_content = updated_content.replace("PLACEHOLDER_EAD_CHECKSUM", ead_checksum)
            
            # Thay the placeholders PREMIS
            updated_content = updated_content.replace("PLACEHOLDER_PREMIS_SIZE", str(premis_size))
            updated_content = updated_content.replace("PLACEHOLDER_PREMIS_CHECKSUM", premis_checksum)
            
            logger.debug(f"Cap nhat METS: EAD size={ead_size}, checksum={ead_checksum[:8] if ead_checksum else 'empty'}...")
            logger.debug(f"Cap nhat METS: PREMIS size={premis_size}, checksum={premis_checksum[:8] if premis_checksum else 'empty'}...")
            
            return updated_content
            
        except Exception as e:
            logger.error(f"Loi cap nhat METS voi metadata files: {e}")
            return mets_content  # Tra ve noi dung goc neu co loi
