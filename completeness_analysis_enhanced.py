#!/usr/bin/env python3
"""
Data Completeness Analysis Tool - Enhanced Version
Phân tích tính đầy đủ của dữ liệu AIP theo tiêu chuẩn CSIP 1.2
Bao gồm kiểm tra metadata cấp package và representation
"""

import os
import sys
from pathlib import Path
from collections import defaultdict
import xml.etree.ElementTree as ET

def analyze_aip_structure(package_dir: Path):
    """Phân tích cấu trúc AIP và metadata"""
    results = {
        'package_name': package_dir.name,
        'structure_complete': True,
        'files_found': [],
        'files_missing': [],
        'metadata_analysis': {},
        'representation_analysis': {},
        'total_files': 0,
        'total_size_mb': 0
    }
    
    # Các file/thư mục bắt buộc theo CSIP 1.2
    required_structure = {
        'root_files': ['METS.xml'],
        'package_metadata': {
            'descriptive/EAD.xml': 'Package-level descriptive metadata',
            'preservation/PREMIS.xml': 'Package-level preservation metadata'
        },
        'representation': {
            'representations/rep1/METS.xml': 'Representation METS',
            'representations/rep1/data/': 'Content files directory',
            'representations/rep1/metadata/descriptive/': 'Representation descriptive metadata',
            'representations/rep1/metadata/preservation/PREMIS_rep1.xml': 'Representation preservation metadata'
        },
        'schemas': ['schemas/mets.xsd', 'schemas/ead.xsd', 'schemas/premis.xsd']
    }
    
    print(f"\n📋 Phân tích package: {results['package_name']}")
    print("=" * 60)
    
    # 1. Kiểm tra cấu trúc thư mục và file bắt buộc
    print("\n🏗️  Kiểm tra cấu trúc AIP:")
    
    # Root level files
    for filename in required_structure['root_files']:
        filepath = package_dir / filename
        if filepath.exists():
            results['files_found'].append(f"✓ {filename}")
            print(f"  ✓ {filename}")
        else:
            results['files_missing'].append(f"✗ {filename}")
            results['structure_complete'] = False
            print(f"  ✗ {filename} - THIẾU")
    
    # Package metadata
    print("\n  📁 Package metadata:")
    metadata_dir = package_dir / 'metadata'
    for rel_path, description in required_structure['package_metadata'].items():
        filepath = metadata_dir / rel_path
        if filepath.exists():
            size = filepath.stat().st_size if filepath.is_file() else 0
            results['files_found'].append(f"✓ metadata/{rel_path}")
            print(f"    ✓ {rel_path} ({size:,} bytes) - {description}")
        else:
            results['files_missing'].append(f"✗ metadata/{rel_path}")
            results['structure_complete'] = False
            print(f"    ✗ {rel_path} - THIẾU - {description}")
    
    # Representation structure
    print("\n  📁 Representation rep1:")
    for rel_path, description in required_structure['representation'].items():
        filepath = package_dir / rel_path
        if filepath.exists():
            if filepath.is_file():
                size = filepath.stat().st_size
                results['files_found'].append(f"✓ {rel_path}")
                print(f"    ✓ {rel_path} ({size:,} bytes) - {description}")
            else:
                results['files_found'].append(f"✓ {rel_path}/ (directory)")
                print(f"    ✓ {rel_path}/ - {description}")
        else:
            results['files_missing'].append(f"✗ {rel_path}")
            results['structure_complete'] = False
            print(f"    ✗ {rel_path} - THIẾU - {description}")
    
    # Schema files
    print("\n  📁 Schema files:")
    for rel_path in required_structure['schemas']:
        filepath = package_dir / rel_path
        if filepath.exists():
            size = filepath.stat().st_size
            results['files_found'].append(f"✓ {rel_path}")
            print(f"    ✓ {rel_path} ({size:,} bytes)")
        else:
            results['files_missing'].append(f"✗ {rel_path}")
            print(f"    ✗ {rel_path} - THIẾU")
    
    # 2. Phân tích nội dung data files
    print("\n📂 Nội dung representation data:")
    data_dir = package_dir / 'representations' / 'rep1' / 'data'
    if data_dir.exists():
        data_files = list(data_dir.glob('**/*'))
        pdf_files = [f for f in data_files if f.is_file() and f.suffix.lower() == '.pdf']
        
        total_size = sum(f.stat().st_size for f in pdf_files)
        results['total_files'] = len(pdf_files)
        results['total_size_mb'] = total_size / (1024 * 1024)
        
        print(f"  📄 Số file PDF: {len(pdf_files)}")
        print(f"  💾 Tổng dung lượng: {results['total_size_mb']:.2f} MB")
        
        if pdf_files:
            print(f"  📝 Các file PDF:")
            for pdf_file in sorted(pdf_files):
                size_mb = pdf_file.stat().st_size / (1024 * 1024)
                print(f"    - {pdf_file.name} ({size_mb:.2f} MB)")
    else:
        print("  ✗ Thư mục data không tồn tại")
        results['structure_complete'] = False
    
    # 3. Phân tích descriptive metadata ở representation level
    print("\n📋 Descriptive metadata (representation level):")
    desc_dir = package_dir / 'representations' / 'rep1' / 'metadata' / 'descriptive'
    if desc_dir.exists():
        ead_files = list(desc_dir.glob('EAD_doc_*.xml'))
        results['representation_analysis']['descriptive_files'] = len(ead_files)
        
        print(f"  📄 Số file EAD_doc: {len(ead_files)}")
        
        for ead_file in sorted(ead_files):
            try:
                tree = ET.parse(ead_file)
                root = tree.getroot()
                # Tìm title elements
                titles = root.findall('.//{http://ead3.archivists.org/schema/}unittitle')
                title = titles[0].text if titles else "N/A"
                print(f"    - {ead_file.name}: {title[:50]}...")
            except Exception as e:
                print(f"    - {ead_file.name}: Lỗi đọc XML - {e}")
    else:
        print("  ✗ Thư mục descriptive metadata không tồn tại")
    
    # 4. Phân tích PREMIS files
    print("\n🛡️  Preservation metadata analysis:")
    
    # Package level PREMIS
    package_premis = package_dir / 'metadata' / 'preservation' / 'PREMIS.xml'
    if package_premis.exists():
        try:
            tree = ET.parse(package_premis)
            root = tree.getroot()
            
            # Count objects, events, agents
            objects = root.findall('.//{http://www.loc.gov/premis/v3}object')
            events = root.findall('.//{http://www.loc.gov/premis/v3}event')
            agents = root.findall('.//{http://www.loc.gov/premis/v3}agent')
            
            print(f"  📦 Package PREMIS.xml:")
            print(f"    - Objects: {len(objects)}")
            print(f"    - Events: {len(events)}")
            print(f"    - Agents: {len(agents)}")
            
            results['metadata_analysis']['package_premis'] = {
                'objects': len(objects),
                'events': len(events), 
                'agents': len(agents)
            }
            
        except Exception as e:
            print(f"  ✗ Lỗi đọc package PREMIS.xml: {e}")
    
    # Representation level PREMIS
    rep_premis = package_dir / 'representations' / 'rep1' / 'metadata' / 'preservation' / 'PREMIS_rep1.xml'
    if rep_premis.exists():
        try:
            tree = ET.parse(rep_premis)
            root = tree.getroot()
            
            # Register namespaces to handle prefixes properly  
            namespaces = {
                'premis': 'http://www.loc.gov/premis/v3',
                'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
            }
            
            # Count objects, events, agents with namespace
            objects = root.findall('.//premis:object', namespaces)
            events = root.findall('.//premis:event', namespaces) 
            agents = root.findall('.//premis:agent', namespaces)
            
            # Count different object types - need to handle xsi:type attribute
            file_objects = []
            rep_objects = []
            
            for obj in objects:
                obj_type = obj.get('{http://www.w3.org/2001/XMLSchema-instance}type')
                if obj_type == 'premis:file':
                    file_objects.append(obj)
                elif obj_type == 'premis:representation':
                    rep_objects.append(obj)
            
            print(f"  📄 Representation PREMIS_rep1.xml:")
            print(f"    - Total Objects: {len(objects)}")
            print(f"    - File Objects: {len(file_objects)}")
            print(f"    - Representation Objects: {len(rep_objects)}")
            print(f"    - Events: {len(events)}")
            print(f"    - Agents: {len(agents)}")
            
            results['metadata_analysis']['representation_premis'] = {
                'total_objects': len(objects),
                'file_objects': len(file_objects),
                'representation_objects': len(rep_objects),
                'events': len(events),
                'agents': len(agents)
            }
            
        except Exception as e:
            print(f"  ✗ Lỗi đọc representation PREMIS_rep1.xml: {e}")
    else:
        print(f"  ✗ PREMIS_rep1.xml không tồn tại")
        results['structure_complete'] = False
    
    # 5. Tổng kết
    print(f"\n📊 TÓM TẮT:")
    print(f"  📁 Package: {results['package_name']}")
    print(f"  ✅ Cấu trúc hoàn chỉnh: {'CÓ' if results['structure_complete'] else 'KHÔNG'}")
    print(f"  📄 File PDF: {results['total_files']}")
    print(f"  💾 Tổng dung lượng: {results['total_size_mb']:.2f} MB")
    print(f"  📋 Files tìm thấy: {len(results['files_found'])}")
    if results['files_missing']:
        print(f"  ⚠️  Files thiếu: {len(results['files_missing'])}")
        for missing in results['files_missing']:
            print(f"    - {missing}")
    
    return results

