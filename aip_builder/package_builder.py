"""
Package Builder cho AIP Builder
Tao cau truc thu muc va sao chep file theo chuan AIP/CSIP
"""
import logging
import shutil
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import uuid

from .models import HoSo, TaiLieu, PackagePlan, BuildSummary
from .config import Config
from .pdf_probe import PDFProbe
from .xml_generator import XMLTemplateGenerator
from .utils.pathlib_win import LongPath

logger = logging.getLogger(__name__)


class PackageBuilder:
    """Xay dung goi AIP theo chuan CSIP"""
    
    def __init__(self, config: Config, cleanup_folders: bool = False):
        self.config = config
        self.pdf_probe = PDFProbe()
        self.xml_generator = XMLTemplateGenerator(config)
        self.cleanup_folders = cleanup_folders  # Tuy chon xoa folder sau khi tao ZIP
    
    def create_package_structure(self, output_dir: Path, package_id: str) -> Dict[str, Path]:
        """
        Tao cau truc thu muc AIP theo thiet ke moi - Updated Design
        Them schemas/ directory va cau truc CSIP 1.2 day du
        
        Returns:
            Dict chua duong dan cac thu muc chinh
        """
        logger.info(f"Tao cau truc thu muc cho package: {package_id}")
        
        package_dir = output_dir / package_id
        
        # Cau truc thu muc AIP theo thiet ke moi
        dirs = {
            'root': package_dir,
            'representations': package_dir / 'representations',
            'rep1': package_dir / 'representations' / 'rep1',
            'rep1_data': package_dir / 'representations' / 'rep1' / 'data',
            'rep1_metadata': package_dir / 'representations' / 'rep1' / 'metadata',
            'rep1_descriptive': package_dir / 'representations' / 'rep1' / 'metadata' / 'descriptive',  # New: rep1 descriptive metadata
            'rep1_preservation': package_dir / 'representations' / 'rep1' / 'metadata' / 'preservation',  # New: rep1 preservation metadata
            'metadata': package_dir / 'metadata',
            'descriptive': package_dir / 'metadata' / 'descriptive',
            'preservation': package_dir / 'metadata' / 'preservation',
            'schemas': package_dir / 'schemas',  # New: XSD files directory
        }
        
        # Tao cac thu muc
        for dir_name, dir_path in dirs.items():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Tao thu muc {dir_name}: {dir_path}")
        
        return dirs
    
    def copy_pdf_files(self, hoso: HoSo, pdf_root: Path, rep1_data_dir: Path) -> Tuple[int, int]:
        """
        Sao chep cac file PDF vao thu muc data
        
        Returns:
            Tuple[int, int]: (so_file_thanh_cong, so_file_loi)
        """
        logger.info(f"Sao chep file PDF cho ho so: {hoso.arc_file_code}")
        
        success_count = 0
        error_count = 0
        
        for tailieu in hoso.tai_lieu:
            if not tailieu.duongDanFile:
                logger.warning(f"Tai lieu khong co duongDanFile: {tailieu.trich_yeu}")
                error_count += 1
                continue
            
            try:
                # Duong dan file goc
                source_path = pdf_root / tailieu.duongDanFile.lstrip('\\/')
                # Khong can dung LongPath.normalize vi no la instance method
                if not source_path.exists():
                    logger.error(f"File khong ton tai: {source_path}")
                    error_count += 1
                    continue
                
                # Ten file dich
                target_filename = source_path.name
                target_path = rep1_data_dir / target_filename
                
                # Neu file da ton tai va co kich thuoc khac nhau -> doi ten
                if target_path.exists():
                    if target_path.stat().st_size != source_path.stat().st_size:
                        # Them suffix de phan biet
                        stem = target_path.stem
                        suffix = target_path.suffix
                        counter = 1
                        while target_path.exists():
                            target_path = rep1_data_dir / f"{stem}_{counter:03d}{suffix}"
                            counter += 1
                        target_filename = target_path.name
                
                # Sao chep file
                shutil.copy2(source_path, target_path)
                
                # Cap nhat thong tin file trong tailieu
                file_info = self.pdf_probe.probe_file(source_path)
                tailieu.file_path = target_path
                tailieu.filename = target_filename
                tailieu.file_size = file_info.size
                tailieu.checksum = file_info.sha256
                
                if file_info.pages and not tailieu.so_trang:
                    tailieu.so_trang = file_info.pages
                
                success_count += 1
                logger.debug(f"Sao chep thanh cong: {source_path} -> {target_path}")
                
            except Exception as e:
                logger.error(f"Loi sao chep file {source_path}: {e}")
                error_count += 1
                continue
        
        logger.info(f"Sao chep xong: {success_count} thanh cong, {error_count} loi")
        return success_count, error_count
    
    def generate_metadata_files(self, hoso: HoSo, package_id: str, dirs: Dict[str, Path]) -> None:
        """Sinh cac file metadata XML"""
        logger.info(f"Sinh metadata cho package: {package_id}")
        
        try:
            # Sinh XML theo thiet ke moi
            xmls = self.xml_generator.generate_all_xml(hoso, package_id)
            
            # Ghi file METS goc (root level) - ban dau voi placeholders
            mets_path = dirs['root'] / 'METS.xml'
            mets_path.write_text(xmls['mets'], encoding='utf-8')
            logger.info(f"Tao METS.xml: {mets_path}")
            
            # Ghi file METS representation level (rep1/METS.xml)
            if 'rep_mets' in xmls:
                rep_mets_path = dirs['rep1'] / 'METS.xml'
                rep_mets_path.write_text(xmls['rep_mets'], encoding='utf-8')
                logger.info(f"Tao rep1/METS.xml: {rep_mets_path}")
            
            # Ghi cac file EAD_doc_FileX.xml rieng cho tung tai lieu
            if 'ead_docs' in xmls and xmls['ead_docs']:
                for file_id, ead_content in xmls['ead_docs'].items():
                    ead_doc_path = dirs['rep1_descriptive'] / f'EAD_doc_{file_id}.xml'
                    ead_doc_path.write_text(ead_content, encoding='utf-8')
                    logger.info(f"Tao EAD_doc_{file_id}.xml: {ead_doc_path}")
            
            # Ghi file EAD tong hop (neu can)
            ead_path = dirs['descriptive'] / 'EAD.xml'  # Sửa tên file cho đúng
            if 'ead' in xmls:
                ead_path.write_text(xmls['ead'], encoding='utf-8')
                logger.info(f"Tao EAD.xml: {ead_path}")
            
            # Ghi file PREMIS  
            premis_path = dirs['preservation'] / 'PREMIS.xml'  # Sửa tên file cho đúng
            premis_path.write_text(xmls['premis'], encoding='utf-8')
            logger.info(f"Tao PREMIS.xml: {premis_path}")
            
            # Ghi file PREMIS representation level (rep1/metadata/preservation/PREMIS_rep1.xml)
            if 'premis_rep' in xmls:
                premis_rep_path = dirs['rep1_preservation'] / 'PREMIS_rep1.xml'
                premis_rep_path.write_text(xmls['premis_rep'], encoding='utf-8')
                logger.info(f"Tao PREMIS_rep1.xml: {premis_rep_path}")
            
            # Cap nhat METS voi thong tin thuc te cua metadata files
            logger.debug("Cap nhat METS voi thong tin metadata files thuc te...")
            updated_mets = self.xml_generator.update_mets_with_metadata_files(
                xmls['mets'], 
                str(ead_path), 
                str(premis_path)
            )
            
            # Ghi lai METS da cap nhat
            mets_path.write_text(updated_mets, encoding='utf-8')
            logger.info(f"Cap nhat METS.xml voi thong tin thuc te")
            
            # Update placeholders in both main METS and rep1 METS
            self._update_placeholders_in_mets(mets_path, dirs['root'])
            rep1_mets_path = dirs['rep1'] / "METS.xml"
            if rep1_mets_path.exists():
                self._update_placeholders_in_mets(rep1_mets_path, dirs['root'])
            
        except Exception as e:
            logger.error(f"Loi khi sinh metadata: {e}")
            raise
    
    def build_single_package(self, hoso: HoSo, pdf_root: Path, output_dir: Path) -> BuildSummary:
        """
        Xay dung 1 goi AIP cho 1 ho so
        
        Returns:
            BuildSummary voi thong tin ket qua
        """
        start_time = datetime.now()
        
        # Tao duong dan thu muc cho ho so va ten AIP package
        # Chia lam 2 phan: duong_dan_ho_so + ten_goi_AIP  
        if hasattr(hoso, 'original_folder_path') and hoso.original_folder_path:
            # Duong dan ho so tu folder goc, vi du: "Chi cuc an toan ve sinh thuc pham/hopso01/hoso01"
            folder_path = str(hoso.original_folder_path).replace('\\', '/').replace(':', '_')
            folder_path = folder_path.lstrip('/')
        else:
            # Fallback: dung arc_file_code
            folder_path = hoso.arc_file_code
        
        # Ten goi AIP lay tu OBJID (thay : -> _)
        aip_package_name = hoso.objid.replace(':', '_')
        
        # Ket hop: duong_dan_ho_so / ten_goi_AIP
        package_id = f"{folder_path}/{aip_package_name}"
        
        logger.info(f"Bat dau xay dung package: {package_id}")
        logger.info(f"  - Duong dan ho so: {folder_path}")  
        logger.info(f"  - Ten goi AIP: {aip_package_name}")
        
        summary = BuildSummary()
        summary.total_hoso = 1
        
        try:
            # 1. Tao cau truc thu muc
            dirs = self.create_package_structure(output_dir, package_id)
            
            # 2. Sao chep file PDF
            success_files, error_files = self.copy_pdf_files(hoso, pdf_root, dirs['rep1_data'])
            summary.total_files = success_files + error_files
            
            if success_files == 0:
                raise Exception(f"Khong sao chep duoc file nao cho ho so {hoso.arc_file_code}")
            
            # 3. Sao chep schema files (Enhanced design)
            self.copy_schema_files(dirs['schemas'])
            
            # 4. Sinh metadata XML
            self.generate_metadata_files(hoso, package_id, dirs)
            
            # 5. Tinh toan kich thuoc
            package_size = self._calculate_package_size(dirs['root'])
            summary.total_size_mb = package_size / (1024 * 1024)  # Convert to MB
            
            # 6. Tao file ZIP - Ten file ZIP theo ten goi AIP (OBJID)
            # Vi du: Chi cuc.../hopso01/hoso01/urn_uuid_xxx.zip
            zip_path = self.create_zip_package(dirs['root'])
            
            # 7. Xoa folder AIP neu co tuy chon cleanup
            if self.cleanup_folders:
                try:
                    shutil.rmtree(dirs['root'])
                    logger.info(f"🧹 Da xoa folder AIP: {dirs['root']}")
                except Exception as e:
                    logger.warning(f"⚠️  Khong the xoa folder {dirs['root']}: {e}")
            
            # 8. Danh dau thanh cong
            summary.successful_builds = 1
            summary.failed_builds = 0
            
            end_time = datetime.now()
            summary.build_time_seconds = (end_time - start_time).total_seconds()
            
            logger.info(f"Xay dung thanh cong package {package_id} trong {summary.build_time_seconds:.2f}s")
            logger.info(f"Package size: {summary.total_size_mb:.2f} MB")
            logger.info(f"ZIP file: {zip_path.name}")
            
            return summary
            
        except Exception as e:
            summary.successful_builds = 0
            summary.failed_builds = 1
            summary.errors.append(f"Loi xay dung {package_id}: {str(e)}")
            
            end_time = datetime.now()
            summary.build_time_seconds = (end_time - start_time).total_seconds()
            
            logger.error(f"Loi xay dung package {package_id}: {e}")
            return summary
    
    def build_single_package_dict(self, hoso: HoSo, output_dir: Path, pdf_root: Path) -> Dict[str, Any]:
        """
        Xay dung 1 package va tra ve dict format cho batch processing
        """
        try:
            summary = self.build_single_package(hoso, pdf_root, output_dir)
            
            # Su dung logic giong nhu build_single_package de tao package_id  
            if hasattr(hoso, 'original_folder_path') and hoso.original_folder_path:
                folder_path = str(hoso.original_folder_path).replace('\\', '/').replace(':', '_')
                folder_path = folder_path.lstrip('/')
            else:
                folder_path = hoso.arc_file_code
            
            # Ten goi AIP lay tu OBJID
            aip_package_name = hoso.objid.replace(':', '_')
            package_id = f"{folder_path}/{aip_package_name}"
            
            package_path = output_dir / package_id
            
            return {
                'success': summary.successful_builds > 0,
                'package_id': package_id,
                'package_path': package_path,
                'hoso_id': hoso.arc_file_code,
                'size_mb': summary.total_size_mb,
                'build_time': summary.build_time_seconds,
                'files_processed': summary.total_files,
                'error': summary.errors[0] if summary.errors else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'package_id': None,
                'package_path': None,
                'hoso_id': hoso.arc_file_code,
                'size_mb': 0.0,
                'build_time': 0.0,
                'files_processed': 0,
                'error': str(e)
            }
    
    def build_multiple_packages(self, hoso_list: List[HoSo], pdf_root: Path, output_dir: Path) -> BuildSummary:
        """
        Xay dung nhieu goi AIP
        
        Returns:
            BuildSummary tong hop
        """
        logger.info(f"Bat dau xay dung {len(hoso_list)} packages")
        start_time = datetime.now()
        
        total_summary = BuildSummary()
        total_summary.total_hoso = len(hoso_list)
        
        for i, hoso in enumerate(hoso_list, 1):
            logger.info(f"Xay dung package {i}/{len(hoso_list)}: {hoso.arc_file_code}")
            
            try:
                package_summary = self.build_single_package(hoso, pdf_root, output_dir)
                
                # Cong don ket qua
                total_summary.successful_builds += package_summary.successful_builds
                total_summary.failed_builds += package_summary.failed_builds
                total_summary.total_files += package_summary.total_files
                total_summary.total_size_mb += package_summary.total_size_mb
                total_summary.errors.extend(package_summary.errors)
                
            except Exception as e:
                total_summary.failed_builds += 1
                total_summary.errors.append(f"Loi xay dung ho so {hoso.arc_file_code}: {str(e)}")
                logger.error(f"Loi xay dung ho so {hoso.arc_file_code}: {e}")
        
        end_time = datetime.now()
        total_summary.build_time_seconds = (end_time - start_time).total_seconds()
        
        logger.info(f"Hoan tat xay dung: {total_summary.successful_builds}/{total_summary.total_hoso} thanh cong")
        logger.info(f"Tong thoi gian: {total_summary.build_time_seconds:.2f}s")
        logger.info(f"Tong kich thuoc: {total_summary.total_size_mb:.2f} MB")
        
        return total_summary
    
    def _calculate_package_size(self, package_dir: Path) -> int:
        """Tinh tong kich thuoc package (bytes)"""
        total_size = 0
        
        try:
            for file_path in package_dir.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception as e:
            logger.warning(f"Loi tinh kich thuoc package: {e}")
        
        return total_size

    def copy_schema_files(self, schemas_dir: Path):
        """
        Sao chep cac file XSD schema vao thu muc schemas/
        Theo thiet ke moi, can cac schema: METS, EAD, PREMIS
        """
        logger.info("Sao chep cac file schema XSD")
        
        # Duong dan den thu muc schemas trong project
        project_schemas = Path(__file__).parent / 'schemas'
        
        # Danh sach cac schema can thiet
        required_schemas = ['mets.xsd', 'ead.xsd', 'premis.xsd']
        
        try:
            for schema_file in required_schemas:
                source_path = project_schemas / schema_file
                dest_path = schemas_dir / schema_file
                
                if source_path.exists():
                    dest_path.write_text(source_path.read_text(encoding='utf-8'), encoding='utf-8')
                    logger.debug(f"Sao chep schema: {schema_file}")
                else:
                    # Tao file schema placeholder neu khong co
                    placeholder_content = f'<!-- Placeholder for {schema_file} -->\n<!-- Download from official source -->'
                    dest_path.write_text(placeholder_content, encoding='utf-8')
                    logger.warning(f"Tao placeholder cho schema: {schema_file}")
                    
        except Exception as e:
            logger.error(f"Loi sao chep schema files: {e}")
            raise

    def create_zip_package(self, package_dir: Path) -> Path:
        """
        Tao file ZIP cho AIP package
        
        Args:
            package_dir: Duong dan thu muc package
            
        Returns:
            Path cua file ZIP da tao
        """
        zip_path = package_dir.with_suffix('.zip')
        
        logger.info(f"Tao file ZIP: {zip_path}")
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
                # Duyet tat ca file trong package directory
                for file_path in package_dir.rglob('*'):
                    if file_path.is_file():
                        # Tinh duong dan tuong doi so voi package root
                        arcname = file_path.relative_to(package_dir.parent)
                        zipf.write(file_path, arcname)
                        
            # Tinh kich thuoc file ZIP
            zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
            logger.info(f"Tao thanh cong file ZIP: {zip_path.name} ({zip_size_mb:.2f} MB)")
            
            return zip_path
            
        except Exception as e:
            logger.error(f"Loi tao file ZIP: {e}")
            # Neu loi thi xoa file ZIP khong hoan chinh
            if zip_path.exists():
                zip_path.unlink()
            raise
    
    def _update_placeholders_in_mets(self, mets_path: Path, package_dir: Path):
        """Update placeholders in METS files with actual file info"""
        import re
        
        try:
            mets_content = mets_path.read_text(encoding='utf-8')
            
            # Update PREMIS file info in main METS
            premis_file = package_dir / "metadata" / "preservation" / "PREMIS.xml" 
            if premis_file.exists():
                premis_size = premis_file.stat().st_size
                premis_checksum = self._calculate_checksum(premis_file)
                
                mets_content = mets_content.replace('PLACEHOLDER_PREMIS_SIZE', str(premis_size))
                mets_content = mets_content.replace('PLACEHOLDER_PREMIS_CHECKSUM', premis_checksum)
            
            # Update PREMIS_rep1 file info in rep1 METS
            premis_rep1_file = package_dir / "representations" / "rep1" / "metadata" / "preservation" / "PREMIS_rep1.xml"
            if premis_rep1_file.exists():
                rep1_size = premis_rep1_file.stat().st_size
                rep1_checksum = self._calculate_checksum(premis_rep1_file)
                
                mets_content = mets_content.replace('PLACEHOLDER_PREMIS_REP_SIZE', str(rep1_size))
                mets_content = mets_content.replace('PLACEHOLDER_PREMIS_REP_CHECKSUM', rep1_checksum)
            
            # Update EAD_doc file info 
            ead_descriptive_dir = package_dir / "representations" / "rep1" / "metadata" / "descriptive"
            if ead_descriptive_dir.exists():
                for ead_file in ead_descriptive_dir.glob("EAD_doc_*.xml"):
                    file_id = ead_file.stem.replace("EAD_doc_", "")
                    ead_size = ead_file.stat().st_size
                    ead_checksum = self._calculate_checksum(ead_file)
                    
                    mets_content = mets_content.replace(f'PLACEHOLDER_EAD_DOC_{file_id}_SIZE', str(ead_size))
                    mets_content = mets_content.replace(f'PLACEHOLDER_EAD_DOC_{file_id}_CHECKSUM', ead_checksum)
            
            mets_path.write_text(mets_content, encoding='utf-8')
            logger.debug(f"Updated placeholders in {mets_path}")
            
        except Exception as e:
            logger.warning(f"Error updating placeholders in {mets_path}: {e}")
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum for a file"""
        import hashlib
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            logger.warning(f"Could not calculate checksum for {file_path}: {e}")
            return "0" * 64
