#!/usr/bin/env python3
"""
Script kiểm tra tính đầy đủ của dữ liệu hồ sơ và tài liệu
so với yêu cầu TT 05/2025/TT-BNV

Kiểm tra:
1. Các trường dữ liệu HoSo theo đặc tả 
2. Các trường dữ liệu TaiLieu theo đặc tả
3. Ánh xạ sang EAD.xml 
4. Ánh xạ sang EAD_doc files
5. Ánh xạ sang PREMIS.xml
6. Tính đầy đủ của thông tin trong XML được tạo ra
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import xml.etree.ElementTree as ET
import json
import pandas as pd

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from aip_builder.excel_reader import read_metadata_excel
from aip_builder.models import HoSo, TaiLieu
from aip_builder.config import get_config

class DataCompletenessAnalyzer:
    """Phân tích tính đầy đủ của dữ liệu"""
    
    def __init__(self):
        self.config = get_config()
        
        # Các trường bắt buộc theo TT 05/2025/TT-BNV
        self.required_hoso_fields_spec = {
            # Theo section 4.1 - Sheet HoSo (1 dòng/AIP)
            'OBJID': 'objid',  # UUID format
            'Title': 'tieu_de_ho_so',  # → EAD titleproper
            'RecordStatus': 'che_do_su_dung',  # → EAD maintenance
            'CreatedAt': 'ngay_so_hoa',  # → EAD creation date
            'LastModAt': None,  # Optional
            'DonViHinhThanh': 'ten_co_quan',  # → EAD origination  
            'PhongLuuTru': 'ten_co_quan',  # → EAD repository/fonds
            'MaHoSo': 'ma_ho_so',  # → EAD unitid
            'PhamViThoiGian_BD': 'ngay_bat_dau',  # → EAD unitdate start
            'PhamViThoiGian_KT': 'ngay_ket_thuc',  # → EAD unitdate end
            'SoTo': 'so_to',  # → EAD physdesc/extent
            'DoMat': 'mat_do_thong_tin',  # → EAD mode (security)
            'ThoiHanBaoQuan': 'thoi_han_bao_quan',  # → EAD appraisal
            'NgonNgu': 'ngon_ngu',  # → EAD langmaterial
            'TomTat': 'ghi_chu_ho_so',  # → EAD scopecontent
        }
        
        self.required_tailieu_fields_spec = {
            # Theo section 4.2 - Sheet TaiLieu (1 dòng/tài liệu)
            'FileName': 'duong_dan_file',  # → File reference
            'Title': 'tieu_de_tai_lieu',  # → EAD_doc title
            'NgayTaiLieu': 'ngay_thang_tai_lieu',  # → EAD_doc docDate
            'ThuTu': 'stt',  # → METS structMap ordering
            'MimeType': 'loai_file',  # → METS file@MIMETYPE
            'FileSize': 'kich_thuoc_file',  # → METS file@SIZE, PREMIS size
            'ChecksumSHA256': 'checksum',  # → METS file@CHECKSUM, PREMIS fixity
            'CreatedAt': 'ngay_tao_file',  # → METS file@CREATED
            'PDF_Version': 'phien_ban_dinh_dang',  # → PREMIS format
            'Trang': 'so_trang_tai_lieu',  # → EAD_doc numberOfPage
            'NgonNgu': 'ngon_ngu_tai_lieu',  # → EAD_doc language
            'QuyenTruyCap': None,  # Optional
            'GhiChuKySo': 'ghi_chu_tai_lieu',  # → EAD_doc inforSign
            'NguonSoHoa': 'nguoi_so_hoa',  # → PREMIS creatingApplication
        }
        
        # Các trường EAD.xml section 7.2 - yêu cầu tối thiểu
        self.required_ead_elements = [
            'arcFileCode',  # ← MaHoSo
            'title',  # ← Title  
            'maintenance',  # ← RecordStatus
            'language',  # ← NgonNgu
            'startDate',  # ← PhamViThoiGian_BD
            'endDate',  # ← PhamViThoiGian_KT
            'numberOfPaper',  # ← SoTo
            'format',  # ← định dạng tập hồ sơ
            'confidenceLevel',  # → "Số hóa" (fixed)
            'paperFileCode',  # ← arcFileCode (same value)
            'description',  # ← TomTat
        ]
        
        # Các trường EAD_doc.xml section 10.2 - yêu cầu tối thiểu
        self.required_ead_doc_elements = [
            'docCode',  # ← FileName (no extension)
            'title',  # ← Title
            'docDate',  # ← NgayTaiLieu
            'language',  # ← NgonNgu
            'numberOfPage',  # ← Trang
            'format',  # ← MimeType/PDF level
            'inforSign',  # ← GhiChuKySo
            'description',  # ← mô tả
        ]
        
        # Các trường PREMIS.xml section 8.2 - yêu cầu tối thiểu
        self.required_premis_elements = [
            'objectIdentifier',
            'objectCategory', 
            'compositionLevel',
            'fixity/messageDigest',  # SHA-256
            'size',
            'format/formatName',
            'creatingApplication',  # nếu có
        ]

    def analyze_excel_data(self, excel_path: str) -> Dict[str, Any]:
        """Phân tích dữ liệu từ file Excel"""
        print(f"📖 Phân tích dữ liệu Excel: {excel_path}")
        
        result = {
            'excel_path': excel_path,
            'hoso_analysis': {},
            'tailieu_analysis': {},
            'summary': {}
        }
        
        try:
            # Đọc dữ liệu
            from aip_builder.excel_reader import ExcelReader
            reader = ExcelReader(self.config)
            hoso_list = reader.read_metadata_file(excel_path)
            
            result['summary']['total_hoso'] = len(hoso_list)
            result['summary']['total_tailieu'] = sum(len(hs.tai_lieu) for hs in hoso_list)
            
            print(f"✓ Tìm thấy {len(hoso_list)} hồ sơ với {result['summary']['total_tailieu']} tài liệu")
            
            # Phân tích HoSo
            result['hoso_analysis'] = self._analyze_hoso_data(hoso_list)
            
            # Phân tích TaiLieu  
            result['tailieu_analysis'] = self._analyze_tailieu_data(hoso_list)
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            print(f"❌ Lỗi đọc Excel: {e}")
            return result

    def _analyze_hoso_data(self, hoso_list: List[HoSo]) -> Dict[str, Any]:
        """Phân tích dữ liệu HoSo"""
        analysis = {
            'total_records': len(hoso_list),
            'field_coverage': {},
            'missing_fields': {},
            'completeness_score': 0.0,
            'issues': []
        }
        
        print("\n📊 PHÂN TÍCH DỮ LIỆU HỒ SƠ:")
        
        # Kiểm tra từng trường bắt buộc
        for spec_field, model_field in self.required_hoso_fields_spec.items():
            if model_field is None:
                continue  # Optional field
                
            filled_count = 0
            missing_records = []
            
            for i, hoso in enumerate(hoso_list):
                value = getattr(hoso, model_field, None)
                if value and str(value).strip():
                    filled_count += 1
                else:
                    missing_records.append(f"HoSo-{i+1}")
            
            coverage_pct = (filled_count / len(hoso_list)) * 100
            analysis['field_coverage'][spec_field] = {
                'model_field': model_field,
                'filled_count': filled_count,
                'total_count': len(hoso_list),
                'coverage_percent': coverage_pct,
                'missing_records': missing_records[:5]  # First 5
            }
            
            if coverage_pct < 100:
                analysis['missing_fields'][spec_field] = coverage_pct
                
            print(f"  • {spec_field:20} → {model_field:20}: {filled_count:3}/{len(hoso_list)} ({coverage_pct:5.1f}%)")
            if missing_records:
                print(f"    ❌ Thiếu tại: {', '.join(missing_records[:3])}")

        # Tính điểm hoàn thiện
        total_coverage = sum(info['coverage_percent'] for info in analysis['field_coverage'].values())
        analysis['completeness_score'] = total_coverage / len(analysis['field_coverage'])
        
        # Kiểm tra các vấn đề đặc biệt
        for i, hoso in enumerate(hoso_list):
            # OBJID format
            if not hoso.objid or not hoso.objid.startswith('urn:uuid:'):
                analysis['issues'].append(f"HoSo-{i+1}: OBJID không đúng format UUID")
            
            # Date format
            if hoso.ngay_bat_dau and not self._is_valid_date_format(hoso.ngay_bat_dau):
                analysis['issues'].append(f"HoSo-{i+1}: ngay_bat_dau không đúng format ISO")
                
            # Required for EAD mapping
            if not hoso.arc_file_code:
                analysis['issues'].append(f"HoSo-{i+1}: Thiếu arc_file_code cho EAD mapping")
        
        return analysis

    def _analyze_tailieu_data(self, hoso_list: List[HoSo]) -> Dict[str, Any]:
        """Phân tích dữ liệu TaiLieu"""
        all_tailieu = []
        for hoso in hoso_list:
            all_tailieu.extend(hoso.tai_lieu)
        
        analysis = {
            'total_records': len(all_tailieu),
            'field_coverage': {},
            'missing_fields': {},
            'completeness_score': 0.0,
            'issues': []
        }
        
        if not all_tailieu:
            analysis['issues'].append("Không có tài liệu nào!")
            return analysis
            
        print(f"\n📄 PHÂN TÍCH DỮ LIỆU TÀI LIỆU ({len(all_tailieu)} records):")
        
        # Kiểm tra từng trường bắt buộc
        for spec_field, model_field in self.required_tailieu_fields_spec.items():
            if model_field is None:
                continue  # Optional field
                
            filled_count = 0
            missing_records = []
            
            for i, tailieu in enumerate(all_tailieu):
                value = getattr(tailieu, model_field, None)
                if value and str(value).strip():
                    filled_count += 1
                else:
                    missing_records.append(f"TaiLieu-{i+1}")
            
            coverage_pct = (filled_count / len(all_tailieu)) * 100
            analysis['field_coverage'][spec_field] = {
                'model_field': model_field,
                'filled_count': filled_count,
                'total_count': len(all_tailieu),
                'coverage_percent': coverage_pct,
                'missing_records': missing_records[:5]
            }
            
            if coverage_pct < 100:
                analysis['missing_fields'][spec_field] = coverage_pct
                
            print(f"  • {spec_field:20} → {model_field:20}: {filled_count:3}/{len(all_tailieu)} ({coverage_pct:5.1f}%)")
            if missing_records:
                print(f"    ❌ Thiếu tại: {', '.join(missing_records[:3])}")

        # Tính điểm hoàn thiện
        total_coverage = sum(info['coverage_percent'] for info in analysis['field_coverage'].values())
        analysis['completeness_score'] = total_coverage / len(analysis['field_coverage'])
        
        # Kiểm tra các vấn đề đặc biệt
        for i, tailieu in enumerate(all_tailieu):
            # File ID generation
            if not tailieu.file_id:
                analysis['issues'].append(f"TaiLieu-{i+1}: Thiếu file_id")
                
            # MIME type
            if not tailieu.loai_file or tailieu.loai_file != 'application/pdf':
                analysis['issues'].append(f"TaiLieu-{i+1}: MIME type không phải PDF")
                
            # Checksum format
            if tailieu.checksum and len(tailieu.checksum) != 64:
                analysis['issues'].append(f"TaiLieu-{i+1}: Checksum không đúng format SHA-256")
        
        return analysis

    def analyze_generated_xml(self, package_dir: str) -> Dict[str, Any]:
        """Phân tích XML được tạo ra"""
        package_path = Path(package_dir)
        
        analysis = {
            'package_dir': package_dir,
            'mets_analysis': {},
            'ead_analysis': {},
            'ead_doc_analysis': {},
            'premis_analysis': {},
            'overall_score': 0.0
        }
        
        print(f"\n🔍 PHÂN TÍCH XML ĐƯỢC TẠO RA: {package_dir}")
        
        # Phân tích METS.xml gốc
        mets_path = package_path / 'METS.xml'
        if mets_path.exists():
            analysis['mets_analysis'] = self._analyze_mets_xml(mets_path)
        else:
            analysis['mets_analysis']['error'] = "METS.xml không tồn tại"
        
        # Phân tích EAD.xml
        ead_path = package_path / 'metadata' / 'descriptive' / 'EAD.xml'
        if ead_path.exists():
            analysis['ead_analysis'] = self._analyze_ead_xml(ead_path)
        else:
            analysis['ead_analysis']['error'] = "EAD.xml không tồn tại"
        
        # Phân tích PREMIS.xml
        premis_path = package_path / 'metadata' / 'preservation' / 'PREMIS.xml'
        if premis_path.exists():
            analysis['premis_analysis'] = self._analyze_premis_xml(premis_path)
        else:
            analysis['premis_analysis']['error'] = "PREMIS.xml không tồn tại"
        
        # Phân tích EAD_doc files
        ead_doc_dir = package_path / 'representations' / 'rep1' / 'metadata' / 'descriptive'
        if ead_doc_dir.exists():
            analysis['ead_doc_analysis'] = self._analyze_ead_doc_files(ead_doc_dir)
        else:
            analysis['ead_doc_analysis']['error'] = "EAD_doc directory không tồn tại"
        
        return analysis

    def _analyze_mets_xml(self, mets_path: Path) -> Dict[str, Any]:
        """Phân tích METS.xml"""
        analysis = {'file': str(mets_path), 'elements': {}, 'completeness_score': 0.0}
        
        try:
            tree = ET.parse(mets_path)
            root = tree.getroot()
            
            # Namespace mapping
            ns = {
                'mets': 'http://www.loc.gov/METS/',
                'xlink': 'http://www.w3.org/1999/xlink',
                'csip': 'https://DILCIS.eu/XML/METS/CSIPExtensionMETS'
            }
            
            # Check required elements
            required_checks = {
                'csip:OAISPACKAGETYPE': root.find('.//csip:OAISPACKAGETYPE', ns) is not None,
                'dmdSec': root.find('.//mets:dmdSec', ns) is not None,
                'amdSec': root.find('.//mets:amdSec', ns) is not None,
                'fileSec': root.find('.//mets:fileSec', ns) is not None,
                'structMap_CSIP': root.find('.//mets:structMap[@LABEL="CSIP"]', ns) is not None,
                'mdRef_EAD': len(root.findall('.//mets:mdRef', ns)) > 0,
                'mdRef_PREMIS': len(root.findall('.//mets:mdRef', ns)) > 0,
            }
            
            score = 0
            for check_name, element in required_checks.items():
                exists = element is not None
                analysis['elements'][check_name] = exists
                if exists:
                    score += 1
                print(f"    {'✓' if exists else '❌'} {check_name}")
            
            analysis['completeness_score'] = (score / len(required_checks)) * 100
            
        except Exception as e:
            analysis['error'] = str(e)
        
        return analysis

    def _analyze_ead_xml(self, ead_path: Path) -> Dict[str, Any]:
        """Phân tích EAD.xml"""
        analysis = {'file': str(ead_path), 'elements': {}, 'completeness_score': 0.0}
        
        try:
            tree = ET.parse(ead_path)
            root = tree.getroot()
            
            # Map elements to expected content
            element_checks = {
                'titleproper': root.find('.//titleproper'),
                'unitid': root.find('.//unitid'), 
                'unitdate': root.find('.//unitdate'),
                'physdesc': root.find('.//physdesc'),
                'langmaterial': root.find('.//langmaterial'),
                'scopecontent': root.find('.//scopecontent'),
                'repository': root.find('.//repository'),
            }
            
            score = 0
            for element_name, element in element_checks.items():
                has_content = element is not None and element.text and element.text.strip()
                analysis['elements'][element_name] = {
                    'exists': element is not None,
                    'has_content': has_content,
                    'content': element.text[:100] if has_content else None
                }
                if has_content:
                    score += 1
                print(f"    {'✓' if has_content else '❌'} {element_name}: {element.text[:50] if has_content else 'MISSING'}")
            
            analysis['completeness_score'] = (score / len(element_checks)) * 100
            
        except Exception as e:
            analysis['error'] = str(e)
        
        return analysis

    def _analyze_ead_doc_files(self, ead_doc_dir: Path) -> Dict[str, Any]:
        """Phân tích các file EAD_doc"""
        analysis = {'directory': str(ead_doc_dir), 'files': [], 'completeness_score': 0.0}
        
        try:
            ead_doc_files = list(ead_doc_dir.glob('EAD_doc_*.xml'))
            print(f"    Tìm thấy {len(ead_doc_files)} file EAD_doc")
            
            total_score = 0
            for ead_doc_file in ead_doc_files:
                file_analysis = self._analyze_single_ead_doc(ead_doc_file)
                analysis['files'].append(file_analysis)
                total_score += file_analysis['completeness_score']
            
            if ead_doc_files:
                analysis['completeness_score'] = total_score / len(ead_doc_files)
            
        except Exception as e:
            analysis['error'] = str(e)
        
        return analysis

    def _analyze_single_ead_doc(self, file_path: Path) -> Dict[str, Any]:
        """Phân tích 1 file EAD_doc"""
        analysis = {'file': file_path.name, 'elements': {}, 'completeness_score': 0.0}
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Expected elements trong EAD_doc theo section 10.2
            element_checks = {
                'unittitle': root.find('.//unittitle'),
                'unitid': root.find('.//unitid'),
                'unitdate': root.find('.//unitdate'), 
                'physdesc/extent': root.find('.//physdesc/extent'),
                'langmaterial': root.find('.//langmaterial'),
            }
            
            score = 0
            for element_name, element in element_checks.items():
                has_content = element is not None and element.text and element.text.strip()
                analysis['elements'][element_name] = has_content
                if has_content:
                    score += 1
            
            analysis['completeness_score'] = (score / len(element_checks)) * 100
            
        except Exception as e:
            analysis['error'] = str(e)
        
        return analysis

    def _analyze_premis_xml(self, premis_path: Path) -> Dict[str, Any]:
        """Phân tích PREMIS.xml"""
        analysis = {'file': str(premis_path), 'elements': {}, 'completeness_score': 0.0}
        
        try:
            tree = ET.parse(premis_path)
            root = tree.getroot()
            
            ns = {'premis': 'http://www.loc.gov/premis/v3'}
            
            # Required elements theo section 8.2
            required_checks = {
                'object': root.find('.//premis:object', ns),
                'objectIdentifier': root.find('.//premis:objectIdentifier', ns),
                'objectCategory': root.find('.//premis:objectCategory', ns),
                'fixity': root.find('.//premis:fixity', ns),
                'messageDigest': root.find('.//premis:messageDigest', ns),
                'size': root.find('.//premis:size', ns),
                'format': root.find('.//premis:format', ns),
                'event': root.find('.//premis:event', ns),
                'agent': root.find('.//premis:agent', ns),
            }
            
            score = 0
            for check_name, element in required_checks.items():
                exists = element is not None
                analysis['elements'][check_name] = exists
                if exists:
                    score += 1
                print(f"    {'✓' if exists else '❌'} {check_name}")
            
            analysis['completeness_score'] = (score / len(required_checks)) * 100
            
        except Exception as e:
            analysis['error'] = str(e)
        
        return analysis

    def _is_valid_date_format(self, date_str: str) -> bool:
        """Kiểm tra định dạng ngày ISO"""
        try:
            from datetime import datetime
            # Try ISO formats
            formats = ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S%z']
            for fmt in formats:
                try:
                    datetime.strptime(date_str, fmt)
                    return True
                except:
                    continue
            return False
        except:
            return False

    def generate_report(self, excel_analysis: Dict, xml_analysis: Dict = None) -> str:
        """Tạo báo cáo tổng hợp"""
        report = []
        report.append("=" * 80)
        report.append("📊 BÁO CÁO PHÂN TÍCH TÍNH ĐẦY ĐỦ DỮ LIỆU AIP")
        report.append("=" * 80)
        report.append("")
        
        # Excel Analysis Summary
        report.append("1. PHÂN TÍCH DỮ LIỆU EXCEL:")
        if 'error' in excel_analysis:
            report.append(f"   ❌ Lỗi: {excel_analysis['error']}")
        else:
            summary = excel_analysis['summary']
            report.append(f"   • Tổng hồ sơ: {summary['total_hoso']}")
            report.append(f"   • Tổng tài liệu: {summary['total_tailieu']}")
            
            # HoSo completeness
            hoso_score = excel_analysis['hoso_analysis']['completeness_score']
            report.append(f"   • Độ hoàn thiện HoSo: {hoso_score:.1f}%")
            
            # TaiLieu completeness  
            tailieu_score = excel_analysis['tailieu_analysis']['completeness_score']
            report.append(f"   • Độ hoàn thiện TaiLieu: {tailieu_score:.1f}%")
            
            # Missing fields
            missing_hoso = excel_analysis['hoso_analysis']['missing_fields']
            if missing_hoso:
                report.append(f"   ❌ HoSo thiếu: {', '.join(missing_hoso.keys())}")
            
            missing_tailieu = excel_analysis['tailieu_analysis']['missing_fields'] 
            if missing_tailieu:
                report.append(f"   ❌ TaiLieu thiếu: {', '.join(missing_tailieu.keys())}")
        
        report.append("")
        
        # XML Analysis Summary
        if xml_analysis:
            report.append("2. PHÂN TÍCH XML ĐƯỢC TẠO:")
            
            # METS
            mets = xml_analysis['mets_analysis']
            if 'error' in mets:
                report.append(f"   ❌ METS: {mets['error']}")
            else:
                report.append(f"   • METS: {mets['completeness_score']:.1f}%")
            
            # EAD
            ead = xml_analysis['ead_analysis']
            if 'error' in ead:
                report.append(f"   ❌ EAD: {ead['error']}")
            else:
                report.append(f"   • EAD: {ead['completeness_score']:.1f}%")
            
            # PREMIS
            premis = xml_analysis['premis_analysis']
            if 'error' in premis:
                report.append(f"   ❌ PREMIS: {premis['error']}")
            else:
                report.append(f"   • PREMIS: {premis['completeness_score']:.1f}%")
            
            # EAD_doc
            ead_doc = xml_analysis['ead_doc_analysis']
            if 'error' in ead_doc:
                report.append(f"   ❌ EAD_doc: {ead_doc['error']}")
            else:
                report.append(f"   • EAD_doc: {ead_doc['completeness_score']:.1f}%")
        
        report.append("")
        report.append("3. KHUYẾN NGHỊ:")
        
        # Recommendations based on analysis
        if 'error' not in excel_analysis:
            hoso_score = excel_analysis['hoso_analysis']['completeness_score']
            tailieu_score = excel_analysis['tailieu_analysis']['completeness_score']
            
            if hoso_score < 80:
                report.append("   ⚠️  Cần bổ sung thông tin hồ sơ thiếu trong Excel")
            if tailieu_score < 80:
                report.append("   ⚠️  Cần bổ sung thông tin tài liệu thiếu trong Excel")
            
            issues = excel_analysis['hoso_analysis']['issues'] + excel_analysis['tailieu_analysis']['issues']
            if issues:
                report.append("   🔧 Các vấn đề cần khắc phục:")
                for issue in issues[:10]:  # Top 10 issues
                    report.append(f"      • {issue}")
        
        report.append("")
        report.append("=" * 80)
        
        return '\n'.join(report)


def main():
    """Main function"""
    analyzer = DataCompletenessAnalyzer()
    
    # Analyze Excel data
    excel_path = "data/Input/metadata.xlsx"
    print(f"🔍 PHÂN TÍCH TÍNH ĐẦY ĐỦ DỮ LIỆU - TT 05/2025/TT-BNV")
    print("=" * 60)
    
    excel_analysis = analyzer.analyze_excel_data(excel_path)
    
    # Analyze generated XML if available
    xml_analysis = None
    output_dir = Path("data/output")
    if output_dir.exists():
        # Find first generated package
        package_dirs = [d for d in output_dir.iterdir() if d.is_dir() and d.name.startswith('urn_uuid')]
        if package_dirs:
            package_dir = package_dirs[0]  # Take first one
            xml_analysis = analyzer.analyze_generated_xml(str(package_dir))
    
    # Generate report
    report = analyzer.generate_report(excel_analysis, xml_analysis)
    print(report)
    
    # Save report to file
    report_file = "data_completeness_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n💾 Báo cáo đã lưu: {report_file}")


if __name__ == "__main__":
    main()
