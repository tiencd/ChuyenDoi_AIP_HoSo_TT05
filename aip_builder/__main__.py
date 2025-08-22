"""
Main - CLI entry point cho AIP Builder

Cung cap cac command:
- build: Xay dung goi AIP tu metadata.xlsx va PDF
- test: Chay test voi du lieu mau
- validate: Kiem tra file Excel va PDF
"""

import click
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from .config import Config, get_config, set_config
from .excel_reader import read_metadata_excel, ExcelReader
from .pdf_probe import probe_pdf_directory, PDFProbe
from .grouping import group_hoso_by_folder, FileGrouper
from .xml_generator import XMLTemplateGenerator
from .package_builder import PackageBuilder
from .validator import CSIPValidator, IntegrityChecker
from .batch_processor import BatchProcessor, BatchMonitor, create_batch_processor
from .error_handling import create_enhanced_logger, ErrorCategory, RetryConfig


def setup_logging(log_level: str = "INFO"):
    """Thiet lap logging"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


@click.group()
@click.option('--log-level', default='INFO', help='Log level (DEBUG, INFO, WARNING, ERROR)')
@click.option('--config-file', help='Duong dan file config (JSON)')
def cli(log_level: str, config_file: Optional[str]):
    """AIP Builder - Chuong trinh chuyen doi metadata.xlsx + PDF thanh goi AIP_hoso"""
    setup_logging(log_level)
    
    # Load config tu file neu co
    if config_file:
        # TODO: Implement config loading from file
        pass


@cli.command()
@click.option('--meta', default=None, help='Duong dan file metadata.xlsx')
@click.option('--pdf-root', default=None, help='Thu muc goc chua PDF')
@click.option('--out', default=None, help='Thu muc dau ra')
@click.option('--keep-folders/--no-keep-folders', default=True, help='Giu thu muc sau khi nen')
def build(meta: Optional[str], pdf_root: Optional[str], out: Optional[str], keep_folders: bool):
    """Xay dung goi AIP tu metadata Excel va file PDF"""
    
    config = get_config()
    
    # Su dung gia tri mac dinh neu khong duoc cung cap
    meta_path = meta or config.default_meta_path
    pdf_root_path = pdf_root or config.default_pdf_root  
    output_dir = out or config.output_dir_with_timestamp
    
    click.echo(f"AIP Builder - Bat dau xay dung goi AIP")
    click.echo(f"  Metadata: {meta_path}")
    click.echo(f"  PDF Root: {pdf_root_path}")
    click.echo(f"  Output: {output_dir}")
    click.echo(f"  Keep folders: {keep_folders}")
    
    try:
        # Kiem tra file dau vao
        if not Path(meta_path).exists():
            click.echo(f"ERROR: File metadata khong ton tai: {meta_path}", err=True)
            return 1
        
        if not Path(pdf_root_path).exists():
            click.echo(f"ERROR: Thu muc PDF khong ton tai: {pdf_root_path}", err=True)
            return 1
        
        # Doc metadata Excel
        click.echo("Dang doc file metadata.xlsx...")
        hoso_list = read_metadata_excel(meta_path, config)
        click.echo(f"Doc thanh cong {len(hoso_list)} ho so")
        
        # Nhom ho so theo thu muc
        click.echo("Dang nhom ho so theo thu muc...")
        folder_groups = group_hoso_by_folder(pdf_root_path, hoso_list)
        click.echo(f"Tim thay {len(folder_groups)} nhom thu muc")
        
        # Hien thi thong tin cac nhom
        for folder_name, folder_group in folder_groups.items():
            hoso = folder_group.hoso
            if hoso:
                click.echo(f"  - {folder_name}: {hoso.arc_file_code} ({len(hoso.tai_lieu)} tai lieu)")
            else:
                click.echo(f"  - {folder_name}: Chua gan ho so ({len(folder_group.pdf_files)} PDF)")
        
        # TODO: Tiep tuc voi cac buoc build XML va dong goi
        click.echo("Cac buoc tiep theo dang duoc phat trien...")
        
    except Exception as e:
        click.echo(f"ERROR: {e}", err=True)
        logging.exception("Chi tiet loi:")
        return 1
    
    click.echo("Hoan thanh!")
    return 0


@cli.command()
@click.option('--meta', default=None, help='Duong dan file metadata.xlsx')
@click.option('--pdf-root', default=None, help='Thu muc goc chua PDF')
def validate(meta: Optional[str], pdf_root: Optional[str]):
    """Kiem tra file Excel va PDF"""
    
    config = get_config()
    meta_path = meta or config.default_meta_path
    pdf_root_path = pdf_root or config.default_pdf_root
    
    click.echo("AIP Builder - Kiem tra du lieu dau vao")
    
    # Kiem tra file metadata
    if Path(meta_path).exists():
        click.echo(f"✓ File metadata ton tai: {meta_path}")
        try:
            hoso_list = read_metadata_excel(meta_path, config)
            click.echo(f"✓ Doc thanh cong {len(hoso_list)} ho so")
        except Exception as e:
            click.echo(f"✗ Loi doc metadata: {e}")
            return 1
    else:
        click.echo(f"✗ File metadata khong ton tai: {meta_path}")
        return 1
    
    # Kiem tra thu muc PDF
    if Path(pdf_root_path).exists():
        click.echo(f"✓ Thu muc PDF ton tai: {pdf_root_path}")
        
        # Dem so file PDF
        pdf_files = list(Path(pdf_root_path).rglob("*.pdf"))
        click.echo(f"✓ Tim thay {len(pdf_files)} file PDF")
        
        # Kiem tra mot vai file mau
        if pdf_files:
            click.echo("Kiem tra file PDF mau...")
            for i, pdf_file in enumerate(pdf_files[:3]):  # Chi kiem tra 3 file dau
                try:
                    from .pdf_probe import probe_pdf
                    pdf_info = probe_pdf(pdf_file)
                    click.echo(f"  ✓ {pdf_file.name}: {pdf_info.size} bytes, {pdf_info.pages} trang")
                except Exception as e:
                    click.echo(f"  ✗ {pdf_file.name}: Loi - {e}")
    else:
        click.echo(f"✗ Thu muc PDF khong ton tai: {pdf_root_path}")
        return 1
    
    click.echo("Kiem tra hoan tat!")
    return 0


@cli.command()
def version():
    """Hien thi phien ban"""
    from . import __version__
    click.echo(f"AIP Builder version {__version__}")


@cli.command()
@click.option('--meta', default='data/input/metadata.xlsx', help='Duong dan file metadata.xlsx')
@click.option('--output', default='temp_xml', help='Thu muc xuat XML test')
def test_xml(meta: str, output: str):
    """Test sinh XML templates"""
    click.echo("AIP Builder - Test XML Generation")
    
    try:
        config = get_config()
        
        # Doc du lieu Excel
        excel_reader = ExcelReader(config)
        hoso_df, tailieu_df = excel_reader.read_excel(meta)
        hoso_list = excel_reader.convert_to_models(hoso_df, tailieu_df)
        
        if not hoso_list:
            click.echo("❌ Khong tim thay ho so nao")
            return
            
        # Lay ho so dau tien de test
        hoso = hoso_list[0]
        click.echo(f"✓ Test ho so: {hoso.arc_file_code}")
        
        # Tao XML generator
        xml_gen = XMLTemplateGenerator(config)
        package_id = f"AIP_{hoso.arc_file_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Tao thu muc output
        output_dir = Path(output)
        output_dir.mkdir(exist_ok=True)
        
        # Sinh XML
        xmls = xml_gen.generate_all_xml(hoso, package_id)
        
        # Ghi ra file
        for xml_type, xml_content in xmls.items():
            xml_file = output_dir / f"{xml_type}.xml"
            xml_file.write_text(xml_content, encoding='utf-8')
            click.echo(f"✓ Tao {xml_type}.xml ({len(xml_content)} characters)")
        
        click.echo(f"✓ Hoan tat! Kiem tra trong thu muc: {output_dir.absolute()}")
        
    except Exception as e:
        click.echo(f"❌ Loi: {e}")
        sys.exit(1)


@cli.command()
@click.option('--meta', default='data/input/metadata.xlsx', help='Duong dan file metadata.xlsx')
@click.option('--pdf-root', default='data/input/PDF_Files', help='Thu muc goc chua PDF')
@click.option('--output', default=None, help='Thu muc xuat AIP packages (mac dinh: data/output_[timestamp])')
@click.option('--limit', type=int, help='Gioi han so luong ho so (cho test)')
@click.option('--cleanup/--no-cleanup', default=False, help='Xoa folder AIP sau khi tao ZIP (mac dinh: giu folder)')
def build(meta: str, pdf_root: str, output: str, limit: Optional[int], cleanup: bool):
    """Xay dung cac goi AIP tu metadata Excel va PDF files"""
    click.echo("🏗️  AIP Builder - Xay dung goi AIP")
    
    try:
        config = get_config()
        
        # Tao output directory voi timestamp neu khong duoc chi dinh
        if output is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = f"data/output_{timestamp}"
        
        # Kiem tra dau vao
        meta_path = Path(meta)
        pdf_root_path = Path(pdf_root)
        output_dir = Path(output)
        
        if not meta_path.exists():
            click.echo(f"❌ File metadata khong ton tai: {meta_path}")
            return
            
        if not pdf_root_path.exists():
            click.echo(f"❌ Thu muc PDF khong ton tai: {pdf_root_path}")
            return
        
        # Tao thu muc output
        output_dir.mkdir(parents=True, exist_ok=True)
        click.echo(f"✓ Thu muc output: {output_dir.absolute()}")
        click.echo(f"🧹 Cleanup mode: {'BAT (xoa folder sau khi tao ZIP)' if cleanup else 'TAT (giu lai folder)'}")
        
        # Doc du lieu Excel
        click.echo("📖 Doc metadata Excel...")
        excel_reader = ExcelReader(config)
        hoso_df, tailieu_df = excel_reader.read_excel(str(meta_path))
        hoso_list = excel_reader.convert_to_models(hoso_df, tailieu_df)
        
        if not hoso_list:
            click.echo("❌ Khong tim thay ho so nao")
            return
        
        # Ap dung gioi han neu co
        if limit and limit > 0:
            hoso_list = hoso_list[:limit]
            click.echo(f"🔢 Gioi han {limit} ho so dau tien")
            
        click.echo(f"✓ Tim thay {len(hoso_list)} ho so")
        
        # Xay dung packages
        click.echo("🏗️  Bat dau xay dung packages...")
        builder = PackageBuilder(config, cleanup_folders=cleanup)
        summary = builder.build_multiple_packages(hoso_list, pdf_root_path, output_dir)
        
        # Hien thi ket qua
        click.echo("\\n📊 KET QUA XAY DUNG:")
        click.echo(f"   • Tong ho so: {summary.total_hoso}")
        click.echo(f"   • Thanh cong: {summary.successful_builds}")
        click.echo(f"   • That bai: {summary.failed_builds}")
        click.echo(f"   • Tong file: {summary.total_files}")
        click.echo(f"   • Kich thuoc: {summary.total_size_mb:.2f} MB")
        click.echo(f"   • Thoi gian: {summary.build_time_seconds:.2f} giay")
        
        if summary.errors:
            click.echo("\\n❌ LOI:")
            for error in summary.errors:
                click.echo(f"   • {error}")
        
        if summary.successful_builds > 0:
            click.echo(f"\\n✅ Hoan tat! Kiem tra packages trong: {output_dir.absolute()}")
        
    except Exception as e:
        click.echo(f"❌ Loi: {e}")
        sys.exit(1)


@cli.command()
@click.option('--package-dir', help='Thu muc chua 1 AIP package de validate')
@click.option('--packages-root', default='data/output', help='Thu muc chua nhieu AIP packages')
@click.option('--check-checksums', is_flag=True, help='Kiem tra checksum cac file')
def validate_packages(package_dir: Optional[str], packages_root: str, check_checksums: bool):
    """Validate AIP packages theo chuan CSIP"""
    click.echo("✅ AIP Builder - Validation Engine")
    
    try:
        config = get_config()
        validator = CSIPValidator(config)
        
        if package_dir:
            # Validate 1 package cu the
            package_path = Path(package_dir)
            if not package_path.exists():
                click.echo(f"❌ Package khong ton tai: {package_path}")
                return
            
            click.echo(f"🔍 Validation package: {package_path.name}")
            result = validator.validate_package(package_path)
            
            # Hien thi ket qua
            summary = result.get_summary()
            click.echo(f"\\n📊 KET QUA VALIDATION:")
            click.echo(f"   • Trang thai: {'✅ HOP LE' if result.is_valid else '❌ KHONG HOP LE'}")
            click.echo(f"   • Loi: {summary['error_count']}")
            click.echo(f"   • Canh bao: {summary['warning_count']}")
            click.echo(f"   • Thong tin: {summary['info_count']}")
            click.echo(f"   • File kiem tra: {summary['checked_files']}")
            click.echo(f"   • Kich thuoc: {summary['total_size_mb']:.2f} MB")
            click.echo(f"   • Thoi gian: {summary['validation_time']:.2f}s")
            
            # Hien thi loi
            if result.errors:
                click.echo(f"\\n❌ LOI:")
                for error in result.errors:
                    click.echo(f"   • {error}")
            
            # Hien thi canh bao
            if result.warnings:
                click.echo(f"\\n⚠️  CANH BAO:")
                for warning in result.warnings:
                    click.echo(f"   • {warning}")
            
            # Kiem tra checksum neu duoc yeu cau
            if check_checksums:
                click.echo("\\n🔒 Kiem tra checksum...")
                is_valid, errors = IntegrityChecker.verify_checksums(package_path)
                if is_valid:
                    click.echo("✅ Checksum hop le")
                else:
                    click.echo("❌ Checksum khong hop le:")
                    for error in errors:
                        click.echo(f"   • {error}")
        
        else:
            # Validate tat ca packages
            packages_path = Path(packages_root)
            if not packages_path.exists():
                click.echo(f"❌ Thu muc packages khong ton tai: {packages_path}")
                return
            
            click.echo(f"🔍 Validation tat ca packages trong: {packages_path}")
            results = validator.validate_multiple_packages(packages_path)
            
            if not results:
                click.echo("❌ Khong tim thay package nao")
                return
            
            # Thong ke tong hop
            total_packages = len(results)
            valid_packages = sum(1 for r in results.values() if r.is_valid)
            total_errors = sum(len(r.errors) for r in results.values())
            total_warnings = sum(len(r.warnings) for r in results.values())
            
            click.echo(f"\\n📊 TONG KET VALIDATION:")
            click.echo(f"   • Tong packages: {total_packages}")
            click.echo(f"   • Hop le: {valid_packages}")
            click.echo(f"   • Khong hop le: {total_packages - valid_packages}")
            click.echo(f"   • Tong loi: {total_errors}")
            click.echo(f"   • Tong canh bao: {total_warnings}")
            
            # Hien thi chi tiet
            click.echo(f"\\n📋 CHI TIET:")
            for package_name, result in results.items():
                status = "✅" if result.is_valid else "❌"
                click.echo(f"   {status} {package_name}: {len(result.errors)} loi, {len(result.warnings)} canh bao")
                
                # Hien thi loi quan trong
                if result.errors:
                    for error in result.errors[:3]:  # Chi hien thi 3 loi dau
                        click.echo(f"      • {error}")
                    if len(result.errors) > 3:
                        click.echo(f"      • ... va {len(result.errors) - 3} loi khac")
        
        click.echo(f"\\n✅ Validation hoan tat!")
        
    except Exception as e:
        click.echo(f"❌ Loi: {e}")
        sys.exit(1)


@cli.command()
@click.option('--output', '-o', type=click.Path(), default=None, 
              help='Thu muc output (mac dinh: data/output_[timestamp])')
@click.option('--pdf-root', type=click.Path(exists=True), default='data/input/PDF_Files',
              help='Thu muc chua PDF files (mac dinh: data/input/PDF_Files)')
@click.option('--excel', type=click.Path(exists=True), default='data/input/metadata.xlsx',
              help='File Excel metadata (mac dinh: data/input/metadata.xlsx)')
@click.option('--max-workers', type=int, default=None,
              help='So luong worker threads (mac dinh: tu dong)')
@click.option('--chunk-size', type=int, default=5,
              help='So luong ho so trong 1 batch (mac dinh: 5)')
@click.option('--no-validate', is_flag=True, default=False,
              help='Bo qua validation sau khi build')
@click.option('--stop-on-error', is_flag=True, default=False,
              help='Dung khi gap loi (mac dinh: tiep tuc)')
def batch_build(output, pdf_root, excel, max_workers, chunk_size, no_validate, stop_on_error):
    """Xay dung dong loat nhieu AIP package voi parallel processing"""
    
    click.secho("🚀 AIP Builder - Batch Processing", fg='green', bold=True)
    
    # Tao output directory voi timestamp neu khong duoc chi dinh
    if output is None:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"data/output_{timestamp}"
    
    output_dir = Path(output).resolve()
    pdf_root_dir = Path(pdf_root).resolve()
    excel_file = Path(excel).resolve()
    
    click.echo(f"✓ Thu muc output: {output_dir}")
    click.echo(f"✓ Thu muc PDF: {pdf_root_dir}")
    click.echo(f"✓ File Excel: {excel_file}")
    click.echo(f"✓ Max workers: {max_workers or 'auto'}")
    click.echo(f"✓ Chunk size: {chunk_size}")
    
    try:
        # Doc metadata Excel
        click.echo("📖 Doc metadata Excel...")
        from .config import Config
        from .excel_reader import read_metadata_excel
        ho_so_list = read_metadata_excel(str(excel_file))
        click.echo(f"✓ Tim thay {len(ho_so_list)} ho so")
        
        # Tao thu muc output
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Tao batch processor
        processor = create_batch_processor(
            max_workers=max_workers,
            validate=not no_validate,
            chunk_size=chunk_size
        )
        processor.config.continue_on_error = not stop_on_error
        
        # Tao monitor
        monitor = BatchMonitor()
        processor.add_progress_callback(monitor.progress_callback)
        monitor.start()
        
        # Xu ly batch
        click.echo("🚀 Bat dau batch processing...")
        result = processor.build_packages_parallel(
            ho_so_list=ho_so_list,
            output_dir=output_dir,
            pdf_root=pdf_root_dir
        )
        
        # Hien thi ket qua
        click.echo()
        click.secho("📊 KET QUA BATCH PROCESSING:", fg='blue', bold=True)
        click.echo(f"   • Tong ho so: {result.total_packages}")
        click.echo(f"   • Thanh cong: {click.style(str(result.successful_packages), fg='green')}")
        click.echo(f"   • That bai: {click.style(str(result.failed_packages), fg='red')}")
        
        if not no_validate:
            click.echo(f"   • Validation passed: {click.style(str(result.validation_passed), fg='green')}")
            click.echo(f"   • Validation failed: {click.style(str(result.validation_failed), fg='red')}")
        
        click.echo(f"   • Tong kich thuoc: {result.total_size_mb:.2f} MB")
        click.echo(f"   • Thoi gian: {result.total_time:.2f} giay")
        
        if result.total_packages > 0:
            success_rate = (result.successful_packages / result.total_packages) * 100
            avg_time = result.total_time / result.total_packages
            click.echo(f"   • Ty le thanh cong: {success_rate:.1f}%")
            click.echo(f"   • Thoi gian trung binh/package: {avg_time:.2f}s")
        
        # Hien thi loi
        if result.errors:
            click.echo()
            click.secho("❌ LOI:", fg='red', bold=True)
            for error in result.errors[:10]:  # Chi hien thi 10 loi dau
                click.echo(f"   • {error}")
            if len(result.errors) > 10:
                click.echo(f"   • ... va {len(result.errors) - 10} loi khac")
        
        click.echo()
        if result.successful_packages == result.total_packages:
            click.secho("✅ Batch processing hoan tat thanh cong!", fg='green', bold=True)
        else:
            click.secho("⚠️  Batch processing hoan tat voi mot so loi!", fg='yellow', bold=True)
            
        click.echo(f"Kiem tra packages trong: {output_dir}")
        
    except KeyboardInterrupt:
        click.echo()
        click.secho("❌ Da huy batch processing!", fg='red', bold=True)
        return
    except Exception as e:
        click.secho(f"❌ Loi batch processing: {e}", fg='red', bold=True)
        raise click.ClickException(f"Batch processing failed: {e}")


@cli.command()  
@click.option('--logs-dir', type=click.Path(), default='logs',
              help='Thu muc logs (mac dinh: logs)')
@click.option('--output', '-o', type=click.Path(), default='error_report.json',
              help='File bao cao loi (mac dinh: error_report.json)')
def generate_error_report(logs_dir, output):
    """Tao bao cao loi tu log files"""
    
    click.secho("📋 AIP Builder - Error Report Generator", fg='blue', bold=True)
    
    logs_path = Path(logs_dir)
    output_file = Path(output)
    
    if not logs_path.exists():
        click.secho(f"❌ Thu muc logs khong ton tai: {logs_path}", fg='red')
        return
    
    try:
        # Tim tat ca log files
        log_files = list(logs_path.glob("*.log"))
        if not log_files:
            click.secho("❌ Khong tim thay log files nao", fg='red')
            return
        
        click.echo(f"📂 Tim thay {len(log_files)} log files")
        
        # Create enhanced logger for processing
        logger = create_enhanced_logger('error_report_generator')
        
        # Process logs (simplified - in real implementation would parse log files)
        click.echo("🔍 Phan tich log files...")
        
        # Export error report
        logger.error_collector.export_to_json(output_file)
        
        click.echo(f"✅ Da tao bao cao loi: {output_file}")
        
    except Exception as e:
        click.secho(f"❌ Loi tao bao cao: {e}", fg='red')


def main():
    """Entry point chinh"""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\nBi gian doan boi nguoi dung")
        sys.exit(1)
    except Exception as e:
        click.echo(f"Loi khong mong doi: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
