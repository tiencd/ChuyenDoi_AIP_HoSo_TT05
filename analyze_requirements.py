#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BÁO CÁO KIỂM TRA YÊU CẦU SO VỚI HIỆN TRẠNG
Phân tích các nội dung chưa đúng hoặc thiếu sót theo TT 05/2025/TT-BNV
"""

import os
import xml.etree.ElementTree as ET

def analyze_package_structure():
    """Phân tích cấu trúc package so với yêu cầu"""
    output_dir = "data/output"
    
    print("🔍 BÁO CÁO KIỂM TRA YÊU CẦU AIP_HOSO")
    print("=" * 70)
    print()
    
    # Get newest package
    packages = []
    for item in os.listdir(output_dir):
        if item.startswith('urn_uuid_') and os.path.isdir(os.path.join(output_dir, item)):
            packages.append(item)
    
    if not packages:
        print("❌ Không tìm thấy package nào để kiểm tra")
        return
    
    packages.sort(key=lambda x: os.path.getmtime(os.path.join(output_dir, x)))
    latest_package = packages[-1]
    package_path = os.path.join(output_dir, latest_package)
    
    print(f"📦 Kiểm tra package: {latest_package}")
    print()
    
    issues = []
    recommendations = []
    
    # 1. Kiểm tra cấu trúc thư mục
    print("1. KIỂM TRA CẤU TRÚC THỦ MỤC:")
    required_structure = {
        'METS.xml': '✓ METS gốc',
        'metadata/descriptive/ead.xml': '✓ EAD tổng thể',
        'metadata/preservation/premis.xml': '✓ PREMIS',
        'representations/rep1/METS.xml': '✓ METS rep1',
        'representations/rep1/data/': '✓ PDF files',
        'representations/rep1/metadata/descriptive/': '✓ EAD_doc files',
        'schemas/': '✓ XSD files'
    }
    
    for path, desc in required_structure.items():
        full_path = os.path.join(package_path, path.replace('/', os.sep))
        if os.path.exists(full_path):
            print(f"   ✅ {desc}: {path}")
        else:
            print(f"   ❌ {desc}: {path}")
            issues.append(f"Thiếu {path}")
    
    print()
    
    # 2. Kiểm tra METS.xml gốc
    print("2. KIỂM TRA METS.XML GỐC:")
    mets_path = os.path.join(package_path, 'METS.xml')
    if os.path.exists(mets_path):
        try:
            tree = ET.parse(mets_path)
            root = tree.getroot()
            
            # Kiểm tra namespaces
            expected_ns = {
                'mets': 'http://www.loc.gov/METS/',
                'xlink': 'http://www.w3.org/1999/xlink',
                'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                'csip': 'https://DILCIS.eu/XML/METS/CSIPExtensionMETS'
            }
            
            print("   Namespaces:")
            for prefix, uri in expected_ns.items():
                if f"{{{uri}}}" in str(ET.tostring(root)):
                    print(f"   ✅ {prefix}: {uri}")
                else:
                    print(f"   ❌ {prefix}: {uri}")
                    if prefix == 'csip':
                        issues.append("Thiếu namespace csip (bắt buộc cho CSIP 1.2)")
            
            # Kiểm tra csip:OAISPACKAGETYPE
            oais_type = root.find('.//csip:OAISPACKAGETYPE', {'csip': expected_ns['csip']})
            if oais_type is not None and oais_type.text == 'AIP':
                print("   ✅ csip:OAISPACKAGETYPE = AIP")
            else:
                print("   ❌ csip:OAISPACKAGETYPE = AIP")
                issues.append("Thiếu hoặc sai csip:OAISPACKAGETYPE=AIP (bắt buộc)")
            
            # Kiểm tra OBJID format
            objid = root.get('OBJID', '')
            if objid.startswith('urn:uuid:') and len(objid.split(':')) == 3:
                print(f"   ✅ OBJID format: {objid}")
            else:
                print(f"   ❌ OBJID format: {objid}")
                issues.append("OBJID phải có format urn:uuid:<uuid>")
            
            # Kiểm tra CREATEDATE có múi giờ +07:00
            createdate = root.find('.//mets:metsHdr', {'mets': expected_ns['mets']})
            if createdate is not None:
                cd_attr = createdate.get('CREATEDATE', '')
                if '+07:00' in cd_attr or cd_attr.endswith('+07:00'):
                    print("   ✅ CREATEDATE có múi giờ +07:00")
                else:
                    print(f"   ❌ CREATEDATE: {cd_attr}")
                    issues.append("CREATEDATE phải có múi giờ +07:00 (ISO 8601)")
            
        except ET.ParseError as e:
            print(f"   ❌ METS.xml không hợp lệ: {e}")
            issues.append("METS.xml có lỗi XML syntax")
    
    print()
    
    # 3. Kiểm tra mdRef attributes
    print("3. KIỂM TRA THUỘC TÍNH MDREF:")
    if os.path.exists(mets_path):
        try:
            tree = ET.parse(mets_path)
            root = tree.getroot()
            
            mdRefs = root.findall('.//mets:mdRef', {'mets': 'http://www.loc.gov/METS/'})
            
            required_attrs = ['ID', 'LOCTYPE', 'MDTYPE', 'MIMETYPE', 'CHECKSUMTYPE']
            recommended_attrs = ['SIZE', 'CREATED', 'CHECKSUM']
            
            for i, mdRef in enumerate(mdRefs, 1):
                print(f"   mdRef {i}:")
                for attr in required_attrs:
                    if mdRef.get(attr):
                        print(f"     ✅ {attr}: {mdRef.get(attr)}")
                    else:
                        print(f"     ❌ {attr}: Thiếu")
                        issues.append(f"mdRef thiếu thuộc tính bắt buộc {attr}")
                
                # Kiểm tra CHECKSUMTYPE = SHA-256
                if mdRef.get('CHECKSUMTYPE') != 'SHA-256':
                    print(f"     ❌ CHECKSUMTYPE phải là SHA-256")
                    issues.append("CHECKSUMTYPE phải là SHA-256")
                
                # Kiểm tra xlink:type và xlink:href
                if mdRef.get('{http://www.w3.org/1999/xlink}type') != 'simple':
                    print(f"     ❌ xlink:type phải là 'simple'")
                    issues.append("xlink:type phải là 'simple'")
                
                href = mdRef.get('HREF') or mdRef.get('{http://www.w3.org/1999/xlink}href')
                if href:
                    print(f"     ✅ xlink:href: {href}")
                else:
                    print(f"     ❌ xlink:href: Thiếu")
                    issues.append("mdRef thiếu xlink:href")
        except:
            pass
    
    print()
    
    # 4. Kiểm tra structMap CSIP
    print("4. KIỂM TRA STRUCTMAP CSIP:")
    if os.path.exists(mets_path):
        try:
            tree = ET.parse(mets_path)
            root = tree.getroot()
            
            structMap = root.find('.//mets:structMap[@LABEL="CSIP"]', {'mets': 'http://www.loc.gov/METS/'})
            if structMap is not None:
                print("   ✅ structMap với LABEL='CSIP'")
                
                # Kiểm tra các div bắt buộc
                required_divs = ['Metadata', 'Schemas', 'Representations/rep1']
                for div_label in required_divs:
                    div_elem = root.find(f'.//mets:div[@LABEL="{div_label}"]', {'mets': 'http://www.loc.gov/METS/'})
                    if div_elem is not None:
                        print(f"   ✅ div[@LABEL='{div_label}']")
                        
                        # Kiểm tra Metadata div có DMDID và ADMID
                        if div_label == 'Metadata':
                            if div_elem.get('DMDID'):
                                print("     ✅ DMDID có giá trị")
                            else:
                                print("     ❌ DMDID thiếu")
                                issues.append("div[@LABEL='Metadata'] thiếu DMDID")
                            
                            if div_elem.get('ADMID'):
                                print("     ✅ ADMID có giá trị") 
                            else:
                                print("     ❌ ADMID thiếu")
                                issues.append("div[@LABEL='Metadata'] thiếu ADMID")
                    else:
                        print(f"   ❌ div[@LABEL='{div_label}']")
                        issues.append(f"Thiếu div[@LABEL='{div_label}'] trong structMap")
            else:
                print("   ❌ structMap với LABEL='CSIP'")
                issues.append("Thiếu structMap[@LABEL='CSIP']")
        except:
            pass
    
    print()
    
    # 5. Kiểm tra rep1/METS.xml
    print("5. KIỂM TRA REP1/METS.XML:")
    rep1_mets = os.path.join(package_path, 'representations', 'rep1', 'METS.xml')
    if os.path.exists(rep1_mets):
        try:
            tree = ET.parse(rep1_mets)
            root = tree.getroot()
            
            # Kiểm tra csip:OAISPACKAGETYPE
            oais_type = root.find('.//csip:OAISPACKAGETYPE', {'csip': 'https://DILCIS.eu/XML/METS/CSIPExtensionMETS'})
            if oais_type is not None and oais_type.text == 'AIP':
                print("   ✅ csip:OAISPACKAGETYPE = AIP")
            else:
                print("   ❌ csip:OAISPACKAGETYPE = AIP")
                issues.append("rep1/METS.xml thiếu csip:OAISPACKAGETYPE=AIP")
            
            # Kiểm tra structMap có các div bắt buộc
            required_rep1_divs = ['Data', 'MetadataLink']
            for div_label in required_rep1_divs:
                div_elem = root.find(f'.//mets:div[@LABEL="{div_label}"]', {'mets': 'http://www.loc.gov/METS/'})
                if div_elem is not None:
                    print(f"   ✅ div[@LABEL='{div_label}']")
                else:
                    print(f"   ❌ div[@LABEL='{div_label}']")
                    issues.append(f"rep1/METS.xml thiếu div[@LABEL='{div_label}']")
            
            # Kiểm tra MetadataLink/File có UUID format và DMDID
            metalink_files = root.findall('.//mets:div[@LABEL="MetadataLink/File"]', {'mets': 'http://www.loc.gov/METS/'})
            print(f"   Tìm thấy {len(metalink_files)} MetadataLink/File")
            for i, ml_file in enumerate(metalink_files, 1):
                file_id = ml_file.get('ID', '')
                if file_id.startswith('uuid-') and len(file_id) > 10:
                    print(f"     ✅ File {i} ID format: {file_id}")
                else:
                    print(f"     ❌ File {i} ID format: {file_id}")
                    issues.append(f"MetadataLink/File {i} ID phải theo format uuid-{{UUIDS}}")
                
                if ml_file.get('DMDID'):
                    print(f"     ✅ File {i} có DMDID")
                else:
                    print(f"     ❌ File {i} thiếu DMDID")
                    issues.append(f"MetadataLink/File {i} thiếu DMDID")
            
        except ET.ParseError as e:
            print(f"   ❌ rep1/METS.xml không hợp lệ: {e}")
            issues.append("rep1/METS.xml có lỗi XML syntax")
    else:
        print("   ❌ rep1/METS.xml không tồn tại")
        issues.append("Thiếu rep1/METS.xml")
    
    print()
    
    # 6. Kiểm tra EAD_doc files
    print("6. KIỂM TRA EAD_DOC FILES:")
    ead_doc_path = os.path.join(package_path, 'representations', 'rep1', 'metadata', 'descriptive')
    if os.path.exists(ead_doc_path):
        ead_files = [f for f in os.listdir(ead_doc_path) if f.startswith('EAD_doc_')]
        print(f"   Tìm thấy {len(ead_files)} EAD_doc files")
        
        # Kiểm tra đặt tên file
        for ead_file in ead_files[:3]:  # Chỉ kiểm tra 3 file đầu
            if ead_file.startswith('EAD_doc_file-') and ead_file.endswith('.xml'):
                print(f"   ✅ Format tên file: {ead_file}")
            else:
                print(f"   ❌ Format tên file: {ead_file}")
                issues.append(f"EAD_doc file {ead_file} không đúng format EAD_doc_file-N.xml")
    else:
        print("   ❌ Không tìm thấy thư mục EAD_doc")
        issues.append("Thiếu thư mục representations/rep1/metadata/descriptive/")
    
    print()
    
    # 7. Tổng kết
    print("=" * 70)
    print("📊 TỔNG KẾT KIỂM TRA:")
    print()
    
    if not issues:
        print("🎉 HOÀN HẢO! Không có vấn đề nào được phát hiện.")
    else:
        print(f"❌ Phát hiện {len(issues)} vấn đề cần khắc phục:")
        print()
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
    
    print()
    
    # 8. Khuyến nghị
    print("💡 KHUYẾN NGHỊ KHẮC PHỤC:")
    print()
    
    priority_fixes = [
        "1. Bổ sung csip:OAISPACKAGETYPE=AIP cho cả METS gốc và rep1/METS.xml",
        "2. Đảm bảo tất cả mdRef có đầy đủ thuộc tính bắt buộc (ID, LOCTYPE, MDTYPE, MIMETYPE, CHECKSUMTYPE, xlink:type, xlink:href)",
        "3. Sử dụng CHECKSUMTYPE='SHA-256' thống nhất thay vì MD5", 
        "4. Thêm múi giờ +07:00 vào tất cả timestamps",
        "5. Đảm bảo structMap có đúng cấu trúc CSIP với các div bắt buộc",
        "6. rep1/METS.xml phải có div MetadataLink với ID format uuid-{UUIDS}"
    ]
    
    for fix in priority_fixes:
        print(f"   {fix}")
    
    print()
    print("=" * 70)

if __name__ == "__main__":
    analyze_package_structure()