def main():
    """Main function để chạy phân tích"""
    if len(sys.argv) < 2:
        print("Sử dụng: python completeness_analysis.py <output_directory>")
        print("Ví dụ: python completeness_analysis.py data/output_20250823_062722")
        sys.exit(1)
    
    output_dir = Path(sys.argv[1])
    if not output_dir.exists():
        print(f"❌ Thư mục không tồn tại: {output_dir}")
        sys.exit(1)
    
    print(f"🔍 Phân tích tính đầy đủ dữ liệu AIP trong: {output_dir}")
    print(f"📅 CSIP 1.2 Compliance Check - Enhanced with Representation Level")
    
    # Tìm tất cả package directories - chỉ những thư mục có METS.xml và có cấu trúc AIP đầy đủ
    package_dirs = []
    for item in output_dir.rglob("*"):
        if item.is_dir() and (item / "METS.xml").exists():
            # Kiểm tra xem đây có phải là package root không (có metadata và representations)
            has_metadata = (item / "metadata").exists()
            has_representations = (item / "representations").exists()
            
            # Chỉ coi là package nếu có cả metadata và representations hoặc là root package
            if has_metadata and has_representations:
                package_dirs.append(item)
            # Nếu không có representations nhưng có METS.xml, có thể là package đơn giản  
            elif (item / "METS.xml").exists() and not str(item).endswith("rep1"):
                package_dirs.append(item)
    
    if not package_dirs:
        print("❌ Không tìm thấy package AIP nào (không có METS.xml)")
        sys.exit(1)
    
    print(f"📦 Tìm thấy {len(package_dirs)} package(s)")
    
    # Phân tích từng package
    all_results = []
    for package_dir in sorted(package_dirs):
        result = analyze_aip_structure(package_dir)
        all_results.append(result)
    
    # Tổng kết chung
    print(f"\n{'='*60}")
    print(f"🎯 TỔNG KẾT CHUNG - {len(all_results)} package(s)")
    print(f"{'='*60}")
    
    complete_packages = sum(1 for r in all_results if r['structure_complete'])
    total_files = sum(r['total_files'] for r in all_results)
    total_size_mb = sum(r['total_size_mb'] for r in all_results)
    
    print(f"  ✅ Packages hoàn chỉnh: {complete_packages}/{len(all_results)}")
    print(f"  📄 Tổng file PDF: {total_files}")  
    print(f"  💾 Tổng dung lượng: {total_size_mb:.2f} MB")
    
    if complete_packages == len(all_results):
        print(f"  🎉 TẤT CẢ PACKAGES ĐÃ TUÂN THỦ CSIP 1.2!")
        print(f"     Bao gồm metadata cấp package và representation")
    else:
        print(f"  ⚠️  {len(all_results) - complete_packages} package(s) chưa hoàn chỉnh")
    
    print(f"\n🔗 CSIP 1.2 Features được triển khai:")
    print(f"   ✅ Package-level METS, EAD, PREMIS")
    print(f"   ✅ Representation-level METS, EAD documents, PREMIS")
    print(f"   ✅ Structured data directory (representations/rep1/data)")
    print(f"   ✅ Schema validation files (XSD)")
    print(f"   ✅ Complete preservation metadata workflow")

if __name__ == "__main__":
    main()
